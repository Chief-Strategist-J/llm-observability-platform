import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import time
from functools import wraps
from neo4j import GraphDatabase, Driver

project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.database.shared.query_monitoring_interfaces import (
    IQueryMonitoringClient, QueryMetric, QueryStatus, QueryPerformanceLevel,
    QueryMonitoringConfig, DatabaseConnectionConfig
)
from infrastructure.database.shared.query_monitoring_utils import (
    QueryHashGenerator, PerformanceClassifier, TimeWindowCalculator
)
from infrastructure.observability.scripts.observability_client import ObservabilityClient
from .neo4j_query_collector import Neo4jQueryCollector
from .neo4j_query_analyzer import Neo4jQueryAnalyzer
from .neo4j_metrics_exporter import Neo4jMetricsExporter
from ..client.neo4j_client import execute_query, Neo4jConnectionConfig


class Neo4jMonitoringClient(IQueryMonitoringClient):
    def __init__(self, driver: Driver, config: Optional[QueryMonitoringConfig] = None):
        self.driver = driver
        self.config = config or QueryMonitoringConfig()
        self.obs = ObservabilityClient(service_name="neo4j-monitoring-client")
        
        self.collector = Neo4jQueryCollector(driver, config)
        self.analyzer = Neo4jQueryAnalyzer(driver)
        self.exporter = Neo4jMetricsExporter(driver, config)
        
        self._monitoring_enabled = True

    def execute_with_monitoring(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        start_time = time.time()
        query_hash = QueryHashGenerator.generate_hash(query, params)
        
        self.obs.log_info(f"execute_with_monitoring hash={query_hash}")
        
        try:
            result = execute_query(self.driver, query, params)
            execution_time_ms = result.execution_time_ms
            
            performance_level = PerformanceClassifier.classify_performance(
                execution_time_ms,
                PerformanceClassifier.get_default_thresholds()
            )
            
            metric = QueryMetric(
                query_hash=query_hash,
                query_type=self._extract_query_type(query),
                database="neo4j",
                collection_table=None,
                execution_time_ms=execution_time_ms,
                status=QueryStatus.SUCCESS if result.success else QueryStatus.ERROR,
                performance_level=performance_level,
                timestamp=datetime.utcnow(),
                affected_rows=len(result.records) if result.records else 0,
                error_message=result.error_message if not result.success else None,
                plan_details=self._get_query_plan(query) if self.config.enable_query_plans else None
            )
            
            self.collector.record_query_execution(metric)
            
            if performance_level in [QueryPerformanceLevel.SLOW, QueryPerformanceLevel.CRITICAL]:
                self.obs.log_warning(f"Slow query detected hash={query_hash} time_ms={execution_time_ms}")
            
            return {
                "success": result.success,
                "result": result.records,
                "execution_time_ms": execution_time_ms,
                "performance_level": performance_level,
                "query_hash": query_hash,
                "summary": result.summary
            }
        
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            
            metric = QueryMetric(
                query_hash=query_hash,
                query_type=self._extract_query_type(query),
                database="neo4j",
                collection_table=None,
                execution_time_ms=execution_time_ms,
                status=QueryStatus.ERROR,
                performance_level=QueryPerformanceLevel.CRITICAL,
                timestamp=datetime.utcnow(),
                error_message=str(e)
            )
            
            self.collector.record_query_execution(metric)
            self.obs.log_error(f"Query execution failed hash={query_hash} error={e}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "performance_level": QueryPerformanceLevel.CRITICAL,
                "query_hash": query_hash
            }

    def get_performance_summary(self, period_minutes: int = 60) -> Dict[str, Any]:
        self.obs.log_info(f"get_performance_summary period_minutes={period_minutes}")
        
        try:
            summary = self.collector.get_performance_summary(period_minutes)
            
            health_status = self.exporter.get_health_status()
            
            index_gaps = self.collector.identify_index_gaps()
            
            return {
                "period_minutes": period_minutes,
                "summary": summary,
                "health": health_status,
                "index_gaps": index_gaps,
                "recommendations": self._generate_summary_recommendations(summary, health_status, index_gaps)
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to get performance summary: {e}")
            return {
                "period_minutes": period_minutes,
                "error": str(e),
                "summary": {},
                "health": {"healthy": False},
                "index_gaps": [],
                "recommendations": ["Performance summary unavailable due to error"]
            }

    def identify_performance_issues(self) -> List[Dict[str, Any]]:
        self.obs.log_info("identify_performance_issues")
        
        issues = []
        
        try:
            slow_queries = self.collector.get_slow_queries(
                threshold_ms=self.config.slow_query_threshold_ms,
                limit=20
            )
            
            for query in slow_queries:
                issues.append({
                    "type": "slow_query",
                    "severity": "high" if query.performance_level == QueryPerformanceLevel.CRITICAL else "medium",
                    "query_hash": query.query_hash,
                    "query_type": query.query_type,
                    "execution_time_ms": query.execution_time_ms,
                    "timestamp": query.timestamp,
                    "recommendation": f"Optimize {query.query_type} query or add appropriate indexes"
                })
            
            index_gaps = self.collector.identify_index_gaps()
            for gap in index_gaps:
                issues.append({
                    "type": "index_gap",
                    "severity": "medium",
                    "query_type": gap["query_type"],
                    "slow_query_count": gap["slow_query_count"],
                    "avg_execution_time": gap["avg_execution_time"],
                    "recommendation": gap["recommendation"]
                })
            
            health = self.exporter.get_health_status()
            if not health["healthy"]:
                for issue in health.get("issues", []):
                    issues.append({
                        "type": "health_issue",
                        "severity": "critical",
                        "description": issue,
                        "recommendation": "Address server health issues immediately"
                    })
            
            error_rate = self._calculate_error_rate()
            if error_rate > 5.0:
                issues.append({
                    "type": "high_error_rate",
                    "severity": "high",
                    "error_rate_percent": error_rate,
                    "recommendation": "Investigate and fix query errors"
                })
        
        except Exception as e:
            self.obs.log_error(f"Failed to identify performance issues: {e}")
            issues.append({
                "type": "analysis_error",
                "severity": "low",
                "description": f"Performance analysis failed: {str(e)}",
                "recommendation": "Check monitoring configuration"
            })
        
        return sorted(issues, key=lambda x: self._severity_priority(x["severity"]), reverse=True)

    def get_slow_queries_analysis(self, hours: int = 24) -> Dict[str, Any]:
        self.obs.log_info(f"get_slow_queries_analysis hours={hours}")
        
        try:
            slow_queries = self.collector.get_slow_queries(
                threshold_ms=self.config.slow_query_threshold_ms,
                limit=100
            )
            
            period_start = datetime.utcnow() - timedelta(hours=hours)
            recent_slow = [q for q in slow_queries if q.timestamp >= period_start]
            
            query_type_breakdown = {}
            for query in recent_slow:
                query_type = query.query_type or "unknown"
                if query_type not in query_type_breakdown:
                    query_type_breakdown[query_type] = {
                        "count": 0,
                        "avg_execution_time": 0,
                        "max_execution_time": 0,
                        "total_execution_time": 0
                    }
                
                breakdown = query_type_breakdown[query_type]
                breakdown["count"] += 1
                breakdown["total_execution_time"] += query.execution_time_ms
                breakdown["max_execution_time"] = max(breakdown["max_execution_time"], query.execution_time_ms)
            
            for query_type, breakdown in query_type_breakdown.items():
                if breakdown["count"] > 0:
                    breakdown["avg_execution_time"] = breakdown["total_execution_time"] / breakdown["count"]
            
            return {
                "period_hours": hours,
                "total_slow_queries": len(recent_slow),
                "query_type_breakdown": query_type_breakdown,
                "top_slow_queries": recent_slow[:10],
                "trend": self._calculate_slow_query_trend(recent_slow)
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to get slow queries analysis: {e}")
            return {
                "period_hours": hours,
                "error": str(e)
            }

    def get_database_health_report(self) -> Dict[str, Any]:
        self.obs.log_info("get_database_health_report")
        
        try:
            health = self.exporter.get_health_status()
            
            json_metrics = self.exporter.export_json_metrics()
            
            performance_summary = self.get_performance_summary(period_minutes=60)
            
            issues = self.identify_performance_issues()
            
            critical_issues = [i for i in issues if i["severity"] == "critical"]
            high_issues = [i for i in issues if i["severity"] == "high"]
            
            overall_health_score = health["health_score"]
            if critical_issues:
                overall_health_score = min(overall_health_score, 30)
            if high_issues:
                overall_health_score = min(overall_health_score, 60)
            
            schema_analysis = self.analyzer.get_schema_analysis("neo4j")
            
            return {
                "overall_health_score": overall_health_score,
                "health_status": "healthy" if overall_health_score >= 70 else "degraded" if overall_health_score >= 40 else "critical",
                "server_health": health,
                "performance_summary": performance_summary.get("summary", {}),
                "schema_analysis": schema_analysis,
                "issues": {
                    "critical": critical_issues,
                    "high": high_issues,
                    "total_count": len(issues)
                },
                "metrics": json_metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to get database health report: {e}")
            return {
                "overall_health_score": 0,
                "health_status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def _extract_query_type(self, query: str) -> str:
        query_upper = query.strip().upper()
        
        if query_upper.startswith("MATCH"):
            return "match"
        elif query_upper.startswith("CREATE"):
            return "create"
        elif query_upper.startswith("MERGE"):
            return "merge"
        elif query_upper.startswith("DELETE"):
            return "delete"
        elif query_upper.startswith("SET"):
            return "set"
        elif query_upper.startswith("REMOVE"):
            return "remove"
        elif query_upper.startswith("CALL"):
            return "call"
        elif query_upper.startswith("WITH"):
            return "with"
        elif query_upper.startswith("UNWIND"):
            return "unwind"
        else:
            return "unknown"

    def _get_query_plan(self, query: str) -> Optional[Dict[str, Any]]:
        try:
            return self.analyzer.explain_query(query, "neo4j")
        except:
            return None

    def _generate_summary_recommendations(self, summary: Dict[str, Any], health: Dict[str, Any], index_gaps: List[Dict[str, Any]]) -> List[str]:
        recommendations = []
        
        if summary.get("slow_query_percentage", 0) > 10:
            recommendations.append("High percentage of slow queries detected")
        
        if summary.get("error_rate", 0) > 5:
            recommendations.append("Elevated error rate detected")
        
        if not health.get("healthy", True):
            recommendations.append("Database health issues detected")
        
        if index_gaps:
            recommendations.append(f"Index gaps identified for {len(index_gaps)} query types")
        
        return recommendations

    def _calculate_error_rate(self) -> float:
        try:
            metrics = self.collector.collect_query_metrics(limit=1000)
            if not metrics:
                return 0.0
            
            error_count = len([m for m in metrics if m.status == QueryStatus.ERROR])
            return (error_count / len(metrics)) * 100
        except:
            return 0.0

    def _severity_priority(self, severity: str) -> int:
        priorities = {"critical": 3, "high": 2, "medium": 1, "low": 0}
        return priorities.get(severity, 0)

    def _calculate_slow_query_trend(self, slow_queries: List[QueryMetric]) -> str:
        if len(slow_queries) < 2:
            return "insufficient_data"
        
        recent_half = slow_queries[len(slow_queries)//2:]
        older_half = slow_queries[:len(slow_queries)//2]
        
        recent_avg = sum(q.execution_time_ms for q in recent_half) / len(recent_half)
        older_avg = sum(q.execution_time_ms for q in older_half) / len(older_half)
        
        if recent_avg > older_avg * 1.2:
            return "deteriorating"
        elif recent_avg < older_avg * 0.8:
            return "improving"
        else:
            return "stable"

    def get_schema_performance_analysis(self) -> Dict[str, Any]:
        self.obs.log_info("get_schema_performance_analysis")
        
        try:
            schema_analysis = self.analyzer.get_schema_analysis("neo4j")
            
            if not schema_analysis.get("success"):
                return {"error": "Failed to get schema analysis"}
            
            schema = schema_analysis.get("schema", {})
            
            recommendations = []
            
            labels = schema.get("labels", [])
            if len(labels) > 20:
                recommendations.append("High number of labels detected - consider schema consolidation")
            
            relationship_types = schema.get("relationship_types", [])
            if len(relationship_types) > 50:
                recommendations.append("High number of relationship types detected - consider schema optimization")
            
            indexes = schema.get("indexes", [])
            if len(indexes) < len(labels) * 2:
                recommendations.append("Consider adding more indexes to improve query performance")
            
            constraints = schema.get("constraints", [])
            if len(constraints) == 0:
                recommendations.append("Consider adding constraints to ensure data integrity")
            
            return {
                "schema": schema,
                "recommendations": recommendations,
                "analysis": {
                    "label_count": len(labels),
                    "relationship_type_count": len(relationship_types),
                    "index_count": len(indexes),
                    "constraint_count": len(constraints)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to get schema performance analysis: {e}")
            return {"error": str(e)}

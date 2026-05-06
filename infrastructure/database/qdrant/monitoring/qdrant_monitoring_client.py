import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import time
from functools import wraps
import requests
from requests import Session

project_root = Path(__file__).resolve().parents[4)
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
from .qdrant_query_collector import QdrantQueryCollector
from .qdrant_query_analyzer import QdrantQueryAnalyzer
from .qdrant_metrics_exporter import QdrantMetricsExporter
from ..client.qdrant_client import (
    execute_request, get_http_client, QdrantConnectionConfig,
    search_points, scroll_points, count_points, list_collections
)


class QdrantMonitoringClient(IQueryMonitoringClient):
    def __init__(self, session: Session, config: Optional[QueryMonitoringConfig] = None):
        self.session = session
        self.config = config or QueryMonitoringConfig()
        self.obs = ObservabilityClient(service_name="qdrant-monitoring-client")
        
        self.collector = QdrantQueryCollector(session, config)
        self.analyzer = QdrantQueryAnalyzer(session)
        self.exporter = QdrantMetricsExporter(session, config)
        
        self._monitoring_enabled = True

    def execute_with_monitoring(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        start_time = time.time()
        query_hash = QueryHashGenerator.generate_hash(query, params)
        
        self.obs.log_info(f"execute_with_monitoring hash={query_hash}")
        
        try:
            # Parse query to determine operation
            query_parts = query.split()
            if not query_parts:
                return {
                    "success": False,
                    "error": "Empty query",
                    "execution_time_ms": 0,
                    "performance_level": QueryPerformanceLevel.CRITICAL,
                    "query_hash": query_hash
                }
            
            operation = query_parts[0].lower()
            
            # Execute the appropriate operation
            if operation == "search" and len(query_parts) >= 2:
                collection_name = query_parts[1]
                vector_size = params.get("vector_size", 128) if params else 128
                dummy_vector = [0.1] * vector_size
                
                result = search_points(
                    self.session,
                    collection_name,
                    dummy_vector,
                    limit=params.get("limit", 10) if params else 10
                )
            elif operation == "scroll" and len(query_parts) >= 2:
                collection_name = query_parts[1]
                result = scroll_points(
                    self.session,
                    collection_name,
                    limit=params.get("limit", 10) if params else 10
                )
            elif operation == "count" and len(query_parts) >= 2:
                collection_name = query_parts[1]
                result = count_points(self.session, collection_name)
            elif operation == "info" and len(query_parts) >= 2:
                collection_name = query_parts[1]
                from ..client.qdrant_client import get_collection_info
                result = get_collection_info(self.session, collection_name)
            elif operation == "list":
                result = list_collections(self.session)
            else:
                # Generic request execution
                result = execute_request(self.session, "GET", query)
            
            execution_time_ms = result.execution_time_ms
            
            performance_level = PerformanceClassifier.classify_performance(
                execution_time_ms,
                PerformanceClassifier.get_default_thresholds()
            )
            
            metric = QueryMetric(
                query_hash=query_hash,
                query_type=operation,
                database="qdrant",
                collection_table=query_parts[1] if len(query_parts) > 1 else None,
                execution_time_ms=execution_time_ms,
                status=QueryStatus.SUCCESS if result.success else QueryStatus.ERROR,
                performance_level=performance_level,
                timestamp=datetime.utcnow(),
                affected_rows=result.result_count if result.result_count else 1,
                error_message=result.error_message if not result.success else None,
                plan_details={
                    "operation": operation,
                    "collection": query_parts[1] if len(query_parts) > 1 else None,
                    "params": params
                } if self.config.enable_query_plans else None
            )
            
            self.collector.record_query_execution(metric)
            
            if performance_level in [QueryPerformanceLevel.SLOW, QueryPerformanceLevel.CRITICAL]:
                self.obs.log_warning(f"Slow query detected hash={query_hash} time_ms={execution_time_ms}")
            
            return {
                "success": result.success,
                "result": result.result,
                "execution_time_ms": execution_time_ms,
                "performance_level": performance_level,
                "query_hash": query_hash,
                "operation": operation,
                "result_count": result.result_count
            }
        
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            
            metric = QueryMetric(
                query_hash=query_hash,
                query_type=query.split()[0].lower() if query else "unknown",
                database="qdrant",
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
                    "collection": query.collection_table,
                    "execution_time_ms": query.execution_time_ms,
                    "timestamp": query.timestamp,
                    "recommendation": f"Optimize {query.query_type} operation or adjust HNSW parameters"
                })
            
            index_gaps = self.collector.identify_index_gaps()
            for gap in index_gaps:
                issues.append({
                    "type": "collection_gap",
                    "severity": "medium",
                    "collection": gap["collection"],
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
            
            collection_breakdown = {}
            for query in recent_slow:
                collection = query.collection_table or "unknown"
                if collection not in collection_breakdown:
                    collection_breakdown[collection] = {
                        "count": 0,
                        "avg_execution_time": 0,
                        "max_execution_time": 0,
                        "total_execution_time": 0
                    }
                
                breakdown = collection_breakdown[collection]
                breakdown["count"] += 1
                breakdown["total_execution_time"] += query.execution_time_ms
                breakdown["max_execution_time"] = max(breakdown["max_execution_time"], query.execution_time_ms)
            
            for collection, breakdown in collection_breakdown.items():
                if breakdown["count"] > 0:
                    breakdown["avg_execution_time"] = breakdown["total_execution_time"] / breakdown["count"]
            
            return {
                "period_hours": hours,
                "total_slow_queries": len(recent_slow),
                "collection_breakdown": collection_breakdown,
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
            
            schema_analysis = self.analyzer.get_schema_analysis("qdrant")
            
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
        parts = query.split()
        return parts[0].lower() if parts else "unknown"

    def _generate_summary_recommendations(self, summary: Dict[str, Any], health: Dict[str, Any], index_gaps: List[Dict[str, Any]]) -> List[str]:
        recommendations = []
        
        if summary.get("slow_query_percentage", 0) > 10:
            recommendations.append("High percentage of slow queries detected")
        
        if summary.get("error_rate", 0) > 5:
            recommendations.append("Elevated error rate detected")
        
        if not health.get("healthy", True):
            recommendations.append("Database health issues detected")
        
        if index_gaps:
            recommendations.append(f"Collection optimization opportunities identified for {len(index_gaps)} collections")
        
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
            schema_analysis = self.analyzer.get_schema_analysis("qdrant")
            
            if not schema_analysis.get("success"):
                return {"error": "Failed to get schema analysis"}
            
            schema = schema_analysis.get("schema", {})
            
            recommendations = []
            
            collections_info = schema.get("collections_info", [])
            if len(collections_info) > 20:
                recommendations.append("High number of collections detected - consider consolidation")
            
            collection_analysis = schema.get("collection_analysis", {})
            performance_issues = 0
            for collection_name, collection_data in collection_analysis.items():
                hnsw_data = collection_data.get("hnsw_analysis", {})
                averages = hnsw_data.get("averages", {})
                
                if averages.get("avg_search_time_ms", 0) > 100:
                    performance_issues += 1
            
            if performance_issues > len(collection_analysis) * 0.3:  # > 30% of collections have issues
                recommendations.append("Multiple collections have performance issues - review HNSW configuration")
            
            return {
                "schema": schema,
                "recommendations": recommendations,
                "analysis": {
                    "total_collections": len(collections_info),
                    "collections_with_issues": performance_issues,
                    "collection_analysis": collection_analysis
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to get schema performance analysis: {e}")
            return {"error": str(e)}

    def get_collection_performance_analysis(self, collection_name: str) -> Dict[str, Any]:
        self.obs.log_info(f"get_collection_performance_analysis collection={collection_name}")
        
        try:
            collection_stats = self.collector.get_collection_statistics(collection_name)
            
            if not collection_stats:
                return {"error": f"Collection '{collection_name}' not found or no statistics available"}
            
            hnsw_analysis = self.collector.get_hnsw_performance_analysis(collection_name)
            vector_performance = self.collector.get_vector_search_performance(collection_name)
            
            recommendations = []
            
            collection_info = collection_stats.get("collection_info", {})
            config = collection_info.get("config", {})
            
            # Check HNSW configuration
            hnsw_config = config.get("hnsw_config", {})
            if hnsw_config:
                m = hnsw_config.get("m", 16)
                ef_construct = hnsw_config.get("ef_construct", 200)
                ef_search = hnsw_config.get("ef_search", 64)
                
                if m > 32:
                    recommendations.append(f"Consider reducing M parameter from {m} for better memory usage")
                if ef_construct > 400:
                    recommendations.append(f"Consider reducing ef_construct from {ef_construct} for faster indexing")
                if ef_search > 128:
                    recommendations.append(f"Consider reducing ef_search from {ef_search} for faster search")
            
            # Check point count
            point_count = collection_stats.get("point_count", 0)
            if point_count > 1000000:
                recommendations.append("Large collection detected - consider quantization or sharding")
            
            # Check vector size
            vector_size = collection_stats.get("vector_size", 0)
            if vector_size > 512:
                recommendations.append(f"High-dimensional vectors ({vector_size}) detected - consider dimensionality reduction")
            
            return {
                "collection": collection_name,
                "statistics": collection_stats,
                "hnsw_analysis": hnsw_analysis,
                "vector_performance": vector_performance,
                "recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to get collection performance analysis: {e}")
            return {"error": str(e)}

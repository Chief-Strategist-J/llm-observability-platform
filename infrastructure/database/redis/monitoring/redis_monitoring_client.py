import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import time
from functools import wraps
import redis
from redis import Redis

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
from .redis_query_collector import RedisQueryCollector
from .redis_query_analyzer import RedisQueryAnalyzer
from .redis_metrics_exporter import RedisMetricsExporter
from ..client.redis_client import execute_query_with_timing, RedisConnectionConfig


class RedisMonitoringClient(IQueryMonitoringClient):
    def __init__(self, client: Redis, config: Optional[QueryMonitoringConfig] = None):
        self.client = client
        self.config = config or QueryMonitoringConfig()
        self.obs = ObservabilityClient(service_name="redis-monitoring-client")
        
        self.collector = RedisQueryCollector(client, config)
        self.analyzer = RedisQueryAnalyzer(client)
        self.exporter = RedisMetricsExporter(client, config)
        
        self._monitoring_enabled = True

    def execute_with_monitoring(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        start_time = time.time()
        query_hash = QueryHashGenerator.generate_hash(query, params)
        
        self.obs.log_info(f"execute_with_monitoring hash={query_hash}")
        
        try:
            # Parse query into command and arguments
            parts = query.split()
            if not parts:
                return {
                    "success": False,
                    "error": "Empty query",
                    "execution_time_ms": 0,
                    "performance_level": QueryPerformanceLevel.CRITICAL,
                    "query_hash": query_hash
                }
            
            command = parts[0].lower()
            args = parts[1:] + (list(params.values()) if params else [])
            
            result = execute_query_with_timing(self.client, query, *args)
            execution_time_ms = result.execution_time_ms
            
            performance_level = PerformanceClassifier.classify_performance(
                execution_time_ms,
                PerformanceClassifier.get_default_thresholds()
            )
            
            metric = QueryMetric(
                query_hash=query_hash,
                query_type=command,
                database="redis",
                collection_table=None,  # Redis doesn't have tables
                execution_time_ms=execution_time_ms,
                status=QueryStatus.SUCCESS if result.success else QueryStatus.ERROR,
                performance_level=performance_level,
                timestamp=datetime.utcnow(),
                affected_rows=result.key_count if result.key_count else 1,
                error_message=result.error_message if not result.success else None,
                plan_details=result.command if self.config.enable_query_plans else None
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
                "command": result.command,
                "key_count": result.key_count
            }
        
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            
            metric = QueryMetric(
                query_hash=query_hash,
                query_type=query.split()[0].lower() if query else "unknown",
                database="redis",
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
                    "recommendation": f"Optimize {query.query_type} operation or use Redis data structures more efficiently"
                })
            
            index_gaps = self.collector.identify_index_gaps()
            for gap in index_gaps:
                issues.append({
                    "type": "command_gap",
                    "severity": "medium",
                    "command_type": gap["command_type"],
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
            
            slow_log_analysis = self.collector.get_slow_log_analysis(limit=20)
            if slow_log_analysis.get("total_slow_queries", 0) > 10:
                issues.append({
                    "type": "slow_log_overflow",
                    "severity": "high",
                    "slow_log_count": slow_log_analysis["total_slow_queries"],
                    "recommendation": "High number of slow queries detected - review slow query patterns"
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
            slow_log_analysis = self.collector.get_slow_log_analysis(limit=100)
            
            period_start = datetime.utcnow() - timedelta(hours=hours)
            
            # Filter slow log entries by time
            recent_slow = []
            for entry in slow_log_analysis.get("slow_queries", []):
                if entry.get("timestamp"):
                    entry_time = datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00'))
                    if entry_time >= period_start:
                        recent_slow.append(entry)
            
            command_breakdown = {}
            for entry in recent_slow:
                command = entry.get("command", ["unknown"])[0].lower() if isinstance(entry.get("command"), list) else "unknown"
                if command not in command_breakdown:
                    command_breakdown[command] = {
                        "count": 0,
                        "avg_execution_time": 0,
                        "max_execution_time": 0,
                        "total_execution_time": 0
                    }
                
                breakdown = command_breakdown[command]
                breakdown["count"] += 1
                breakdown["total_execution_time"] += entry.get("execution_time_micros", 0)
                breakdown["max_execution_time"] = max(breakdown["max_execution_time"], entry.get("execution_time_micros", 0))
            
            for command, breakdown in command_breakdown.items():
                if breakdown["count"] > 0:
                    breakdown["avg_execution_time"] = breakdown["total_execution_time"] / breakdown["count"]
            
            return {
                "period_hours": hours,
                "total_slow_queries": len(recent_slow),
                "command_breakdown": command_breakdown,
                "top_slow_queries": recent_slow[:10],
                "trend": self._calculate_slow_query_trend(recent_slow),
                "slow_log_analysis": slow_log_analysis.get("analysis", {})
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
            
            schema_analysis = self.analyzer.get_schema_analysis("redis")
            
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
            recommendations.append(f"Command optimization opportunities identified for {len(index_gaps)} command types")
        
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

    def _calculate_slow_query_trend(self, slow_queries: List[Dict[str, Any]]) -> str:
        if len(slow_queries) < 2:
            return "insufficient_data"
        
        recent_half = slow_queries[len(slow_queries)//2:]
        older_half = slow_queries[:len(slow_queries)//2]
        
        recent_avg = sum(q.get("execution_time_micros", 0) for q in recent_half) / len(recent_half)
        older_avg = sum(q.get("execution_time_micros", 0) for q in older_half) / len(older_half)
        
        if recent_avg > older_avg * 1.2:
            return "deteriorating"
        elif recent_avg < older_avg * 0.8:
            return "improving"
        else:
            return "stable"

    def get_schema_performance_analysis(self) -> Dict[str, Any]:
        self.obs.log_info("get_schema_performance_analysis")
        
        try:
            schema_analysis = self.analyzer.get_schema_analysis("redis")
            
            if not schema_analysis.get("success"):
                return {"error": "Failed to get schema analysis"}
            
            schema = schema_analysis.get("schema", {})
            
            recommendations = []
            
            key_stats = schema.get("keyspace_analysis", {})
            if key_stats.get("total_keys", 0) > 100000:
                recommendations.append("High number of keys detected - consider key naming conventions and TTL management")
            
            key_types = key_stats.get("key_types", {})
            if key_types.get("string", 0) > key_types.get("hash", 0) * 2:
                recommendations.append("Consider using HASH for structured string data")
            
            ttl_dist = key_stats.get("ttl_distribution", {})
            if ttl_dist.get("no_ttl", 0) > ttl_dist.get("short_ttl", 0) + ttl_dist.get("medium_ttl", 0):
                recommendations.append("Consider setting TTL for keys to manage memory usage")
            
            db_metrics = schema.get("database_metrics", {})
            memory_info = db_metrics.get("memory_info", {})
            if memory_info.get("used_memory", 0) > memory_info.get("maxmemory", 0) * 0.8:
                recommendations.append("Memory usage is high - consider optimization")
            
            return {
                "schema": schema,
                "recommendations": recommendations,
                "analysis": {
                    "total_keys": key_stats.get("total_keys", 0),
                    "key_types": key_types,
                    "ttl_distribution": ttl_dist,
                    "memory_usage": memory_info.get("used_memory", 0)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to get schema performance analysis: {e}")
            return {"error": str(e)}

    def get_key_performance_analysis(self, key_pattern: str = "*") -> Dict[str, Any]:
        self.obs.log_info(f"get_key_performance_analysis pattern={key_pattern}")
        
        try:
            key_stats = self.collector.get_key_statistics(key_pattern)
            
            if not key_stats:
                return {"error": f"No keys found matching pattern: {key_pattern}"}
            
            recommendations = []
            
            total_keys = key_stats.get("total_keys", 0)
            if total_keys > 10000:
                recommendations.append(f"Large number of keys matching pattern: {total_keys}")
            
            key_types = key_stats.get("key_types", {})
            if key_types.get("string", 0) > 0:
                recommendations.append("Consider analyzing string keys for optimization opportunities")
            
            sample_memory = key_stats.get("sample_memory_usage", {})
            if sample_memory:
                avg_memory = sum(sample_memory.values()) / len(sample_memory)
                if avg_memory > 1024:  # > 1KB average
                    recommendations.append("High average key memory usage detected")
            
            ttl_dist = key_stats.get("ttl_distribution", {})
            if ttl_dist.get("no_ttl", 0) > total_keys * 0.8:
                recommendations.append("Most keys have no TTL - consider setting expiration")
            
            return {
                "key_pattern": key_pattern,
                "statistics": key_stats,
                "recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to get key performance analysis: {e}")
            return {"error": str(e)}

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import redis
from redis import Redis

project_root = Path(__file__).resolve().parents[4)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.database.shared.query_monitoring_interfaces import (
    IQueryAnalyzer, QueryAnalysisResult, PerformanceReport, QueryMetric,
    QueryPerformanceLevel, QueryStatus
)
from infrastructure.database.shared.query_monitoring_utils import (
    QueryHashGenerator, QueryMetricsAggregator, QueryRecommendationEngine,
    QueryPlanAnalyzer, PerformanceClassifier
)
from infrastructure.observability.scripts.observability_client import ObservabilityClient
from ..client.redis_client import execute_command, get_redis_client, RedisConnectionConfig


class RedisQueryAnalyzer(IQueryAnalyzer):
    def __init__(self, client: Redis):
        self.client = client
        self.obs = ObservabilityClient(service_name="redis-query-analyzer")

    def analyze_query(self, query_text: str, database: str) -> QueryAnalysisResult:
        self.obs.log_info(f"analyze_query database={database}")
        
        try:
            query_hash = QueryHashGenerator.generate_hash(query_text)
            
            plan_details = self.explain_query(query_text, database)
            plan_analysis = QueryPlanAnalyzer.analyze_plan_efficiency(plan_details)
            
            performance_score = self._calculate_performance_score(query_text, database, plan_analysis)
            
            recommendations = self._generate_query_recommendations(query_text, database, plan_analysis)
            
            suggested_indexes = self.suggest_indexes(query_text, database)
            
            optimization_potential = self._assess_optimization_potential(performance_score, plan_analysis)
            
            estimated_improvement = self._estimate_improvement(suggested_indexes, plan_analysis)
            
            return QueryAnalysisResult(
                query_hash=query_hash,
                query_text=query_text,
                performance_score=performance_score,
                recommendations=recommendations,
                suggested_indexes=suggested_indexes,
                optimization_potential=optimization_potential,
                estimated_improvement_percent=estimated_improvement
            )
        
        except Exception as e:
            self.obs.log_error(f"Failed to analyze query: {e}")
            return QueryAnalysisResult(
                query_hash=QueryHashGenerator.generate_hash(query_text),
                query_text=query_text,
                performance_score=0,
                recommendations=["Query analysis failed due to error"],
                suggested_indexes=[],
                optimization_potential="unknown",
                estimated_improvement_percent=None
            )

    def explain_query(self, query_text: str, database: str) -> Dict[str, Any]:
        self.obs.log_info(f"explain_query database={database}")
        
        try:
            # Parse the query
            parts = query_text.split()
            if not parts:
                return {
                    "success": False,
                    "error": "Empty query"
                }
            
            command = parts[0].upper()
            args = parts[1:]
            
            # Get command-specific analysis
            analysis = {
                "command": command,
                "args": args,
                "success": True,
                "command_info": self._get_command_info(command),
                "performance_implications": self._get_performance_implications(command, args),
                "optimization_suggestions": self._get_command_optimizations(command, args)
            }
            
            return analysis
        
        except Exception as e:
            self.obs.log_error(f"Failed to explain query: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def suggest_indexes(self, query_text: str, database: str) -> List[Dict[str, Any]]:
        self.obs.log_info(f"suggest_indexes database={database}")
        
        suggestions = []
        
        try:
            parts = query_text.split()
            if not parts:
                return suggestions
            
            command = parts[0].upper()
            args = parts[1:]
            
            # Redis doesn't have traditional indexes, but we can suggest data structure optimizations
            if command == "KEYS" and args:
                pattern = args[0]
                if pattern == "*":
                    suggestions.append({
                        'type': 'data_structure',
                        'recommendation': 'Avoid using KEYS * in production - use SCAN instead',
                        'reason': 'KEYS command blocks the server and can impact performance',
                        'alternative': 'Use SCAN with cursor-based iteration'
                    })
            
            if command in ["GET", "SET", "HGET", "HSET"] and args:
                key = args[0]
                suggestions.append({
                    'type': 'key_optimization',
                    'key': key,
                    'recommendation': f'Consider using appropriate data structure for key: {key}',
                    'reason': 'Optimal data structure selection improves performance',
                    'alternatives': self._suggest_data_structures_for_key(key)
                })
            
            if command in ["ZRANGE", "ZREVRANGE", "ZRANGEBYSCORE"] and len(args) >= 2:
                suggestions.append({
                    'type': 'sorted_set_optimization',
                    'recommendation': 'Consider using ZSCAN for large sorted sets',
                    'reason': 'Range operations on large sorted sets can be slow',
                    'alternative': 'Use ZSCAN with pattern matching'
                })
            
            if command in ["LRANGE", "LINDEX"] and args:
                suggestions.append({
                    'type': 'list_optimization',
                    'recommendation': 'Consider using LPUSH/RPUSH with LTRIM for sliding windows',
                    'reason': 'Large lists can be memory intensive',
                    'alternative': 'Use streaming operations or limited lists'
                })
        
        except Exception as e:
            self.obs.log_error(f"Failed to suggest indexes: {e}")
        
        return suggestions

    def generate_performance_report(self, database: str, period_start: datetime, period_end: datetime) -> PerformanceReport:
        self.obs.log_info(f"generate_performance_report database={database}")
        
        try:
            from .redis_query_collector import RedisQueryCollector
            collector = RedisQueryCollector(self.client)
            
            all_metrics = collector.collect_query_metrics(limit=10000)
            
            period_metrics = [
                m for m in all_metrics
                if period_start <= m.timestamp <= period_end
            ]
            
            if not period_metrics:
                return PerformanceReport(
                    database=database,
                    period_start=period_start,
                    period_end=period_end,
                    total_queries=0,
                    slow_queries=0,
                    avg_execution_time_ms=0.0,
                    performance_distribution={level: 0 for level in QueryPerformanceLevel},
                    top_slow_queries=[],
                    recommendations=["No query data available for the specified period"]
                )
            
            summary = QueryMetricsAggregator.aggregate_metrics(period_metrics)
            top_slow = QueryMetricsAggregator.get_top_slow_queries(period_metrics, limit=10)
            recommendations = QueryRecommendationEngine.generate_recommendations(period_metrics)
            
            # Add Redis-specific recommendations
            redis_recommendations = self._generate_redis_specific_recommendations(period_metrics)
            recommendations.extend(redis_recommendations)
            
            return PerformanceReport(
                database=database,
                period_start=period_start,
                period_end=period_end,
                total_queries=summary['total_queries'],
                slow_queries=summary['slow_query_count'],
                avg_execution_time_ms=summary['avg_execution_time_ms'],
                performance_distribution=summary['performance_distribution'],
                top_slow_queries=top_slow,
                recommendations=recommendations
            )
        
        except Exception as e:
            self.obs.log_error(f"Failed to generate performance report: {e}")
            return PerformanceReport(
                database=database,
                period_start=period_start,
                period_end=period_end,
                total_queries=0,
                slow_queries=0,
                avg_execution_time_ms=0.0,
                performance_distribution={level: 0 for level in QueryPerformanceLevel},
                top_slow_queries=[],
                recommendations=[f"Report generation failed: {str(e)}"]
            )

    def _calculate_performance_score(self, query_text: str, database: str, plan_analysis: Dict[str, Any]) -> float:
        score = 100.0
        
        if plan_analysis.get('efficiency_score', 100) < 100:
            score = plan_analysis['efficiency_score']
        
        # Redis-specific performance factors
        parts = query_text.split()
        if parts:
            command = parts[0].upper()
            
            if command == "KEYS":
                score -= 40  # KEYS is very expensive
            elif command == "FLUSHALL":
                score -= 30  # Destructive operation
            elif command == "FLUSHDB":
                score -= 25  # Destructive operation
            elif command in ["SMEMBERS", "HGETALL"] and self._is_potentially_large_key(parts[1] if len(parts) > 1 else ""):
                score -= 20  # Operations that can return large data sets
            elif command in ["LRANGE", "ZRANGE"] and len(parts) >= 3:
                score -= 15  # Range operations can be expensive
        
        return max(0, score)

    def _generate_query_recommendations(self, query_text: str, database: str, plan_analysis: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        if plan_analysis.get('issues'):
            recommendations.extend(plan_analysis['issues'])
        
        parts = query_text.split()
        if parts:
            command = parts[0].upper()
            
            if command == "KEYS":
                recommendations.append("Replace KEYS with SCAN for production environments")
            
            if command in ["GET", "SET"] and len(parts) > 1:
                key = parts[1]
                if self._is_potentially_large_key(key):
                    recommendations.append(f"Consider data structure optimization for key: {key}")
            
            if command in ["HGETALL", "SMEMBERS"]:
                recommendations.append("Consider using HSCAN/SSCAN for large data structures")
            
            if command == "SELECT":
                recommendations.append("Avoid SELECT in production - use connection pooling instead")
        
        return recommendations

    def _assess_optimization_potential(self, performance_score: float, plan_analysis: Dict[str, Any]) -> str:
        if performance_score >= 80:
            return "low"
        elif performance_score >= 60:
            return "medium"
        elif performance_score >= 40:
            return "high"
        else:
            return "critical"

    def _estimate_improvement(self, suggested_indexes: List[Dict[str, Any]], plan_analysis: Dict[str, Any]) -> Optional[float]:
        if not suggested_indexes and not plan_analysis.get('issues'):
            return None
        
        improvement = 0.0
        
        if suggested_indexes:
            improvement += len(suggested_indexes) * 20.0
        
        if plan_analysis.get('efficiency_score', 100) < 80:
            improvement += (80 - plan_analysis['efficiency_score']) * 0.8
        
        return min(85.0, improvement)

    def _get_command_info(self, command: str) -> Dict[str, Any]:
        command_info = {
            "complexity": "O(1)",
            "memory_impact": "low",
            "blocking": False,
            "thread_safe": True
        }
        
        # Redis command-specific information
        if command == "KEYS":
            command_info.update({
                "complexity": "O(N)",
                "memory_impact": "high",
                "blocking": True,
                "warning": "Should not be used in production"
            })
        elif command == "SCAN":
            command_info.update({
                "complexity": "O(1) per iteration",
                "memory_impact": "low",
                "blocking": False,
                "recommendation": "Use instead of KEYS"
            })
        elif command in ["GET", "SET"]:
            command_info.update({
                "complexity": "O(1)",
                "memory_impact": "low",
                "blocking": False
            })
        elif command in ["HGET", "HSET"]:
            command_info.update({
                "complexity": "O(1)",
                "memory_impact": "low",
                "blocking": False
            })
        elif command in ["HGETALL", "SMEMBERS"]:
            command_info.update({
                "complexity": "O(N)",
                "memory_impact": "high",
                "blocking": False,
                "warning": "Can be expensive for large data structures"
            })
        
        return command_info

    def _get_performance_implications(self, command: str, args: List[str]) -> List[str]:
        implications = []
        
        if command == "KEYS":
            implications.append("Blocks the entire Redis server")
            implications.append("High memory usage for large keyspaces")
        
        if command in ["FLUSHALL", "FLUSHDB"]:
            implications.append("Destructive operation - all data will be lost")
            implications.append("May cause performance issues during execution")
        
        if command in ["HGETALL", "SMEMBERS", "LRANGE"]:
            implications.append("May return large amounts of data")
            implications.append("High network and memory usage")
        
        if command in ["SAVE", "BGSAVE"]:
            implications.append("May impact performance during save operation")
        
        return implications

    def _get_command_optimizations(self, command: str, args: List[str]) -> List[str]:
        optimizations = []
        
        if command == "KEYS":
            optimizations.append("Use SCAN instead for production environments")
        
        if command in ["HGETALL", "SMEMBERS"]:
            optimizations.append("Consider using HSCAN/SSCAN for large datasets")
        
        if command == "LRANGE" and len(args) >= 3:
            optimizations.append("Use LTRIM to maintain list size")
            optimizations.append("Consider using streaming for large lists")
        
        if command == "ZRANGE" and len(args) >= 3:
            optimizations.append("Use ZSCAN for pattern-based queries")
        
        if command == "GET" and args:
            key = args[0]
            if self._is_potentially_large_key(key):
                optimizations.append("Consider using hash fields or smaller data structures")
        
        return optimizations

    def _is_potentially_large_key(self, key: str) -> bool:
        try:
            # Check if key exists and estimate size
            key_type = self.client.type(key)
            
            if key_type == 'string':
                size = self.client.strlen(key)
                return size > 1024  # > 1KB
            elif key_type == 'hash':
                size = self.client.hlen(key)
                return size > 100  # > 100 fields
            elif key_type == 'list':
                size = self.client.llen(key)
                return size > 1000  # > 1000 elements
            elif key_type == 'set':
                size = self.client.scard(key)
                return size > 1000  # > 1000 elements
            elif key_type == 'zset':
                size = self.client.zcard(key)
                return size > 1000  # > 1000 elements
        
        except:
            pass
        
        return False

    def _suggest_data_structures_for_key(self, key: str) -> List[str]:
        suggestions = []
        
        try:
            key_type = self.client.type(key)
            
            if key_type == 'string':
                suggestions.append("Consider using HASH for structured data")
                suggestions.append("Consider using LIST for ordered data")
            elif key_type == 'hash':
                suggestions.append("Consider using JSON for complex nested data")
                suggestions.append("Consider using multiple smaller hashes if field count is high")
            elif key_type == 'list':
                suggestions.append("Consider using ZSET for scored/ordered data")
                suggestions.append("Consider using STREAM for event data")
            elif key_type == 'set':
                suggestions.append("Consider using ZSET if ordering is needed")
                suggestions.append("Consider using HASH for field-value pairs")
            elif key_type == 'zset':
                suggestions.append("Consider using LIST for simple ordered data")
                suggestions.append("Consider using HASH if scores are not needed")
        
        except:
            suggestions.append("Analyze data access patterns for optimal structure")
        
        return suggestions

    def _generate_redis_specific_recommendations(self, metrics: List[QueryMetric]) -> List[str]:
        recommendations = []
        
        # Analyze command distribution
        command_counts = {}
        for metric in metrics:
            command = metric.query_type
            if command not in command_counts:
                command_counts[command] = 0
            command_counts[command] += 1
        
        # Check for expensive operations
        if command_counts.get('keys', 0) > 0:
            recommendations.append("Replace KEYS operations with SCAN for better performance")
        
        if command_counts.get('flushall', 0) > 0 or command_counts.get('flushdb', 0) > 0:
            recommendations.append("Review FLUSH operations - ensure they are necessary")
        
        # Check for large data structure operations
        expensive_commands = ['hgetall', 'smembers', 'lrange', 'zrange']
        expensive_count = sum(command_counts.get(cmd, 0) for cmd in expensive_commands)
        
        if expensive_count > len(metrics) * 0.2:  # > 20% of operations
            recommendations.append("Consider using SCAN-based operations for large data structures")
        
        return recommendations

    def get_query_plan_analysis(self, query_text: str, database: str) -> Dict[str, Any]:
        self.obs.log_info(f"get_query_plan_analysis database={database}")
        
        try:
            explain_result = self.explain_query(query_text, database)
            
            analysis = {
                "query": query_text,
                "database": database,
                "explain": explain_result,
                "analysis": {}
            }
            
            if explain_result.get("success"):
                analysis["analysis"]["command_info"] = explain_result.get("command_info", {})
                analysis["analysis"]["performance_implications"] = explain_result.get("performance_implications", [])
                analysis["analysis"]["optimization_suggestions"] = explain_result.get("optimization_suggestions", [])
                
                # Add Redis-specific analysis
                parts = query_text.split()
                if parts:
                    command = parts[0].upper()
                    analysis["analysis"]["redis_specific"] = self._get_redis_specific_analysis(command, parts[1:])
            
            return analysis
        
        except Exception as e:
            self.obs.log_error(f"Failed to get query plan analysis: {e}")
            return {
                "query": query_text,
                "database": database,
                "error": str(e)
            }

    def _get_redis_specific_analysis(self, command: str, args: List[str]) -> Dict[str, Any]:
        analysis = {
            "memory_efficiency": "high",
            "scalability": "good",
            "best_practices": []
        }
        
        if command == "KEYS":
            analysis["memory_efficiency"] = "low"
            analysis["scalability"] = "poor"
            analysis["best_practices"] = ["Use SCAN instead", "Avoid in production"]
        
        if command in ["GET", "SET"]:
            analysis["best_practices"] = ["Use appropriate key naming", "Consider TTL for expiration"]
        
        if command in ["HGET", "HSET"]:
            analysis["best_practices"] = ["Keep hash size reasonable", "Use field names efficiently"]
        
        if command in ["LPUSH", "RPUSH"]:
            analysis["best_practices"] = ["Use LTRIM for bounded lists", "Consider streaming for large lists"]
        
        return analysis

    def get_schema_analysis(self, database: str) -> Dict[str, Any]:
        self.obs.log_info(f"get_schema_analysis database={database}")
        
        try:
            from .redis_query_collector import RedisQueryCollector
            collector = RedisQueryCollector(self.client)
            
            # Redis doesn't have a traditional schema, but we can analyze the key space
            key_stats = collector.get_key_statistics()
            db_metrics = collector.get_database_metrics()
            connection_metrics = collector.get_connection_metrics()
            
            analysis = {
                "database_type": "redis",
                "keyspace_analysis": key_stats,
                "database_metrics": db_metrics,
                "connection_metrics": connection_metrics,
                "recommendations": self._generate_schema_recommendations(key_stats, db_metrics)
            }
            
            return {
                "success": True,
                "database": database,
                "schema": analysis,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to get schema analysis: {e}")
            return {
                "success": False,
                "database": database,
                "error": str(e)
            }

    def _generate_schema_recommendations(self, key_stats: Dict[str, Any], db_metrics: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        if key_stats.get('total_keys', 0) > 100000:
            recommendations.append("Large key count detected - consider key naming conventions and TTL management")
        
        key_types = key_stats.get('key_types', {})
        if key_types.get('string', 0) > key_types.get('hash', 0) * 2:
            recommendations.append("Consider using HASH for structured string data")
        
        ttl_dist = key_stats.get('ttl_distribution', {})
        if ttl_dist.get('no_ttl', 0) > ttl_dist.get('short_ttl', 0) + ttl_dist.get('medium_ttl', 0):
            recommendations.append("Consider setting TTL for keys to manage memory usage")
        
        memory_info = db_metrics.get('memory_info', {})
        if memory_info.get('used_memory', 0) > memory_info.get('maxmemory', 0) * 0.8:
            recommendations.append("Memory usage is high - consider optimization")
        
        return recommendations

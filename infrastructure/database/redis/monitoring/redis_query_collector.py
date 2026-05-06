import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import redis
from redis import Redis

project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.database.shared.query_monitoring_interfaces import (
    IQueryPerformanceCollector, QueryMetric, QueryStatus, QueryPerformanceLevel,
    QueryMonitoringConfig
)
from infrastructure.database.shared.query_monitoring_utils import (
    QueryHashGenerator, PerformanceClassifier, QueryMetricsAggregator,
    TimeWindowCalculator, QueryPlanAnalyzer
)
from infrastructure.observability.scripts.observability_client import ObservabilityClient
from ..client.redis_client import execute_command, get_redis_client, RedisConnectionConfig


class RedisQueryCollector(IQueryPerformanceCollector):
    def __init__(self, client: Redis, config: Optional[QueryMonitoringConfig] = None):
        self.client = client
        self.config = config or QueryMonitoringConfig()
        self.obs = ObservabilityClient(service_name="redis-query-collector")
        self._query_metrics_store = []
        self._max_store_size = self.config.max_query_history_size

    def collect_query_metrics(self, limit: int = 1000) -> List[QueryMetric]:
        self.obs.log_info(f"collect_query_metrics limit={limit}")
        
        metrics = []
        
        try:
            slow_log_metrics = self._get_slow_log_metrics()
            metrics.extend(slow_log_metrics)
            
            command_metrics = self._get_command_metrics()
            metrics.extend(command_metrics)
            
            key_metrics = self._get_key_operation_metrics()
            metrics.extend(key_metrics)
            
        except Exception as e:
            self.obs.log_error(f"Failed to collect query metrics: {e}")
        
        return metrics[:limit]

    def get_slow_queries(self, threshold_ms: float = 1000.0, limit: int = 50) -> List[QueryMetric]:
        self.obs.log_info(f"get_slow_queries threshold_ms={threshold_ms} limit={limit}")
        
        try:
            all_metrics = self.collect_query_metrics(limit * 2)
            
            slow_metrics = [
                metric for metric in all_metrics
                if metric.execution_time_ms >= threshold_ms
            ]
            
            return sorted(slow_metrics, key=lambda x: x.execution_time_ms, reverse=True)[:limit]
        
        except Exception as e:
            self.obs.log_error(f"Failed to get slow queries: {e}")
            return []

    def get_query_by_hash(self, query_hash: str) -> Optional[QueryMetric]:
        for metric in self._query_metrics_store:
            if metric.query_hash == query_hash:
                return metric
        return None

    def record_query_execution(self, query_metric: QueryMetric) -> None:
        self._query_metrics_store.append(query_metric)
        
        if len(self._query_metrics_store) > self._max_store_size:
            self._query_metrics_store = self._query_metrics_store[-self._max_store_size:]
        
        self.obs.log_info(f"record_query_execution hash={query_metric.query_hash} time_ms={query_metric.execution_time_ms}")

    def _get_slow_log_metrics(self) -> List[QueryMetric]:
        metrics = []
        
        try:
            from ..client.redis_client import get_slow_log
            slow_log = get_slow_log(self.client)
            
            for entry in slow_log:
                if entry['execution_time_micros']:
                    execution_time_ms = entry['execution_time_micros'] / 1000.0
                    
                    # Convert microseconds to milliseconds for comparison
                    if execution_time_ms >= self.config.slow_query_threshold_ms:
                        performance_level = PerformanceClassifier.classify_performance(
                            execution_time_ms,
                            PerformanceClassifier.get_default_thresholds()
                        )
                        
                        command_str = ' '.join(entry['command']) if isinstance(entry['command'], list) else str(entry['command'])
                        query_hash = QueryHashGenerator.generate_hash(command_str)
                        
                        metric = QueryMetric(
                            query_hash=query_hash,
                            query_type=self._extract_command_type(entry['command']),
                            database="redis",
                            collection_table=None,  # Redis doesn't have tables
                            execution_time_ms=execution_time_ms,
                            status=QueryStatus.SUCCESS,
                            performance_level=performance_level,
                            timestamp=datetime.fromtimestamp(entry['timestamp']) if entry['timestamp'] else datetime.utcnow(),
                            plan_details={
                                "slow_log_id": entry['id'],
                                "client_info": entry.get('client_info'),
                                "command": entry['command']
                            }
                        )
                        metrics.append(metric)
        
        except Exception as e:
            self.obs.log_error(f"Failed to get slow log metrics: {e}")
        
        return metrics

    def _get_command_metrics(self) -> List[QueryMetric]:
        metrics = []
        
        try:
            # Simulate common Redis commands with timing
            common_commands = [
                ("GET", "test_key"),
                ("SET", "test_key", "test_value"),
                ("HGET", "test_hash", "test_field"),
                ("HSET", "test_hash", "test_field", "test_value"),
                ("ZADD", "test_zset", "1", "test_member"),
                ("SADD", "test_set", "test_member"),
                ("LRANGE", "test_list", "0", "-1")
            ]
            
            for command_data in common_commands:
                command = command_data[0]
                args = command_data[1:]
                
                try:
                    result = execute_command(self.client, command.lower(), *args)
                    if result.success:
                        performance_level = PerformanceClassifier.classify_performance(
                            result.execution_time_ms,
                            PerformanceClassifier.get_default_thresholds()
                        )
                        
                        command_str = f"{command} {' '.join(map(str, args))}"
                        query_hash = QueryHashGenerator.generate_hash(command_str)
                        
                        metric = QueryMetric(
                            query_hash=query_hash,
                            query_type=command.lower(),
                            database="redis",
                            collection_table=None,
                            execution_time_ms=result.execution_time_ms,
                            status=QueryStatus.SUCCESS if result.success else QueryStatus.ERROR,
                            performance_level=performance_level,
                            timestamp=datetime.utcnow(),
                            affected_rows=result.key_count if result.key_count else 1,
                            plan_details={
                                "command": command,
                                "args": args,
                                "key_count": result.key_count
                            }
                        )
                        metrics.append(metric)
                except Exception:
                    pass  # Skip commands that fail
        
        except Exception as e:
            self.obs.log_error(f"Failed to get command metrics: {e}")
        
        return metrics

    def _get_key_operation_metrics(self) -> List[QueryMetric]:
        metrics = []
        
        try:
            # Get key statistics
            key_count = self.client.dbsize()
            
            # Create a metric for key space scan
            metric = QueryMetric(
                query_hash=QueryHashGenerator.generate_hash("KEYS *"),
                query_type="keys",
                database="redis",
                collection_table=None,
                execution_time_ms=50.0,  # Estimated time for keys operation
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.FAST,
                timestamp=datetime.utcnow(),
                affected_rows=key_count,
                plan_details={
                    "operation": "keyspace_scan",
                    "total_keys": key_count
                }
            )
            metrics.append(metric)
            
            # Get memory usage metrics
            try:
                memory_info = self.client.info('memory')
                if memory_info:
                    metric = QueryMetric(
                        query_hash=QueryHashGenerator.generate_hash("INFO memory"),
                        query_type="info",
                        database="redis",
                        collection_table=None,
                        execution_time_ms=20.0,
                        status=QueryStatus.SUCCESS,
                        performance_level=QueryPerformanceLevel.FAST,
                        timestamp=datetime.utcnow(),
                        plan_details={
                            "operation": "memory_info",
                            "memory_usage": memory_info.get('used_memory', 0)
                        }
                    )
                    metrics.append(metric)
            except:
                pass
        
        except Exception as e:
            self.obs.log_error(f"Failed to get key operation metrics: {e}")
        
        return metrics

    def _extract_command_type(self, command) -> str:
        if isinstance(command, list) and command:
            return command[0].lower()
        elif isinstance(command, str):
            return command.split()[0].lower()
        return "unknown"

    def get_performance_summary(self, period_minutes: int = 60) -> Dict[str, Any]:
        self.obs.log_info(f"get_performance_summary period_minutes={period_minutes}")
        
        time_window = TimeWindowCalculator.get_time_windows(period_minutes)
        recent_metrics = TimeWindowCalculator.filter_metrics_by_time(
            self._query_metrics_store,
            time_window['period_start'],
            time_window['period_end']
        )
        
        return QueryMetricsAggregator.aggregate_metrics(recent_metrics)

    def identify_index_gaps(self) -> List[Dict[str, Any]]:
        self.obs.log_info("identify_index_gaps")
        
        gaps = []
        
        try:
            slow_queries = self.get_slow_queries(threshold_ms=self.config.slow_query_threshold_ms)
            
            command_analysis = {}
            for metric in slow_queries:
                command_type = metric.query_type
                if command_type not in command_analysis:
                    command_analysis[command_type] = {
                        'slow_queries': [],
                        'avg_execution_time': 0
                    }
                
                command_analysis[command_type]['slow_queries'].append(metric)
            
            for command_type, analysis in command_analysis.items():
                if len(analysis['slow_queries']) > 5:
                    avg_time = sum(q.execution_time_ms for q in analysis['slow_queries']) / len(analysis['slow_queries'])
                    
                    gaps.append({
                        'command_type': command_type,
                        'slow_query_count': len(analysis['slow_queries']),
                        'avg_execution_time': avg_time,
                        'recommendation': f"Consider optimizing {command_type} operations or using Redis data structures more efficiently"
                    })
        
        except Exception as e:
            self.obs.log_error(f"Failed to identify index gaps: {e}")
        
        return gaps

    def get_database_metrics(self) -> Dict[str, Any]:
        self.obs.log_info("get_database_metrics")
        
        try:
            metrics = {}
            
            # Get basic info
            info = self.client.info()
            if info:
                metrics["redis_version"] = info.get("redis_version")
                metrics["redis_mode"] = info.get("redis_mode")
                metrics["uptime_seconds"] = info.get("uptime_in_seconds")
                metrics["connected_clients"] = info.get("connected_clients")
            
            # Get memory info
            memory_info = self.client.info('memory')
            if memory_info:
                metrics["used_memory"] = memory_info.get("used_memory")
                metrics["used_memory_human"] = memory_info.get("used_memory_human")
                metrics["used_memory_rss"] = memory_info.get("used_memory_rss")
                metrics["maxmemory"] = memory_info.get("maxmemory")
            
            # Get key space info
            keyspace_info = self.client.info('keyspace')
            if keyspace_info:
                metrics["keyspace"] = keyspace_info
            
            # Get database size
            metrics["database_size"] = self.client.dbsize()
            
            # Get slow log info
            slowlog_len = self.client.slowlog_len()
            metrics["slow_log_length"] = slowlog_len
            
            return metrics
        
        except Exception as e:
            self.obs.log_error(f"Failed to get database metrics: {e}")
            return {}

    def get_key_statistics(self, pattern: str = "*") -> Dict[str, Any]:
        self.obs.log_info(f"get_key_statistics pattern={pattern}")
        
        try:
            stats = {}
            
            # Get all keys matching pattern
            keys = self.client.keys(pattern)
            stats['total_keys'] = len(keys)
            
            # Analyze key types
            key_types = {}
            for key in keys[:1000]:  # Limit to first 1000 keys for performance
                key_type = self.client.type(key)
                if key_type not in key_types:
                    key_types[key_type] = 0
                key_types[key_type] += 1
            
            stats['key_types'] = key_types
            
            # Get memory usage for sample keys
            memory_usage = {}
            for key in keys[:100]:  # Sample first 100 keys
                try:
                    memory = self.client.memory_usage(key)
                    if memory:
                        memory_usage[key] = memory
                except:
                    pass
            
            stats['sample_memory_usage'] = memory_usage
            
            # Get TTL distribution
            ttl_stats = {'no_ttl': 0, 'short_ttl': 0, 'medium_ttl': 0, 'long_ttl': 0}
            for key in keys[:1000]:
                try:
                    ttl = self.client.ttl(key)
                    if ttl == -1:
                        ttl_stats['no_ttl'] += 1
                    elif ttl < 3600:  # < 1 hour
                        ttl_stats['short_ttl'] += 1
                    elif ttl < 86400:  # < 1 day
                        ttl_stats['medium_ttl'] += 1
                    else:
                        ttl_stats['long_ttl'] += 1
                except:
                    pass
            
            stats['ttl_distribution'] = ttl_stats
            
            return stats
        
        except Exception as e:
            self.obs.log_error(f"Failed to get key statistics: {e}")
            return {}

    def get_connection_metrics(self) -> Dict[str, Any]:
        self.obs.log_info("get_connection_metrics")
        
        try:
            metrics = {}
            
            # Get client info
            info = self.client.info('clients')
            if info:
                metrics["connected_clients"] = info.get("connected_clients")
                metrics["client_recent_max_input_buffer"] = info.get("client_recent_max_input_buffer")
                metrics["client_recent_max_output_buffer"] = info.get("client_recent_max_output_buffer")
                metrics["blocked_clients"] = info.get("blocked_clients")
            
            # Get stats info
            stats_info = self.client.info('stats')
            if stats_info:
                metrics["total_connections_received"] = stats_info.get("total_connections_received")
                metrics["total_commands_processed"] = stats_info.get("total_commands_processed")
                metrics["instantaneous_ops_per_sec"] = stats_info.get("instantaneous_ops_per_sec")
                metrics["total_net_input_bytes"] = stats_info.get("total_net_input_bytes")
                metrics["total_net_output_bytes"] = stats_info.get("total_net_output_bytes")
            
            return metrics
        
        except Exception as e:
            self.obs.log_error(f"Failed to get connection metrics: {e}")
            return {}

    def get_slow_log_analysis(self, limit: int = 50) -> Dict[str, Any]:
        self.obs.log_info(f"get_slow_log_analysis limit={limit}")
        
        try:
            from ..client.redis_client import get_slow_log
            slow_log = get_slow_log(self.client)
            
            if not slow_log:
                return {
                    "total_slow_queries": 0,
                    "analysis": {},
                    "slow_queries": []
                }
            
            # Analyze slow queries
            analysis = {
                "total_slow_queries": len(slow_log),
                "avg_execution_time_micros": sum(entry['execution_time_micros'] for entry in slow_log) / len(slow_log),
                "max_execution_time_micros": max(entry['execution_time_micros'] for entry in slow_log),
                "command_distribution": {},
                "time_distribution": {}
            }
            
            # Command distribution
            for entry in slow_log:
                command = entry['command'][0].lower() if entry['command'] and isinstance(entry['command'], list) else 'unknown'
                if command not in analysis["command_distribution"]:
                    analysis["command_distribution"][command] = 0
                analysis["command_distribution"][command] += 1
            
            # Time distribution (last 24 hours)
            now = datetime.utcnow()
            time_buckets = {"0-1h": 0, "1-6h": 0, "6-24h": 0, "24h+": 0}
            
            for entry in slow_log:
                if entry['timestamp']:
                    entry_time = datetime.fromtimestamp(entry['timestamp'])
                    hours_ago = (now - entry_time).total_seconds() / 3600
                    
                    if hours_ago <= 1:
                        time_buckets["0-1h"] += 1
                    elif hours_ago <= 6:
                        time_buckets["1-6h"] += 1
                    elif hours_ago <= 24:
                        time_buckets["6-24h"] += 1
                    else:
                        time_buckets["24h+"] += 1
            
            analysis["time_distribution"] = time_buckets
            
            return {
                "total_slow_queries": len(slow_log),
                "analysis": analysis,
                "slow_queries": slow_log[:limit]
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to get slow log analysis: {e}")
            return {
                "total_slow_queries": 0,
                "analysis": {},
                "slow_queries": [],
                "error": str(e)
            }

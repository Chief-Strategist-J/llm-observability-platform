import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import redis
from redis import Redis

project_root = Path(__file__).resolve().parents[4)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.database.shared.query_monitoring_interfaces import (
    IMetricsExporter, QueryMetric, QueryMonitoringConfig
)
from infrastructure.database.shared.query_monitoring_utils import MetricsFormatter
from infrastructure.observability.scripts.observability_client import ObservabilityClient
from ..client.redis_client import execute_command, get_redis_client, RedisConnectionConfig


class RedisMetricsExporter(IMetricsExporter):
    def __init__(self, client: Redis, config: Optional[QueryMonitoringConfig] = None):
        self.client = client
        self.config = config or QueryMonitoringConfig()
        self.obs = ObservabilityClient(service_name="redis-metrics-exporter")
        self._cached_metrics = {}
        self._cache_timestamp = None
        self._cache_ttl_seconds = 30

    def export_query_metrics(self, metrics: List[QueryMetric]) -> str:
        self.obs.log_info(f"export_query_metrics count={len(metrics)}")
        
        try:
            prometheus_format = MetricsFormatter.format_for_prometheus(metrics, "redis")
            self._cached_metrics['query_metrics'] = prometheus_format
            self._cache_timestamp = datetime.utcnow()
            
            return prometheus_format
        
        except Exception as e:
            self.obs.log_error(f"Failed to export query metrics: {e}")
            return ""

    def export_database_metrics(self, database: str, metrics: Dict[str, Any]) -> str:
        self.obs.log_info(f"export_database_metrics database={database}")
        
        try:
            prometheus_lines = []
            
            prometheus_lines.append(f"# HELP redis_database_info Database information")
            prometheus_lines.append(f"# TYPE redis_database_info gauge")
            prometheus_lines.append(f'redis_database_info{{database="{database}"}} 1')
            
            if 'redis_version' in metrics:
                prometheus_lines.append(f"# HELP redis_version Redis version")
                prometheus_lines.append(f"# TYPE redis_version gauge")
                prometheus_lines.append(f'redis_version{{database="{database}"}} 1')
            
            if 'database_size' in metrics:
                prometheus_lines.append(f"# HELP redis_database_size Total number of keys")
                prometheus_lines.append(f"# TYPE redis_database_size gauge")
                prometheus_lines.append(f'redis_database_size{{database="{database}"}} {metrics["database_size"]}')
            
            if 'used_memory' in metrics:
                prometheus_lines.append(f"# HELP redis_used_memory_bytes Used memory in bytes")
                prometheus_lines.append(f"# TYPE redis_used_memory_bytes gauge")
                prometheus_lines.append(f'redis_used_memory_bytes{{database="{database}"}} {metrics["used_memory"]}')
            
            if 'connected_clients' in metrics:
                prometheus_lines.append(f"# HELP redis_connected_clients Connected clients")
                prometheus_lines.append(f"# TYPE redis_connected_clients gauge")
                prometheus_lines.append(f'redis_connected_clients{{database="{database}"}} {metrics["connected_clients"]}')
            
            if 'uptime_seconds' in metrics:
                prometheus_lines.append(f"# HELP redis_uptime_seconds Uptime in seconds")
                prometheus_lines.append(f"# TYPE redis_uptime_seconds gauge")
                prometheus_lines.append(f'redis_uptime_seconds{{database="{database}"}} {metrics["uptime_seconds"]}')
            
            prometheus_lines.append(f"# HELP redis_export_timestamp_seconds Last export timestamp")
            prometheus_lines.append(f"# TYPE redis_export_timestamp_seconds gauge")
            prometheus_lines.append(f'redis_export_timestamp_seconds{{database="{database}"}} {datetime.utcnow().timestamp()}')
            
            return "\n".join(prometheus_lines)
        
        except Exception as e:
            self.obs.log_error(f"Failed to export database metrics: {e}")
            return ""

    def get_prometheus_metrics(self) -> str:
        self.obs.log_info("get_prometheus_metrics")
        
        try:
            all_metrics = []
            
            query_metrics = self._collect_database_query_metrics()
            if query_metrics:
                all_metrics.append(query_metrics)
            
            db_metrics = self._collect_database_status_metrics()
            if db_metrics:
                all_metrics.append(db_metrics)
            
            server_metrics = self._collect_server_metrics()
            if server_metrics:
                all_metrics.append(server_metrics)
            
            return "\n\n".join(filter(None, all_metrics))
        
        except Exception as e:
            self.obs.log_error(f"Failed to get prometheus metrics: {e}")
            return ""

    def _collect_database_query_metrics(self) -> str:
        try:
            from .redis_query_collector import RedisQueryCollector
            collector = RedisQueryCollector(self.client, self.config)
            
            metrics = collector.collect_query_metrics(limit=1000)
            return self.export_query_metrics(metrics)
        
        except Exception as e:
            self.obs.log_error(f"Failed to collect query metrics: {e}")
            return ""

    def _collect_database_status_metrics(self) -> str:
        try:
            from .redis_query_collector import RedisQueryCollector
            collector = RedisQueryCollector(self.client, self.config)
            
            db_metrics = collector.get_database_metrics()
            
            all_db_metrics = []
            for db_name in ["redis"]:
                metrics = self.export_database_metrics(db_name, db_metrics)
                if metrics:
                    all_db_metrics.append(metrics)
            
            return "\n\n".join(all_db_metrics)
        
        except Exception as e:
            self.obs.log_error(f"Failed to collect database status metrics: {e}")
            return ""

    def _collect_server_metrics(self) -> str:
        try:
            prometheus_lines = []
            
            # Get server info
            info = self.client.info()
            
            # Memory metrics
            memory_lines = self._get_memory_metrics(info)
            prometheus_lines.extend(memory_lines)
            
            # Client metrics
            client_lines = self._get_client_metrics(info)
            prometheus_lines.extend(client_lines)
            
            # Stats metrics
            stats_lines = self._get_stats_metrics(info)
            prometheus_lines.extend(stats_lines)
            
            # Persistence metrics
            persistence_lines = self._get_persistence_metrics(info)
            prometheus_lines.extend(persistence_lines)
            
            # Replication metrics
            replication_lines = self._get_replication_metrics(info)
            prometheus_lines.extend(replication_lines)
            
            # CPU metrics
            cpu_lines = self._get_cpu_metrics(info)
            prometheus_lines.extend(cpu_lines)
            
            prometheus_lines.append(f"# HELP redis_metrics_export_timestamp_seconds Last metrics export timestamp")
            prometheus_lines.append(f"# TYPE redis_metrics_export_timestamp_seconds gauge")
            prometheus_lines.append(f'redis_metrics_export_timestamp_seconds {datetime.utcnow().timestamp()}')
            
            return "\n".join(prometheus_lines)
        
        except Exception as e:
            self.obs.log_error(f"Failed to collect server metrics: {e}")
            return ""

    def _get_memory_metrics(self, info: Dict[str, Any]) -> List[str]:
        lines = []
        
        try:
            memory_info = info.get('memory', {})
            
            if 'used_memory' in memory_info:
                lines.append(f"# HELP redis_memory_used_bytes Used memory in bytes")
                lines.append(f"# TYPE redis_memory_used_bytes gauge")
                lines.append(f'redis_memory_used_bytes {memory_info["used_memory"]}')
            
            if 'used_memory_rss' in memory_info:
                lines.append(f"# HELP redis_memory_used_rss_bytes RSS memory used in bytes")
                lines.append(f"# TYPE redis_memory_used_rss_bytes gauge")
                lines.append(f'redis_memory_used_rss_bytes {memory_info["used_memory_rss"]}')
            
            if 'used_memory_peak' in memory_info:
                lines.append(f"# HELP redis_memory_used_peak_bytes Peak memory used in bytes")
                lines.append(f"# TYPE redis_memory_used_peak_bytes gauge")
                lines.append(f'redis_memory_used_peak_bytes {memory_info["used_memory_peak"]}')
            
            if 'maxmemory' in memory_info:
                lines.append(f"# HELP redis_memory_max_bytes Maximum memory in bytes")
                lines.append(f"# TYPE redis_memory_max_bytes gauge")
                lines.append(f'redis_memory_max_bytes {memory_info["maxmemory"]}')
            
            if 'used_memory_lua' in memory_info:
                lines.append(f"# HELP redis_memory_lua_bytes Lua script memory in bytes")
                lines.append(f"# TYPE redis_memory_lua_bytes gauge")
                lines.append(f'redis_memory_lua_bytes {memory_info["used_memory_lua"]}')
            
            if 'mem_fragmentation_ratio' in memory_info:
                lines.append(f"# HELP redis_memory_fragmentation_ratio Memory fragmentation ratio")
                lines.append(f"# TYPE redis_memory_fragmentation_ratio gauge")
                lines.append(f'redis_memory_fragmentation_ratio {memory_info["mem_fragmentation_ratio"]}')
        
        except Exception as e:
            self.obs.log_error(f"Failed to get memory metrics: {e}")
        
        return lines

    def _get_client_metrics(self, info: Dict[str, Any]) -> List[str]:
        lines = []
        
        try:
            client_info = info.get('clients', {})
            
            if 'connected_clients' in client_info:
                lines.append(f"# HELP redis_connected_clients Connected clients")
                lines.append(f"# TYPE redis_connected_clients gauge")
                lines.append(f'redis_connected_clients {client_info["connected_clients"]}')
            
            if 'client_recent_max_input_buffer' in client_info:
                lines.append(f"# HELP redis_client_max_input_buffer_bytes Max input buffer size")
                lines.append(f"# TYPE redis_client_max_input_buffer_bytes gauge")
                lines.append(f'redis_client_max_input_buffer_bytes {client_info["client_recent_max_input_buffer"]}')
            
            if 'client_recent_max_output_buffer' in client_info:
                lines.append(f"# HELP redis_client_max_output_buffer_bytes Max output buffer size")
                lines.append(f"# TYPE redis_client_max_output_buffer_bytes gauge")
                lines.append(f'redis_client_max_output_buffer_bytes {client_info["client_recent_max_output_buffer"]}')
            
            if 'blocked_clients' in client_info:
                lines.append(f"# HELP redis_blocked_clients Blocked clients")
                lines.append(f"# TYPE redis_blocked_clients gauge")
                lines.append(f'redis_blocked_clients {client_info["blocked_clients"]}')
        
        except Exception as e:
            self.obs.log_error(f"Failed to get client metrics: {e}")
        
        return lines

    def _get_stats_metrics(self, info: Dict[str, Any]) -> List[str]:
        lines = []
        
        try:
            stats_info = info.get('stats', {})
            
            if 'total_connections_received' in stats_info:
                lines.append(f"# HELP redis_total_connections_received Total connections received")
                lines.append(f"# TYPE redis_total_connections_received counter")
                lines.append(f'redis_total_connections_received {stats_info["total_connections_received"]}')
            
            if 'total_commands_processed' in stats_info:
                lines.append(f"# HELP redis_total_commands_processed Total commands processed")
                lines.append(f"# TYPE redis_total_commands_processed counter")
                lines.append(f'redis_total_commands_processed {stats_info["total_commands_processed"]}')
            
            if 'instantaneous_ops_per_sec' in stats_info:
                lines.append(f"# HELP redis_instantaneous_ops_per_sec Instantaneous operations per second")
                lines.append(f"# TYPE redis_instantaneous_ops_per_sec gauge")
                lines.append(f'redis_instantaneous_ops_per_sec {stats_info["instantaneous_ops_per_sec"]}')
            
            if 'keyspace_hits' in stats_info:
                lines.append(f"# HELP redis_keyspace_hits Keyspace hits")
                lines.append(f"# TYPE redis_keyspace_hits counter")
                lines.append(f'redis_keyspace_hits {stats_info["keyspace_hits"]}')
            
            if 'keyspace_misses' in stats_info:
                lines.append(f"# HELP redis_keyspace_misses Keyspace misses")
                lines.append(f"# TYPE redis_keyspace_misses counter")
                lines.append(f'redis_keyspace_misses {stats_info["keyspace_misses"]}')
            
            if 'keyspace_hits' in stats_info and 'keyspace_misses' in stats_info:
                hits = stats_info["keyspace_hits"]
                misses = stats_info["keyspace_misses"]
                total = hits + misses
                if total > 0:
                    hit_rate = (hits / total) * 100
                    lines.append(f"# HELP redis_keyspace_hit_rate_percent Keyspace hit rate percentage")
                    lines.append(f"# TYPE redis_keyspace_hit_rate_percent gauge")
                    lines.append(f'redis_keyspace_hit_rate_percent {hit_rate}')
        
        except Exception as e:
            self.obs.log_error(f"Failed to get stats metrics: {e}")
        
        return lines

    def _get_persistence_metrics(self, info: Dict[str, Any]) -> List[str]:
        lines = []
        
        try:
            persistence_info = info.get('persistence', {})
            
            if 'rdb_changes_since_last_save' in persistence_info:
                lines.append(f"# HELP redis_rdb_changes_since_last_save Changes since last RDB save")
                lines.append(f"# TYPE redis_rdb_changes_since_last_save gauge")
                lines.append(f'redis_rdb_changes_since_last_save {persistence_info["rdb_changes_since_last_save"]}')
            
            if 'rdb_bgsave_in_progress' in persistence_info:
                lines.append(f"# HELP redis_rdb_bgsave_in_progress RDB background save in progress")
                lines.append(f"# TYPE redis_rdb_bgsave_in_progress gauge")
                lines.append(f'redis_rdb_bgsave_in_progress {1 if persistence_info["rdb_bgsave_in_progress"] else 0}')
            
            if 'rdb_last_save_time' in persistence_info:
                lines.append(f"# HELP redis_rdb_last_save_time_seconds Time of last RDB save")
                lines.append(f"# TYPE redis_rdb_last_save_time_seconds gauge")
                lines.append(f'redis_rdb_last_save_time_seconds {persistence_info["rdb_last_save_time"]}')
            
            if 'aof_rewrite_in_progress' in persistence_info:
                lines.append(f"# HELP redis_aof_rewrite_in_progress AOF rewrite in progress")
                lines.append(f"# TYPE redis_aof_rewrite_in_progress gauge")
                lines.append(f'redis_aof_rewrite_in_progress {1 if persistence_info["aof_rewrite_in_progress"] else 0}')
        
        except Exception as e:
            self.obs.log_error(f"Failed to get persistence metrics: {e}")
        
        return lines

    def _get_replication_metrics(self, info: Dict[str, Any]) -> List[str]:
        lines = []
        
        try:
            replication_info = info.get('replication', {})
            
            if 'connected_slaves' in replication_info:
                lines.append(f"# HELP redis_connected_slaves Connected slaves")
                lines.append(f"# TYPE redis_connected_slaves gauge")
                lines.append(f'redis_connected_slaves {replication_info["connected_slaves"]}')
            
            if 'master_repl_offset' in replication_info:
                lines.append(f"# HELP redis_master_repl_offset Master replication offset")
                lines.append(f"# TYPE redis_master_repl_offset counter")
                lines.append(f'redis_master_repl_offset {replication_info["master_repl_offset"]}')
            
            if 'repl_backlog_size' in replication_info:
                lines.append(f"# HELP redis_repl_backlog_size_bytes Replication backlog size")
                lines.append(f"# TYPE redis_repl_backlog_size_bytes gauge")
                lines.append(f'redis_repl_backlog_size_bytes {replication_info["repl_backlog_size"]}')
        
        except Exception as e:
            self.obs.log_error(f"Failed to get replication metrics: {e}")
        
        return lines

    def _get_cpu_metrics(self, info: Dict[str, Any]) -> List[str]:
        lines = []
        
        try:
            cpu_info = info.get('cpu', {})
            
            if 'used_cpu_sys' in cpu_info:
                lines.append(f"# HELP redis_cpu_used_sys_seconds System CPU time used")
                lines.append(f"# TYPE redis_cpu_used_sys_seconds counter")
                lines.append(f'redis_cpu_used_sys_seconds {cpu_info["used_cpu_sys"]}')
            
            if 'used_cpu_user' in cpu_info:
                lines.append(f"# HELP redis_cpu_used_user_seconds User CPU time used")
                lines.append(f"# TYPE redis_cpu_used_user_seconds counter")
                lines.append(f'redis_cpu_used_user_seconds {cpu_info["used_cpu_user"]}')
            
            if 'used_cpu_sys_children' in cpu_info:
                lines.append(f"# HELP redis_cpu_used_sys_children_seconds System CPU time used by children")
                lines.append(f"# TYPE redis_cpu_used_sys_children_seconds counter")
                lines.append(f'redis_cpu_used_sys_children_seconds {cpu_info["used_cpu_sys_children"]}')
            
            if 'used_cpu_user_children' in cpu_info:
                lines.append(f"# HELP redis_cpu_used_user_children_seconds User CPU time used by children")
                lines.append(f"# TYPE redis_cpu_used_user_children_seconds counter")
                lines.append(f'redis_cpu_used_user_children_seconds {cpu_info["used_cpu_user_children"]}')
        
        except Exception as e:
            self.obs.log_error(f"Failed to get CPU metrics: {e}")
        
        return lines

    def get_health_status(self) -> Dict[str, Any]:
        self.obs.log_info("get_health_status")
        
        try:
            health_score = 100
            issues = []
            
            connectivity_result = self._test_connectivity()
            if not connectivity_result["success"]:
                health_score -= 50
                issues.append("Database connectivity failed")
            
            query_result = self._test_simple_query()
            if not query_result["success"]:
                health_score -= 30
                issues.append("Simple query test failed")
            
            memory_health = self._check_memory_health()
            if not memory_health["healthy"]:
                health_score -= 20
                issues.append("Memory health issues detected")
            
            performance_health = self._check_performance_health()
            if not performance_health["healthy"]:
                health_score -= 15
                issues.append("Performance health issues detected")
            
            return {
                "healthy": health_score >= 70,
                "health_score": health_score,
                "connectivity": connectivity_result,
                "query_test": query_result,
                "memory_health": memory_health,
                "performance_health": performance_health,
                "issues": issues,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to get health status: {e}")
            return {
                "healthy": False,
                "health_score": 0,
                "issues": [f"Health check failed: {str(e)}"],
                "timestamp": datetime.utcnow().isoformat()
            }

    def _test_connectivity(self) -> Dict[str, Any]:
        try:
            result = self.client.ping()
            
            return {
                "success": result,
                "error": None if result else "Ping failed"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _test_simple_query(self) -> Dict[str, Any]:
        try:
            result = self.client.info()
            
            return {
                "success": bool(result),
                "info_keys": len(result) if result else 0,
                "error": None if result else "Info command failed"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _check_memory_health(self) -> Dict[str, Any]:
        try:
            info = self.client.info('memory')
            
            used_memory = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)
            
            if max_memory > 0:
                memory_usage_percent = (used_memory / max_memory) * 100
                healthy = memory_usage_percent < 80
            else:
                # If no max memory set, check fragmentation ratio
                frag_ratio = info.get('mem_fragmentation_ratio', 1.0)
                healthy = frag_ratio < 1.5
                memory_usage_percent = None
            
            return {
                "healthy": healthy,
                "used_memory_bytes": used_memory,
                "max_memory_bytes": max_memory,
                "memory_usage_percent": memory_usage_percent,
                "fragmentation_ratio": info.get('mem_fragmentation_ratio', 1.0)
            }
        
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    def _check_performance_health(self) -> Dict[str, Any]:
        try:
            info = self.client.info('stats')
            
            ops_per_sec = info.get('instantaneous_ops_per_sec', 0)
            total_commands = info.get('total_commands_processed', 0)
            connected_clients = info.get('connected_clients', 0)
            
            # Health checks
            ops_healthy = ops_per_sec < 10000  # Very high ops/sec might indicate issues
            clients_healthy = connected_clients < 1000  # High client count might indicate issues
            
            healthy = ops_healthy and clients_healthy
            
            return {
                "healthy": healthy,
                "instantaneous_ops_per_sec": ops_per_sec,
                "total_commands_processed": total_commands,
                "connected_clients": connected_clients
            }
        
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    def export_json_metrics(self) -> Dict[str, Any]:
        self.obs.log_info("export_json_metrics")
        
        try:
            from .redis_query_collector import RedisQueryCollector
            collector = RedisQueryCollector(self.client, self.config)
            
            query_metrics = collector.collect_query_metrics(limit=1000)
            
            db_metrics = collector.get_database_metrics()
            
            key_stats = collector.get_key_statistics()
            
            connection_metrics = collector.get_connection_metrics()
            
            health = self.get_health_status()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "database": "redis",
                "query_metrics": MetricsFormatter.format_for_json_export(query_metrics, "redis"),
                "database_metrics": db_metrics,
                "key_statistics": key_stats,
                "connection_metrics": connection_metrics,
                "health": health
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to export JSON metrics: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "database": "redis",
                "error": str(e)
            }

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from pymongo import MongoClient

project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.database.shared.query_monitoring_interfaces import (
    IMetricsExporter, QueryMetric, QueryMonitoringConfig
)
from infrastructure.database.shared.query_monitoring_utils import MetricsFormatter
from infrastructure.observability.scripts.observability_client import ObservabilityClient


class MongoDBMetricsExporter(IMetricsExporter):
    def __init__(self, client: MongoClient, config: Optional[QueryMonitoringConfig] = None):
        self.client = client
        self.config = config or QueryMonitoringConfig()
        self.obs = ObservabilityClient(service_name="mongodb-metrics-exporter")
        self._cached_metrics = {}
        self._cache_timestamp = None
        self._cache_ttl_seconds = 30

    def export_query_metrics(self, metrics: List[QueryMetric]) -> str:
        self.obs.log_info(f"export_query_metrics count={len(metrics)}")
        
        try:
            prometheus_format = MetricsFormatter.format_for_prometheus(metrics, "mongodb")
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
            
            prometheus_lines.append(f"# HELP mongodb_database_info Database information")
            prometheus_lines.append(f"# TYPE mongodb_database_info gauge")
            prometheus_lines.append(f'mongodb_database_info{{database="{database}"}} 1')
            
            if 'collections' in metrics:
                prometheus_lines.append(f"# HELP mongodb_collections_total Number of collections")
                prometheus_lines.append(f"# TYPE mongodb_collections_total gauge")
                prometheus_lines.append(f'mongodb_collections_total{{database="{database}"}} {metrics["collections"]}')
            
            if 'data_size' in metrics:
                prometheus_lines.append(f"# HELP mongodb_data_size_bytes Total data size in bytes")
                prometheus_lines.append(f"# TYPE mongodb_data_size_bytes gauge")
                prometheus_lines.append(f'mongodb_data_size_bytes{{database="{database}"}} {metrics["data_size"]}')
            
            if 'storage_size' in metrics:
                prometheus_lines.append(f"# HELP mongodb_storage_size_bytes Total storage size in bytes")
                prometheus_lines.append(f"# TYPE mongodb_storage_size_bytes gauge")
                prometheus_lines.append(f'mongodb_storage_size_bytes{{database="{database}"}} {metrics["storage_size"]}')
            
            if 'index_size' in metrics:
                prometheus_lines.append(f"# HELP mongodb_index_size_bytes Total index size in bytes")
                prometheus_lines.append(f"# TYPE mongodb_index_size_bytes gauge")
                prometheus_lines.append(f'mongodb_index_size_bytes{{database="{database}"}} {metrics["index_size"]}')
            
            if 'connections' in metrics:
                conn = metrics['connections']
                prometheus_lines.append(f"# HELP mongodb_connections_current Current connections")
                prometheus_lines.append(f"# TYPE mongodb_connections_current gauge")
                prometheus_lines.append(f'mongodb_connections_current{{database="{database}"}} {conn.get("current", 0)}')
                
                prometheus_lines.append(f"# HELP mongodb_connections_available Available connections")
                prometheus_lines.append(f"# TYPE mongodb_connections_available gauge")
                prometheus_lines.append(f'mongodb_connections_available{{database="{database}"}} {conn.get("available", 0)}')
            
            if 'operations' in metrics:
                ops = metrics['operations']
                for op_type, count in ops.items():
                    prometheus_lines.append(f"# HELP mongodb_operations_total Total operations by type")
                    prometheus_lines.append(f"# TYPE mongodb_operations_total counter")
                    prometheus_lines.append(f'mongodb_operations_total{{database="{database}",type="{op_type}"}} {count}')
            
            if 'memory' in metrics:
                mem = metrics['memory']
                prometheus_lines.append(f"# HELP mongodb_memory_resident_bytes Resident memory in bytes")
                prometheus_lines.append(f"# TYPE mongodb_memory_resident_bytes gauge")
                prometheus_lines.append(f'mongodb_memory_resident_bytes{{database="{database}"}} {mem.get("resident", 0)}')
                
                prometheus_lines.append(f"# HELP mongodb_memory_virtual_bytes Virtual memory in bytes")
                prometheus_lines.append(f"# TYPE mongodb_memory_virtual_bytes gauge")
                prometheus_lines.append(f'mongodb_memory_virtual_bytes{{database="{database}"}} {mem.get("virtual", 0)}')
            
            prometheus_lines.append(f"# HELP mongodb_export_timestamp_seconds Last export timestamp")
            prometheus_lines.append(f"# TYPE mongodb_export_timestamp_seconds gauge")
            prometheus_lines.append(f'mongodb_export_timestamp_seconds{{database="{database}"}} {datetime.utcnow().timestamp()}')
            
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
            from .mongodb_query_collector import MongoDBQueryCollector
            collector = MongoDBQueryCollector(self.client, self.config)
            
            metrics = collector.collect_query_metrics(limit=1000)
            return self.export_query_metrics(metrics)
        
        except Exception as e:
            self.obs.log_error(f"Failed to collect query metrics: {e}")
            return ""

    def _collect_database_status_metrics(self) -> str:
        try:
            admin_db = self.client.admin
            
            db_stats = {}
            for db_name in self.client.list_database_names():
                if db_name not in ['admin', 'config', 'local']:
                    stats = self.client[db_name].command("dbStats")
                    db_stats[db_name] = stats
            
            all_db_metrics = []
            for db_name, stats in db_stats.items():
                metrics = self.export_database_metrics(db_name, stats)
                if metrics:
                    all_db_metrics.append(metrics)
            
            return "\n\n".join(all_db_metrics)
        
        except Exception as e:
            self.obs.log_error(f"Failed to collect database status metrics: {e}")
            return ""

    def _collect_server_metrics(self) -> str:
        try:
            server_status = self.client.admin.command("serverStatus")
            
            prometheus_lines = []
            
            prometheus_lines.append(f"# HELP mongodb_server_info MongoDB server information")
            prometheus_lines.append(f"# TYPE mongodb_server_info gauge")
            prometheus_lines.append(f'mongodb_server_info{{version="{server_status.get("version", "unknown")}"}} 1')
            
            uptime = server_status.get("uptime", 0)
            prometheus_lines.append(f"# HELP mongodb_uptime_seconds Server uptime in seconds")
            prometheus_lines.append(f"# TYPE mongodb_uptime_seconds gauge")
            prometheus_lines.append(f'mongodb_uptime_seconds {uptime}')
            
            connections = server_status.get("connections", {})
            prometheus_lines.append(f"# HELP mongodb_connections_current Current connections")
            prometheus_lines.append(f"# TYPE mongodb_connections_current gauge")
            prometheus_lines.append(f'mongodb_connections_current {connections.get("current", 0)}')
            
            prometheus_lines.append(f"# HELP mongodb_connections_available Available connections")
            prometheus_lines.append(f"# TYPE mongodb_connections_available gauge")
            prometheus_lines.append(f'mongodb_connections_available {connections.get("available", 0)}')
            
            prometheus_lines.append(f"# HELP mongodb_connections_total_created Total created connections")
            prometheus_lines.append(f"# TYPE mongodb_connections_total_created counter")
            prometheus_lines.append(f'mongodb_connections_total_created {connections.get("totalCreated", 0)}')
            
            opcounters = server_status.get("opcounters", {})
            for op_type, count in opcounters.items():
                prometheus_lines.append(f"# HELP mongodb_operations_total Total operations by type")
                prometheus_lines.append(f"# TYPE mongodb_operations_total counter")
                prometheus_lines.append(f'mongodb_operations_total{{type="{op_type}"}} {count}')
            
            mem = server_status.get("mem", {})
            prometheus_lines.append(f"# HELP mongodb_memory_resident_bytes Resident memory in bytes")
            prometheus_lines.append(f"# TYPE mongodb_memory_resident_bytes gauge")
            prometheus_lines.append(f'mongodb_memory_resident_bytes {mem.get("resident", 0) * 1024 * 1024}')
            
            prometheus_lines.append(f"# HELP mongodb_memory_virtual_bytes Virtual memory in bytes")
            prometheus_lines.append(f"# TYPE mongodb_memory_virtual_bytes gauge")
            prometheus_lines.append(f'mongodb_memory_virtual_bytes {mem.get("virtual", 0) * 1024 * 1024}')
            
            wired_tiger = server_status.get("wiredTiger", {})
            if wired_tiger:
                cache = wired_tiger.get("cache", {})
                if cache:
                    prometheus_lines.append(f"# HELP mongodb_cache_bytes_current WiredTiger cache current bytes")
                    prometheus_lines.append(f"# TYPE mongodb_cache_bytes_current gauge")
                    prometheus_lines.append(f'mongodb_cache_bytes_current {cache.get("bytes currently in the cache", 0)}')
                    
                    prometheus_lines.append(f"# HELP mongodb_cache_bytes_maximum WiredTiger cache maximum bytes")
                    prometheus_lines.append(f"# TYPE mongodb_cache_bytes_maximum gauge")
                    prometheus_lines.append(f'mongodb_cache_bytes_maximum {cache.get("maximum bytes configured", 0)}')
                    
                    prometheus_lines.append(f"# HELP mongodb_cache_bytes_dirty WiredTiger cache dirty bytes")
                    prometheus_lines.append(f"# TYPE mongodb_cache_bytes_dirty gauge")
                    prometheus_lines.append(f'mongodb_cache_bytes_dirty {cache.get("dirty bytes in the cache", 0)}')
            
            prometheus_lines.append(f"# HELP mongodb_metrics_export_timestamp_seconds Last metrics export timestamp")
            prometheus_lines.append(f"# TYPE mongodb_metrics_export_timestamp_seconds gauge")
            prometheus_lines.append(f'mongodb_metrics_export_timestamp_seconds {datetime.utcnow().timestamp()}')
            
            return "\n".join(prometheus_lines)
        
        except Exception as e:
            self.obs.log_error(f"Failed to collect server metrics: {e}")
            return ""

    def get_health_status(self) -> Dict[str, Any]:
        self.obs.log_info("get_health_status")
        
        try:
            admin_db = self.client.admin
            
            server_status = admin_db.command("serverStatus")
            
            uptime = server_status.get("uptime", 0)
            connections = server_status.get("connections", {})
            current_connections = connections.get("current", 0)
            available_connections = connections.get("available", 0)
            
            health_score = 100
            issues = []
            
            if uptime < 60:
                health_score -= 20
                issues.append("Server recently restarted")
            
            if current_connections > available_connections * 0.8:
                health_score -= 30
                issues.append("High connection usage")
            
            try:
                admin_db.command("ping")
            except Exception:
                health_score -= 50
                issues.append("Database ping failed")
            
            return {
                "healthy": health_score >= 70,
                "health_score": health_score,
                "uptime_seconds": uptime,
                "connections": {
                    "current": current_connections,
                    "available": available_connections,
                    "usage_percent": (current_connections / max(available_connections, 1)) * 100
                },
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

    def export_json_metrics(self) -> Dict[str, Any]:
        self.obs.log_info("export_json_metrics")
        
        try:
            from .mongodb_query_collector import MongoDBQueryCollector
            collector = MongoDBQueryCollector(self.client, self.config)
            
            query_metrics = collector.collect_query_metrics(limit=1000)
            
            server_status = self.client.admin.command("serverStatus")
            
            db_stats = {}
            for db_name in self.client.list_database_names():
                if db_name not in ['admin', 'config', 'local']:
                    stats = self.client[db_name].command("dbStats")
                    db_stats[db_name] = stats
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "database": "mongodb",
                "query_metrics": MetricsFormatter.format_for_json_export(query_metrics, "mongodb"),
                "server_status": server_status,
                "database_stats": db_stats,
                "health": self.get_health_status()
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to export JSON metrics: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "database": "mongodb",
                "error": str(e)
            }

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from cassandra.cluster import Session

project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.database.shared.query_monitoring_interfaces import (
    IMetricsExporter, QueryMetric, QueryMonitoringConfig
)
from infrastructure.database.shared.query_monitoring_utils import MetricsFormatter
from infrastructure.observability.scripts.observability_client import ObservabilityClient
from ..client.cassandra_client import execute_query


class CassandraMetricsExporter(IMetricsExporter):
    def __init__(self, session: Session, config: Optional[QueryMonitoringConfig] = None):
        self.session = session
        self.config = config or QueryMonitoringConfig()
        self.obs = ObservabilityClient(service_name="cassandra-metrics-exporter")
        self._cached_metrics = {}
        self._cache_timestamp = None
        self._cache_ttl_seconds = 30

    def export_query_metrics(self, metrics: List[QueryMetric]) -> str:
        self.obs.log_info(f"export_query_metrics count={len(metrics)}")
        
        try:
            prometheus_format = MetricsFormatter.format_for_prometheus(metrics, "cassandra")
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
            
            prometheus_lines.append(f"# HELP cassandra_database_info Database information")
            prometheus_lines.append(f"# TYPE cassandra_database_info gauge")
            prometheus_lines.append(f'cassandra_database_info{{database="{database}"}} 1')
            
            if 'cluster_name' in metrics:
                prometheus_lines.append(f"# HELP cassandra_cluster_name Cluster name")
                prometheus_lines.append(f"# TYPE cassandra_cluster_name gauge")
                prometheus_lines.append(f'cassandra_cluster_name{{database="{database}"}} 1')
            
            if 'table_count' in metrics:
                prometheus_lines.append(f"# HELP cassandra_tables_total Total number of tables")
                prometheus_lines.append(f"# TYPE cassandra_tables_total gauge")
                prometheus_lines.append(f'cassandra_tables_total{{database="{database}"}} {metrics["table_count"]}')
            
            if 'node_count' in metrics:
                prometheus_lines.append(f"# HELP cassandra_nodes_total Total number of nodes")
                prometheus_lines.append(f"# TYPE cassandra_nodes_total gauge")
                prometheus_lines.append(f'cassandra_nodes_total{{database="{database}"}} {metrics["node_count"]}')
            
            prometheus_lines.append(f"# HELP cassandra_export_timestamp_seconds Last export timestamp")
            prometheus_lines.append(f"# TYPE cassandra_export_timestamp_seconds gauge")
            prometheus_lines.append(f'cassandra_export_timestamp_seconds{{database="{database}"}} {datetime.utcnow().timestamp()}')
            
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
            from .cassandra_query_collector import CassandraQueryCollector
            collector = CassandraQueryCollector(self.session, self.config)
            
            metrics = collector.collect_query_metrics(limit=1000)
            return self.export_query_metrics(metrics)
        
        except Exception as e:
            self.obs.log_error(f"Failed to collect query metrics: {e}")
            return ""

    def _collect_database_status_metrics(self) -> str:
        try:
            from .cassandra_query_collector import CassandraQueryCollector
            collector = CassandraQueryCollector(self.session, self.config)
            
            db_metrics = collector.get_database_metrics()
            
            all_db_metrics = []
            for db_name in [self.session.keyspace]:
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
            
            node_metrics = self._get_node_metrics()
            prometheus_lines.extend(node_metrics)
            
            table_metrics = self._get_table_metrics()
            prometheus_lines.extend(table_metrics)
            
            compaction_metrics = self._get_compaction_metrics()
            prometheus_lines.extend(compaction_metrics)
            
            prometheus_lines.append(f"# HELP cassandra_metrics_export_timestamp_seconds Last metrics export timestamp")
            prometheus_lines.append(f"# TYPE cassandra_metrics_export_timestamp_seconds gauge")
            prometheus_lines.append(f'cassandra_metrics_export_timestamp_seconds {datetime.utcnow().timestamp()}')
            
            return "\n".join(prometheus_lines)
        
        except Exception as e:
            self.obs.log_error(f"Failed to collect server metrics: {e}")
            return ""

    def _get_node_metrics(self) -> List[str]:
        lines = []
        
        try:
            # Get node status
            node_query = "SELECT * FROM system.local"
            result = execute_query(self.session, node_query)
            if result.success and result.records:
                record = result.records[0]
                
                lines.append(f"# HELP cassandra_node_uptime_seconds Node uptime in seconds")
                lines.append(f"# TYPE cassandra_node_uptime_seconds gauge")
                lines.append(f'cassandra_node_uptime_seconds 0')  # Placeholder
                
                lines.append(f"# HELP cassandra_node_status Node status")
                lines.append(f"# TYPE cassandra_node_status gauge")
                lines.append(f'cassandra_node_status 1')  # Up
            
            # Get peer nodes
            peer_query = "SELECT * FROM system.peers"
            result = execute_query(self.session, peer_query)
            if result.success:
                peer_count = len(result.records)
                
                lines.append(f"# HELP cassandra_peer_nodes_count Number of peer nodes")
                lines.append(f"# TYPE cassandra_peer_nodes_count gauge")
                lines.append(f'cassandra_peer_nodes_count {peer_count}')
        
        except Exception as e:
            self.obs.log_error(f"Failed to get node metrics: {e}")
        
        return lines

    def _get_table_metrics(self) -> List[str]:
        lines = []
        
        try:
            # Get table statistics
            table_query = "SELECT table_name FROM system_schema.tables WHERE keyspace_name = %s"
            result = execute_query(self.session, table_query, {"keyspace_name": self.session.keyspace})
            
            if result.success:
                table_count = len(result.records)
                
                lines.append(f"# HELP cassandra_tables_count Number of tables in keyspace")
                lines.append(f"# TYPE cassandra_tables_count gauge")
                lines.append(f'cassandra_tables_count{{keyspace="{self.session.keyspace}"}} {table_count}')
                
                # Get detailed metrics for each table
                for record in result.records[:20]:  # Limit to first 20 tables
                    table_name = record["table_name"]
                    
                    lines.append(f'# HELP cassandra_table_size_estimated Estimated size for table {table_name}')
                    lines.append(f'# TYPE cassandra_table_size_estimated gauge')
                    lines.append(f'cassandra_table_size_estimated{{table="{table_name}",keyspace="{self.session.keyspace}"}} 0')  # Placeholder
        
        except Exception as e:
            self.obs.log_error(f"Failed to get table metrics: {e}")
        
        return lines

    def _get_compaction_metrics(self) -> List[str]:
        lines = []
        
        try:
            # Get compaction metrics (placeholder as Cassandra doesn't expose this easily)
            lines.append(f"# HELP cassandra_compaction_tasks_active Active compaction tasks")
            lines.append(f"# TYPE cassandra_compaction_tasks_active gauge")
            lines.append(f'cassandra_compaction_tasks_active 0')  # Placeholder
            
            lines.append(f"# HELP cassandra_compaction_tasks_pending Pending compaction tasks")
            lines.append(f"# TYPE cassandra_compaction_tasks_pending gauge")
            lines.append(f'cassandra_compaction_tasks_pending 0')  # Placeholder
        
        except Exception as e:
            self.obs.log_error(f"Failed to get compaction metrics: {e}")
        
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
            
            node_health = self._check_node_health()
            if not node_health["healthy"]:
                health_score -= 20
                issues.append("Node health issues detected")
            
            table_health = self._check_table_health()
            if not table_health["healthy"]:
                health_score -= 15
                issues.append("Table health issues detected")
            
            return {
                "healthy": health_score >= 70,
                "health_score": health_score,
                "connectivity": connectivity_result,
                "query_test": query_result,
                "node_health": node_health,
                "table_health": table_health,
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
            query = "SELECT now() as test"
            result = execute_query(self.session, query)
            
            return {
                "success": result.success,
                "execution_time_ms": result.execution_time_ms,
                "error": result.error_message if not result.success else None
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _test_simple_query(self) -> Dict[str, Any]:
        try:
            query = "SELECT cluster_name FROM system.local"
            result = execute_query(self.session, query)
            
            return {
                "success": result.success,
                "execution_time_ms": result.execution_time_ms,
                "cluster_name": result.records[0].get("cluster_name") if result.success and result.records else None,
                "error": result.error_message if not result.success else None
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _check_node_health(self) -> Dict[str, Any]:
        try:
            # Check local node status
            local_query = "SELECT * FROM system.local"
            result = execute_query(self.session, local_query)
            
            if not result.success:
                return {"healthy": False, "error": result.error_message}
            
            # Check peer nodes
            peer_query = "SELECT * FROM system.peers"
            peer_result = execute_query(self.session, peer_query)
            
            peer_count = len(peer_result.records) if peer_result.success else 0
            
            return {
                "healthy": True,
                "local_node_available": True,
                "peer_node_count": peer_count,
                "total_nodes": peer_count + 1
            }
        
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    def _check_table_health(self) -> Dict[str, Any]:
        try:
            # Check table accessibility
            table_query = "SELECT table_name FROM system_schema.tables WHERE keyspace_name = %s"
            result = execute_query(self.session, table_query, {"keyspace_name": self.session.keyspace})
            
            if not result.success:
                return {"healthy": False, "error": result.error_message}
            
            table_count = len(result.records)
            
            # Check a sample table for accessibility
            if table_count > 0:
                sample_table = result.records[0]["table_name"]
                sample_query = f"SELECT COUNT(*) as count FROM {self.session.keyspace}.{sample_table} LIMIT 1"
                sample_result = execute_query(self.session, sample_query)
                
                return {
                    "healthy": sample_result.success,
                    "table_count": table_count,
                    "sample_table_accessible": sample_result.success,
                    "sample_table": sample_table
                }
            
            return {
                "healthy": True,
                "table_count": 0,
                "sample_table_accessible": False,
                "sample_table": None
            }
        
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    def export_json_metrics(self) -> Dict[str, Any]:
        self.obs.log_info("export_json_metrics")
        
        try:
            from .cassandra_query_collector import CassandraQueryCollector
            collector = CassandraQueryCollector(self.session, self.config)
            
            query_metrics = collector.collect_query_metrics(limit=1000)
            
            db_metrics = collector.get_database_metrics()
            
            health = self.get_health_status()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "database": "cassandra",
                "keyspace": self.session.keyspace,
                "query_metrics": MetricsFormatter.format_for_json_export(query_metrics, "cassandra"),
                "database_metrics": db_metrics,
                "health": health
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to export JSON metrics: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "database": "cassandra",
                "keyspace": self.session.keyspace,
                "error": str(e)
            }

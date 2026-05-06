import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extensions import connection as Connection

project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.database.shared.query_monitoring_interfaces import (
    IMetricsExporter, QueryMetric, QueryMonitoringConfig
)
from infrastructure.database.shared.query_monitoring_utils import MetricsFormatter
from infrastructure.observability.scripts.observability_client import ObservabilityClient
from ..client.postgres_client import execute_query


class PostgreSQLMetricsExporter(IMetricsExporter):
    def __init__(self, connection: Connection, config: Optional[QueryMonitoringConfig] = None):
        self.connection = connection
        self.config = config or QueryMonitoringConfig()
        self.obs = ObservabilityClient(service_name="postgres-metrics-exporter")
        self._cached_metrics = {}
        self._cache_timestamp = None
        self._cache_ttl_seconds = 30

    def export_query_metrics(self, metrics: List[QueryMetric]) -> str:
        self.obs.log_info(f"export_query_metrics count={len(metrics)}")
        
        try:
            prometheus_format = MetricsFormatter.format_for_prometheus(metrics, "postgres")
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
            
            prometheus_lines.append(f"# HELP postgres_database_info Database information")
            prometheus_lines.append(f"# TYPE postgres_database_info gauge")
            prometheus_lines.append(f'postgres_database_info{{database="{database}"}} 1')
            
            if 'table_count' in metrics:
                prometheus_lines.append(f"# HELP postgres_tables_total Total number of tables")
                prometheus_lines.append(f"# TYPE postgres_tables_total gauge")
                prometheus_lines.append(f'postgres_tables_total{{database="{database}"}} {metrics["table_count"]}')
            
            if 'index_count' in metrics:
                prometheus_lines.append(f"# HELP postgres_indexes_total Total number of indexes")
                prometheus_lines.append(f"# TYPE postgres_indexes_total gauge")
                prometheus_lines.append(f'postgres_indexes_total{{database="{database}"}} {metrics["index_count"]}')
            
            if 'active_connections' in metrics:
                prometheus_lines.append(f"# HELP postgres_active_connections Current active connections")
                prometheus_lines.append(f"# TYPE postgres_active_connections gauge")
                prometheus_lines.append(f'postgres_active_connections{{database="{database}"}} {metrics["active_connections"]}')
            
            prometheus_lines.append(f"# HELP postgres_export_timestamp_seconds Last export timestamp")
            prometheus_lines.append(f"# TYPE postgres_export_timestamp_seconds gauge")
            prometheus_lines.append(f'postgres_export_timestamp_seconds{{database="{database}"}} {datetime.utcnow().timestamp()}')
            
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
            from .postgres_query_collector import PostgreSQLQueryCollector
            collector = PostgreSQLQueryCollector(self.connection, self.config)
            
            metrics = collector.collect_query_metrics(limit=1000)
            return self.export_query_metrics(metrics)
        
        except Exception as e:
            self.obs.log_error(f"Failed to collect query metrics: {e}")
            return ""

    def _collect_database_status_metrics(self) -> str:
        try:
            from .postgres_query_collector import PostgreSQLQueryCollector
            collector = PostgreSQLQueryCollector(self.connection, self.config)
            
            db_metrics = collector.get_database_metrics()
            
            all_db_metrics = []
            for db_name in ["postgres"]:
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
            
            connection_metrics = self._get_connection_metrics()
            prometheus_lines.extend(connection_metrics)
            
            database_size_metrics = self._get_database_size_metrics()
            prometheus_lines.extend(database_size_metrics)
            
            table_metrics = self._get_table_metrics()
            prometheus_lines.extend(table_metrics)
            
            index_metrics = self._get_index_metrics()
            prometheus_lines.extend(index_metrics)
            
            prometheus_lines.append(f"# HELP postgres_metrics_export_timestamp_seconds Last metrics export timestamp")
            prometheus_lines.append(f"# TYPE postgres_metrics_export_timestamp_seconds gauge")
            prometheus_lines.append(f'postgres_metrics_export_timestamp_seconds {datetime.utcnow().timestamp()}')
            
            return "\n".join(prometheus_lines)
        
        except Exception as e:
            self.obs.log_error(f"Failed to collect server metrics: {e}")
            return ""

    def _get_connection_metrics(self) -> List[str]:
        lines = []
        
        try:
            query = """
            SELECT 
                count(*) as total_connections,
                count(*) FILTER (WHERE state = 'active') as active_connections,
                count(*) FILTER (WHERE state = 'idle') as idle_connections,
                count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction_connections
            FROM pg_stat_activity
            """
            
            result = execute_query(self.connection, query)
            if result.success and result.records:
                record = result.records[0]
                
                lines.append(f"# HELP postgres_connections_total Total number of connections")
                lines.append(f"# TYPE postgres_connections_total gauge")
                lines.append(f'postgres_connections_total {record["total_connections"]}')
                
                lines.append(f"# HELP postgres_connections_active Active connections")
                lines.append(f"# TYPE postgres_connections_active gauge")
                lines.append(f'postgres_connections_active {record["active_connections"]}')
                
                lines.append(f"# HELP postgres_connections_idle Idle connections")
                lines.append(f"# TYPE postgres_connections_idle gauge")
                lines.append(f'postgres_connections_idle {record["idle_connections"]}')
                
                lines.append(f"# HELP postgres_connections_idle_in_transaction Idle in transaction connections")
                lines.append(f"# TYPE postgres_connections_idle_in_transaction gauge")
                lines.append(f'postgres_connections_idle_in_transaction {record["idle_in_transaction_connections"]}')
        
        except Exception as e:
            self.obs.log_error(f"Failed to get connection metrics: {e}")
        
        return lines

    def _get_database_size_metrics(self) -> List[str]:
        lines = []
        
        try:
            query = """
            SELECT 
                pg_database_size(current_database()) as database_size_bytes,
                pg_size_pretty(pg_database_size(current_database())) as database_size_pretty
            """
            
            result = execute_query(self.connection, query)
            if result.success and result.records:
                record = result.records[0]
                
                lines.append(f"# HELP postgres_database_size_bytes Database size in bytes")
                lines.append(f"# TYPE postgres_database_size_bytes gauge")
                lines.append(f'postgres_database_size_bytes {record["database_size_bytes"]}')
        
        except Exception as e:
            self.obs.log_error(f"Failed to get database size metrics: {e}")
        
        return lines

    def _get_table_metrics(self) -> List[str]:
        lines = []
        
        try:
            query = """
            SELECT 
                schemaname,
                tablename,
                seq_scan,
                seq_tup_read,
                idx_scan,
                idx_tup_fetch,
                n_tup_ins,
                n_tup_upd,
                n_tup_del
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            LIMIT 20
            """
            
            result = execute_query(self.connection, query)
            if result.success:
                for record in result.records:
                    table_name = record['tablename']
                    
                    lines.append(f'# HELP postgres_table_seq_scans Sequential scans for table {table_name}')
                    lines.append(f'# TYPE postgres_table_seq_scans counter')
                    lines.append(f'postgres_table_seq_scans{{table="{table_name}"}} {record["seq_scan"]}')
                    
                    lines.append(f'# HELP postgres_table_idx_scans Index scans for table {table_name}')
                    lines.append(f'# TYPE postgres_table_idx_scans counter')
                    lines.append(f'postgres_table_idx_scans{{table="{table_name}"}} {record["idx_scan"]}')
                    
                    lines.append(f'# HELP postgres_table_rows_inserted Rows inserted in table {table_name}')
                    lines.append(f'# TYPE postgres_table_rows_inserted counter')
                    lines.append(f'postgres_table_rows_inserted{{table="{table_name}"}} {record["n_tup_ins"]}')
                    
                    lines.append(f'# HELP postgres_table_rows_updated Rows updated in table {table_name}')
                    lines.append(f'# TYPE postgres_table_rows_updated counter')
                    lines.append(f'postgres_table_rows_updated{{table="{table_name}"}} {record["n_tup_upd"]}')
                    
                    lines.append(f'# HELP postgres_table_rows_deleted Rows deleted in table {table_name}')
                    lines.append(f'# TYPE postgres_table_rows_deleted counter')
                    lines.append(f'postgres_table_rows_deleted{{table="{table_name}"}} {record["n_tup_del"]}')
        
        except Exception as e:
            self.obs.log_error(f"Failed to get table metrics: {e}")
        
        return lines

    def _get_index_metrics(self) -> List[str]:
        lines = []
        
        try:
            query = """
            SELECT 
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            WHERE schemaname = 'public'
            LIMIT 20
            """
            
            result = execute_query(self.connection, query)
            if result.success:
                for record in result.records:
                    index_name = record['indexname']
                    table_name = record['tablename']
                    
                    lines.append(f'# HELP postgres_index_scans Index scans for {index_name}')
                    lines.append(f'# TYPE postgres_index_scans counter')
                    lines.append(f'postgres_index_scans{{index="{index_name}",table="{table_name}"}} {record["idx_scan"]}')
        
        except Exception as e:
            self.obs.log_error(f"Failed to get index metrics: {e}")
        
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
            
            connection_metrics = self._get_connection_health_metrics()
            if connection_metrics.get("connection_usage_percent", 0) > 80:
                health_score -= 20
                issues.append("High connection usage")
            
            long_running_queries = self._get_long_running_queries()
            if len(long_running_queries) > 5:
                health_score -= 15
                issues.append("Multiple long-running queries detected")
            
            return {
                "healthy": health_score >= 70,
                "health_score": health_score,
                "connectivity": connectivity_result,
                "query_test": query_result,
                "connections": connection_metrics,
                "long_running_queries": long_running_queries,
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
            query = "SELECT 1 as test"
            result = execute_query(self.connection, query)
            
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
            query = "SELECT count(*) as table_count FROM information_schema.tables WHERE table_schema = 'public'"
            result = execute_query(self.connection, query)
            
            return {
                "success": result.success,
                "execution_time_ms": result.execution_time_ms,
                "table_count": result.records[0]["table_count"] if result.success and result.records else 0,
                "error": result.error_message if not result.success else None
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _get_connection_health_metrics(self) -> Dict[str, Any]:
        try:
            query = """
            SELECT 
                count(*) as total_connections,
                count(*) FILTER (WHERE state = 'active') as active_connections,
                (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections
            FROM pg_stat_activity
            """
            
            result = execute_query(self.connection, query)
            if result.success and result.records:
                record = result.records[0]
                total = record["total_connections"]
                active = record["active_connections"]
                max_conn = record["max_connections"]
                
                connection_usage_percent = (total / max_conn) * 100 if max_conn > 0 else 0
                
                return {
                    "total_connections": total,
                    "active_connections": active,
                    "max_connections": max_conn,
                    "connection_usage_percent": connection_usage_percent
                }
        
        except:
            pass
        
        return {
            "connection_usage_percent": 0
        }

    def _get_long_running_queries(self) -> List[Dict[str, Any]]:
        try:
            query = """
            SELECT 
                pid,
                query,
                EXTRACT(EPOCH FROM (now() - query_start)) * 1000 as execution_time_ms,
                state
            FROM pg_stat_activity 
            WHERE state = 'active' 
            AND query NOT LIKE '%pg_stat_activity%'
            AND query_start < now() - interval '30 seconds'
            ORDER BY execution_time_ms DESC
            LIMIT 10
            """
            
            result = execute_query(self.connection, query)
            if result.success:
                return result.records
        except:
            pass
        
        return []

    def export_json_metrics(self) -> Dict[str, Any]:
        self.obs.log_info("export_json_metrics")
        
        try:
            from .postgres_query_collector import PostgreSQLQueryCollector
            collector = PostgreSQLQueryCollector(self.connection, self.config)
            
            query_metrics = collector.collect_query_metrics(limit=1000)
            
            db_metrics = collector.get_database_metrics()
            
            connection_metrics = self._get_connection_health_metrics()
            
            health = self.get_health_status()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "database": "postgres",
                "query_metrics": MetricsFormatter.format_for_json_export(query_metrics, "postgres"),
                "database_metrics": db_metrics,
                "connection_metrics": connection_metrics,
                "health": health
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to export JSON metrics: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "database": "postgres",
                "error": str(e)
            }

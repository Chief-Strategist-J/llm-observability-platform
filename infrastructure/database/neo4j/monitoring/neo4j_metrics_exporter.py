import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from neo4j import GraphDatabase, Driver

project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.database.shared.query_monitoring_interfaces import (
    IMetricsExporter, QueryMetric, QueryMonitoringConfig
)
from infrastructure.database.shared.query_monitoring_utils import MetricsFormatter
from infrastructure.observability.scripts.observability_client import ObservabilityClient
from ..client.neo4j_client import execute_query


class Neo4jMetricsExporter(IMetricsExporter):
    def __init__(self, driver: Driver, config: Optional[QueryMonitoringConfig] = None):
        self.driver = driver
        self.config = config or QueryMonitoringConfig()
        self.obs = ObservabilityClient(service_name="neo4j-metrics-exporter")
        self._cached_metrics = {}
        self._cache_timestamp = None
        self._cache_ttl_seconds = 30

    def export_query_metrics(self, metrics: List[QueryMetric]) -> str:
        self.obs.log_info(f"export_query_metrics count={len(metrics)}")
        
        try:
            prometheus_format = MetricsFormatter.format_for_prometheus(metrics, "neo4j")
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
            
            prometheus_lines.append(f"# HELP neo4j_database_info Database information")
            prometheus_lines.append(f"# TYPE neo4j_database_info gauge")
            prometheus_lines.append(f'neo4j_database_info{{database="{database}"}} 1')
            
            if 'node_count' in metrics:
                prometheus_lines.append(f"# HELP neo4j_nodes_total Total number of nodes")
                prometheus_lines.append(f"# TYPE neo4j_nodes_total gauge")
                prometheus_lines.append(f'neo4j_nodes_total{{database="{database}"}} {metrics["node_count"]}')
            
            if 'relationship_count' in metrics:
                prometheus_lines.append(f"# HELP neo4j_relationships_total Total number of relationships")
                prometheus_lines.append(f"# TYPE neo4j_relationships_total gauge")
                prometheus_lines.append(f'neo4j_relationships_total{{database="{database}"}} {metrics["relationship_count"]}')
            
            if 'label_count' in metrics:
                prometheus_lines.append(f"# HELP neo4j_labels_total Total number of labels")
                prometheus_lines.append(f"# TYPE neo4j_labels_total gauge")
                prometheus_lines.append(f'neo4j_labels_total{{database="{database}"}} {metrics["label_count"]}')
            
            if 'relationship_type_count' in metrics:
                prometheus_lines.append(f"# HELP neo4j_relationship_types_total Total number of relationship types")
                prometheus_lines.append(f"# TYPE neo4j_relationship_types_total gauge")
                prometheus_lines.append(f'neo4j_relationship_types_total{{database="{database}"}} {metrics["relationship_type_count"]}')
            
            if 'index_count' in metrics:
                prometheus_lines.append(f"# HELP neo4j_indexes_total Total number of indexes")
                prometheus_lines.append(f"# TYPE neo4j_indexes_total gauge")
                prometheus_lines.append(f'neo4j_indexes_total{{database="{database}"}} {metrics["index_count"]}')
            
            prometheus_lines.append(f"# HELP neo4j_export_timestamp_seconds Last export timestamp")
            prometheus_lines.append(f"# TYPE neo4j_export_timestamp_seconds gauge")
            prometheus_lines.append(f'neo4j_export_timestamp_seconds{{database="{database}"}} {datetime.utcnow().timestamp()}')
            
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
            from .neo4j_query_collector import Neo4jQueryCollector
            collector = Neo4jQueryCollector(self.driver, self.config)
            
            metrics = collector.collect_query_metrics(limit=1000)
            return self.export_query_metrics(metrics)
        
        except Exception as e:
            self.obs.log_error(f"Failed to collect query metrics: {e}")
            return ""

    def _collect_database_status_metrics(self) -> str:
        try:
            from .neo4j_query_collector import Neo4jQueryCollector
            collector = Neo4jQueryCollector(self.driver, self.config)
            
            db_metrics = collector.get_database_metrics()
            
            all_db_metrics = []
            for db_name in ["neo4j"]:
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
            
            jmx_queries = [
                "CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Kernel') YIELD attributes RETURN attributes",
                "CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Store') YIELD attributes RETURN attributes",
                "CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Memory Pools') YIELD attributes RETURN attributes"
            ]
            
            for query in jmx_queries:
                result = execute_query(self.driver, query)
                if result.success and result.records:
                    attributes = result.records[0].get("attributes", {})
                    prometheus_lines.extend(self._parse_jmx_attributes(attributes))
            
            active_queries = self._get_active_queries_metrics()
            prometheus_lines.extend(active_queries)
            
            prometheus_lines.append(f"# HELP neo4j_metrics_export_timestamp_seconds Last metrics export timestamp")
            prometheus_lines.append(f"# TYPE neo4j_metrics_export_timestamp_seconds gauge")
            prometheus_lines.append(f'neo4j_metrics_export_timestamp_seconds {datetime.utcnow().timestamp()}')
            
            return "\n".join(prometheus_lines)
        
        except Exception as e:
            self.obs.log_error(f"Failed to collect server metrics: {e}")
            return ""

    def _parse_jmx_attributes(self, attributes: Dict[str, Any]) -> List[str]:
        lines = []
        
        kernel_metrics = [
            ("KernelDatabaseSize", "neo4j_kernel_database_size_bytes"),
            ("TransactionCount", "neo4j_transaction_count_total"),
            ("LastCommittedTxId", "neo4j_last_committed_tx_id"),
            ("NumberOfOpenTransactions", "neo4j_transactions_open"),
        ]
        
        for attr_name, metric_name in kernel_metrics:
            if attr_name in attributes:
                value = attributes[attr_name]
                if isinstance(value, (int, float)):
                    lines.append(f"# HELP {metric_name} Neo4j kernel metric")
                    lines.append(f"# TYPE {metric_name} gauge")
                    lines.append(f'{metric_name} {value}')
        
        store_metrics = [
            ("SizeTotal", "neo4j_store_size_bytes"),
            ("SizeFile", "neo4j_store_file_size_bytes"),
        ]
        
        for attr_name, metric_name in store_metrics:
            if attr_name in attributes:
                value = attributes[attr_name]
                if isinstance(value, (int, float)):
                    lines.append(f"# HELP {metric_name} Neo4j store metric")
                    lines.append(f"# TYPE {metric_name} gauge")
                    lines.append(f'{metric_name} {value}')
        
        return lines

    def _get_active_queries_metrics(self) -> List[str]:
        lines = []
        
        try:
            query = "CALL dbms.listQueries() YIELD queryId, query, metaData, runtime RETURN count(queryId) as active_queries"
            result = execute_query(self.driver, query)
            
            if result.success and result.records:
                active_count = result.records[0]["active_queries"]
                
                lines.append(f"# HELP neo4j_active_queries Current number of active queries")
                lines.append(f"# TYPE neo4j_active_queries gauge")
                lines.append(f'neo4j_active_queries {active_count}')
        
        except Exception as e:
            self.obs.log_error(f"Failed to get active queries metrics: {e}")
        
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
            
            active_queries = self._get_active_query_count()
            if active_queries > 100:
                health_score -= 20
                issues.append("High number of active queries")
            
            memory_metrics = self._get_memory_metrics()
            if memory_metrics.get("memory_usage_percent", 0) > 80:
                health_score -= 25
                issues.append("High memory usage")
            
            return {
                "healthy": health_score >= 70,
                "health_score": health_score,
                "connectivity": connectivity_result,
                "query_test": query_result,
                "active_queries": active_queries,
                "memory": memory_metrics,
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
            query = "RETURN 1 as test"
            result = execute_query(self.driver, query)
            
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
            query = "MATCH (n) RETURN count(n) as node_count LIMIT 1"
            result = execute_query(self.driver, query)
            
            return {
                "success": result.success,
                "execution_time_ms": result.execution_time_ms,
                "node_count": result.records[0]["node_count"] if result.success and result.records else 0,
                "error": result.error_message if not result.success else None
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _get_active_query_count(self) -> int:
        try:
            query = "CALL dbms.listQueries() YIELD queryId RETURN count(queryId) as count"
            result = execute_query(self.driver, query)
            
            if result.success and result.records:
                return result.records[0]["count"]
            return 0
        
        except:
            return 0

    def _get_memory_metrics(self) -> Dict[str, Any]:
        try:
            query = "CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Memory Pools') YIELD attributes RETURN attributes"
            result = execute_query(self.driver, query)
            
            if result.success and result.records:
                attributes = result.records[0].get("attributes", {})
                
                total_memory = attributes.get("TotalMemory", 0)
                free_memory = attributes.get("FreeMemory", 0)
                
                if total_memory > 0:
                    memory_usage_percent = ((total_memory - free_memory) / total_memory) * 100
                else:
                    memory_usage_percent = 0
                
                return {
                    "total_memory_bytes": total_memory,
                    "free_memory_bytes": free_memory,
                    "used_memory_bytes": total_memory - free_memory,
                    "memory_usage_percent": memory_usage_percent
                }
        
        except:
            pass
        
        return {
            "memory_usage_percent": 0
        }

    def export_json_metrics(self) -> Dict[str, Any]:
        self.obs.log_info("export_json_metrics")
        
        try:
            from .neo4j_query_collector import Neo4jQueryCollector
            collector = Neo4jQueryCollector(self.driver, self.config)
            
            query_metrics = collector.collect_query_metrics(limit=1000)
            
            db_metrics = collector.get_database_metrics()
            
            jmx_metrics = self._collect_jmx_metrics()
            
            health = self.get_health_status()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "database": "neo4j",
                "query_metrics": MetricsFormatter.format_for_json_export(query_metrics, "neo4j"),
                "database_metrics": db_metrics,
                "jmx_metrics": jmx_metrics,
                "health": health
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to export JSON metrics: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "database": "neo4j",
                "error": str(e)
            }

    def _collect_jmx_metrics(self) -> Dict[str, Any]:
        try:
            jmx_queries = [
                ("kernel", "CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Kernel') YIELD attributes RETURN attributes"),
                ("store", "CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Store') YIELD attributes RETURN attributes"),
                ("memory", "CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Memory Pools') YIELD attributes RETURN attributes")
            ]
            
            metrics = {}
            for name, query in jmx_queries:
                result = execute_query(self.driver, query)
                if result.success and result.records:
                    attributes = result.records[0].get("attributes", {})
                    metrics[name] = attributes
            
            return metrics
        
        except Exception as e:
            self.obs.log_error(f"Failed to collect JMX metrics: {e}")
            return {}

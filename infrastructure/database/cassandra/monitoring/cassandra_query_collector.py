import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from cassandra.cluster import Session

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
from ..client.cassandra_client import execute_query, get_session, CassandraConnectionConfig


class CassandraQueryCollector(IQueryPerformanceCollector):
    def __init__(self, session: Session, config: Optional[QueryMonitoringConfig] = None):
        self.session = session
        self.config = config or QueryMonitoringConfig()
        self.obs = ObservabilityClient(service_name="cassandra-query-collector")
        self._query_metrics_store = []
        self._max_store_size = self.config.max_query_history_size

    def collect_query_metrics(self, limit: int = 1000) -> List[QueryMetric]:
        self.obs.log_info(f"collect_query_metrics limit={limit}")
        
        metrics = []
        
        try:
            system_metrics = self._get_system_metrics()
            metrics.extend(system_metrics)
            
            table_metrics = self._get_table_metrics()
            metrics.extend(table_metrics)
            
            slow_query_metrics = self._get_slow_query_metrics()
            metrics.extend(slow_query_metrics)
            
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

    def _get_system_metrics(self) -> List[QueryMetric]:
        metrics = []
        
        try:
            # Get system table metrics
            system_queries = [
                "SELECT * FROM system.local",
                "SELECT * FROM system.peers",
                "SELECT * FROM system.schema_keyspaces"
            ]
            
            for query in system_queries:
                try:
                    result = execute_query(self.session, query)
                    if result.success:
                        metric = self._convert_system_query_to_metric(query, result)
                        if metric:
                            metrics.append(metric)
                except Exception as e:
                    self.obs.log_error(f"Failed to collect system metric for query {query}: {e}")
        
        except Exception as e:
            self.obs.log_error(f"Failed to get system metrics: {e}")
        
        return metrics

    def _get_table_metrics(self) -> List[QueryMetric]:
        metrics = []
        
        try:
            # Get table statistics
            tables_query = "SELECT table_name FROM system_schema.tables WHERE keyspace_name = %s"
            result = execute_query(self.session, tables_query, {"keyspace_name": self.session.keyspace})
            
            if result.success:
                for record in result.records:
                    table_name = record["table_name"]
                    
                    # Get table-specific metrics
                    table_query = f"SELECT * FROM {self.session.keyspace}.{table_name} LIMIT 1"
                    try:
                        table_result = execute_query(self.session, table_query)
                        if table_result.success:
                            metric = self._convert_table_query_to_metric(table_name, table_result)
                            if metric:
                                metrics.append(metric)
                    except Exception:
                        pass  # Skip tables that can't be accessed
        
        except Exception as e:
            self.obs.log_error(f"Failed to get table metrics: {e}")
        
        return metrics

    def _get_slow_query_metrics(self) -> List[QueryMetric]:
        metrics = []
        
        try:
            # Simulate slow query detection based on table scans
            tables_query = "SELECT table_name FROM system_schema.tables WHERE keyspace_name = %s"
            result = execute_query(self.session, tables_query, {"keyspace_name": self.session.keyspace})
            
            if result.success:
                for record in result.records:
                    table_name = record["table_name"]
                    
                    # Create simulated slow query metric
                    metric = QueryMetric(
                        query_hash=QueryHashGenerator.generate_hash(f"SELECT * FROM {table_name}"),
                        query_type="select",
                        database="cassandra",
                        collection_table=table_name,
                        execution_time_ms=self.config.slow_query_threshold_ms + 500,
                        status=QueryStatus.SUCCESS,
                        performance_level=QueryPerformanceLevel.SLOW,
                        timestamp=datetime.utcnow(),
                        affected_rows=0
                    )
                    metrics.append(metric)
        
        except Exception as e:
            self.obs.log_error(f"Failed to get slow query metrics: {e}")
        
        return metrics

    def _convert_system_query_to_metric(self, query: str, result) -> Optional[QueryMetric]:
        try:
            query_hash = QueryHashGenerator.generate_hash(query)
            
            performance_level = PerformanceClassifier.classify_performance(
                result.execution_time_ms,
                PerformanceClassifier.get_default_thresholds()
            )
            
            return QueryMetric(
                query_hash=query_hash,
                query_type=self._extract_query_type(query),
                database="cassandra",
                collection_table="system",
                execution_time_ms=result.execution_time_ms,
                status=QueryStatus.SUCCESS if result.success else QueryStatus.ERROR,
                performance_level=performance_level,
                timestamp=datetime.utcnow(),
                affected_rows=len(result.records)
            )
        
        except Exception as e:
            self.obs.log_error(f"Failed to convert system query to metric: {e}")
            return None

    def _convert_table_query_to_metric(self, table_name: str, result) -> Optional[QueryMetric]:
        try:
            query = f"SELECT * FROM {self.session.keyspace}.{table_name} LIMIT 1"
            query_hash = QueryHashGenerator.generate_hash(query)
            
            performance_level = PerformanceClassifier.classify_performance(
                result.execution_time_ms,
                PerformanceClassifier.get_default_thresholds()
            )
            
            return QueryMetric(
                query_hash=query_hash,
                query_type="select",
                database="cassandra",
                collection_table=table_name,
                execution_time_ms=result.execution_time_ms,
                status=QueryStatus.SUCCESS if result.success else QueryStatus.ERROR,
                performance_level=performance_level,
                timestamp=datetime.utcnow(),
                affected_rows=len(result.records)
            )
        
        except Exception as e:
            self.obs.log_error(f"Failed to convert table query to metric: {e}")
            return None

    def _extract_query_type(self, query: str) -> str:
        query_upper = query.strip().upper()
        
        if query_upper.startswith("SELECT"):
            return "select"
        elif query_upper.startswith("INSERT"):
            return "insert"
        elif query_upper.startswith("UPDATE"):
            return "update"
        elif query_upper.startswith("DELETE"):
            return "delete"
        elif query_upper.startswith("CREATE"):
            return "create"
        elif query_upper.startswith("DROP"):
            return "drop"
        elif query_upper.startswith("ALTER"):
            return "alter"
        else:
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
            
            table_analysis = {}
            for metric in slow_queries:
                table = metric.collection_table
                if table:
                    if table not in table_analysis:
                        table_analysis[table] = {
                            'slow_queries': [],
                            'avg_execution_time': 0
                        }
                    
                    table_analysis[table]['slow_queries'].append(metric)
            
            for table, analysis in table_analysis.items():
                if len(analysis['slow_queries']) > 5:
                    avg_time = sum(q.execution_time_ms for q in analysis['slow_queries']) / len(analysis['slow_queries'])
                    
                    gaps.append({
                        'table': table,
                        'slow_query_count': len(analysis['slow_queries']),
                        'avg_execution_time': avg_time,
                        'recommendation': f"Consider optimizing table '{table}' or adding appropriate indexes"
                    })
        
        except Exception as e:
            self.obs.log_error(f"Failed to identify index gaps: {e}")
        
        return gaps

    def get_database_metrics(self) -> Dict[str, Any]:
        self.obs.log_info("get_database_metrics")
        
        try:
            metrics = {}
            
            # Get cluster info
            cluster_query = "SELECT cluster_name FROM system.local"
            result = execute_query(self.session, cluster_query)
            if result.success and result.records:
                metrics["cluster_name"] = result.records[0].get("cluster_name")
            
            # Get keyspace info
            keyspace_query = f"SELECT * FROM system_schema.keyspaces WHERE keyspace_name = '{self.session.keyspace}'"
            result = execute_query(self.session, keyspace_query)
            if result.success and result.records:
                metrics["keyspace_info"] = result.records[0]
            
            # Get table count
            table_query = "SELECT COUNT(*) as table_count FROM system_schema.tables WHERE keyspace_name = %s"
            result = execute_query(self.session, table_query, {"keyspace_name": self.session.keyspace})
            if result.success and result.records:
                metrics["table_count"] = result.records[0].get("table_count")
            
            # Get node count
            node_query = "SELECT COUNT(*) as node_count FROM system.peers"
            result = execute_query(self.session, node_query)
            if result.success and result.records:
                metrics["node_count"] = result.records[0].get("node_count") + 1  # +1 for local node
            
            return metrics
        
        except Exception as e:
            self.obs.log_error(f"Failed to get database metrics: {e}")
            return {}

    def get_table_statistics(self, table_name: str) -> Dict[str, Any]:
        self.obs.log_info(f"get_table_statistics table={table_name}")
        
        try:
            stats = {}
            
            # Get table info
            table_query = "SELECT * FROM system_schema.tables WHERE keyspace_name = %s AND table_name = %s"
            result = execute_query(self.session, table_query, {
                "keyspace_name": self.session.keyspace,
                "table_name": table_name
            })
            if result.success and result.records:
                stats["table_info"] = result.records[0]
            
            # Get column info
            column_query = "SELECT * FROM system_schema.columns WHERE keyspace_name = %s AND table_name = %s"
            result = execute_query(self.session, column_query, {
                "keyspace_name": self.session.keyspace,
                "table_name": table_name
            })
            if result.success:
                stats["columns"] = result.records
            
            # Get index info
            index_query = "SELECT * FROM system_schema.indexes WHERE keyspace_name = %s AND table_name = %s"
            result = execute_query(self.session, index_query, {
                "keyspace_name": self.session.keyspace,
                "table_name": table_name
            })
            if result.success:
                stats["indexes"] = result.records
            
            return stats
        
        except Exception as e:
            self.obs.log_error(f"Failed to get table statistics: {e}")
            return {}

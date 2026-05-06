import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extensions import connection as Connection

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
from ..client.postgres_client import get_connection, PostgreSQLConnectionConfig, execute_query


class PostgreSQLQueryCollector(IQueryPerformanceCollector):
    def __init__(self, connection: Connection, config: Optional[QueryMonitoringConfig] = None):
        self.connection = connection
        self.config = config or QueryMonitoringConfig()
        self.obs = ObservabilityClient(service_name="postgres-query-collector")
        self._query_metrics_store = []
        self._max_store_size = self.config.max_query_history_size

    def collect_query_metrics(self, limit: int = 1000) -> List[QueryMetric]:
        self.obs.log_info(f"collect_query_metrics limit={limit}")
        
        metrics = []
        
        try:
            pg_stat_metrics = self._get_pg_stat_statements()
            metrics.extend(pg_stat_metrics)
            
            pg_activity_metrics = self._get_pg_activity_metrics()
            metrics.extend(pg_activity_metrics)
            
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

    def _get_pg_stat_statements(self) -> List[QueryMetric]:
        metrics = []
        
        try:
            query = """
            SELECT query, calls, total_time, mean_time, rows, 
                   100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
            FROM pg_stat_statements 
            ORDER BY total_time DESC 
            LIMIT 100
            """
            
            result = execute_query(self.connection, query)
            
            if result.success:
                for record in result.records:
                    metric = self._convert_pg_stat_to_metric(record)
                    if metric:
                        metrics.append(metric)
        
        except Exception as e:
            self.obs.log_error(f"Failed to get pg_stat_statements: {e}")
        
        return metrics

    def _get_pg_activity_metrics(self) -> List[QueryMetric]:
        metrics = []
        
        try:
            query = """
            SELECT query, state, backend_start, xact_start, query_start, state_change,
                   EXTRACT(EPOCH FROM (now() - query_start)) * 1000 as execution_time_ms
            FROM pg_stat_activity 
            WHERE state = 'active' AND query NOT LIKE '%pg_stat_activity%'
            ORDER BY execution_time_ms DESC
            LIMIT 50
            """
            
            result = execute_query(self.connection, query)
            
            if result.success:
                for record in result.records:
                    metric = self._convert_pg_activity_to_metric(record)
                    if metric:
                        metrics.append(metric)
        
        except Exception as e:
            self.obs.log_error(f"Failed to get pg_activity_metrics: {e}")
        
        return metrics

    def _get_slow_query_metrics(self) -> List[QueryMetric]:
        metrics = []
        
        try:
            query = """
            SELECT query, calls, total_time, mean_time, rows
            FROM pg_stat_statements 
            WHERE mean_time > %s
            ORDER BY mean_time DESC 
            LIMIT 50
            """
            
            threshold_ms = self.config.slow_query_threshold_ms
            result = execute_query(self.connection, query, (threshold_ms,))
            
            if result.success:
                for record in result.records:
                    metric = self._convert_pg_stat_to_metric(record)
                    if metric:
                        metrics.append(metric)
        
        except Exception as e:
            self.obs.log_error(f"Failed to get slow_query_metrics: {e}")
        
        return metrics

    def _convert_pg_stat_to_metric(self, record: Dict[str, Any]) -> Optional[QueryMetric]:
        try:
            query_text = record.get("query", "")
            if not query_text or query_text.startswith("<"):
                return None
            
            query_hash = QueryHashGenerator.generate_hash(query_text)
            
            mean_time_ms = float(record.get("mean_time", 0))
            performance_level = PerformanceClassifier.classify_performance(
                mean_time_ms,
                PerformanceClassifier.get_default_thresholds()
            )
            
            table_name = self._extract_table_from_query(query_text)
            
            return QueryMetric(
                query_hash=query_hash,
                query_type=self._extract_query_type(query_text),
                database="postgres",
                collection_table=table_name,
                execution_time_ms=mean_time_ms,
                status=QueryStatus.SUCCESS,
                performance_level=performance_level,
                timestamp=datetime.utcnow(),
                affected_rows=record.get("rows", 0),
                plan_details=None
            )
        
        except Exception as e:
            self.obs.log_error(f"Failed to convert pg_stat to metric: {e}")
            return None

    def _convert_pg_activity_to_metric(self, record: Dict[str, Any]) -> Optional[QueryMetric]:
        try:
            query_text = record.get("query", "")
            if not query_text:
                return None
            
            query_hash = QueryHashGenerator.generate_hash(query_text)
            
            execution_time_ms = float(record.get("execution_time_ms", 0))
            performance_level = PerformanceClassifier.classify_performance(
                execution_time_ms,
                PerformanceClassifier.get_default_thresholds()
            )
            
            table_name = self._extract_table_from_query(query_text)
            
            return QueryMetric(
                query_hash=query_hash,
                query_type=self._extract_query_type(query_text),
                database="postgres",
                collection_table=table_name,
                execution_time_ms=execution_time_ms,
                status=QueryStatus.SUCCESS,
                performance_level=performance_level,
                timestamp=datetime.utcnow(),
                plan_details=None
            )
        
        except Exception as e:
            self.obs.log_error(f"Failed to convert pg_activity to metric: {e}")
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
        elif query_upper.startswith("WITH"):
            return "with"
        else:
            return "unknown"

    def _extract_table_from_query(self, query: str) -> Optional[str]:
        try:
            import re
            patterns = [
                r'FROM\s+(\w+)',
                r'INTO\s+(\w+)',
                r'UPDATE\s+(\w+)',
                r'TABLE\s+(\w+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    return match.group(1)
        except:
            pass
        return None

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
                        'recommendation': f"Consider adding indexes to table '{table}' to improve query performance"
                    })
        
        except Exception as e:
            self.obs.log_error(f"Failed to identify index gaps: {e}")
        
        return gaps

    def get_database_metrics(self) -> Dict[str, Any]:
        self.obs.log_info("get_database_metrics")
        
        try:
            metrics = {}
            
            table_count_query = "SELECT count(*) as table_count FROM information_schema.tables WHERE table_schema = 'public'"
            result = execute_query(self.connection, table_count_query)
            if result.success and result.records:
                metrics['table_count'] = result.records[0]['table_count']
            
            index_count_query = "SELECT count(*) as index_count FROM pg_indexes WHERE schemaname = 'public'"
            result = execute_query(self.connection, index_count_query)
            if result.success and result.records:
                metrics['index_count'] = result.records[0]['index_count']
            
            size_query = "SELECT pg_size_pretty(pg_database_size(current_database())) as database_size"
            result = execute_query(self.connection, size_query)
            if result.success and result.records:
                metrics['database_size'] = result.records[0]['database_size']
            
            connection_query = "SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active'"
            result = execute_query(self.connection, connection_query)
            if result.success and result.records:
                metrics['active_connections'] = result.records[0]['active_connections']
            
            return metrics
        
        except Exception as e:
            self.obs.log_error(f"Failed to get database metrics: {e}")
            return {}

    def get_table_statistics(self, table_name: str) -> Dict[str, Any]:
        self.obs.log_info(f"get_table_statistics table={table_name}")
        
        try:
            stats = {}
            
            row_count_query = f"SELECT count(*) as row_count FROM {table_name}"
            result = execute_query(self.connection, row_count_query)
            if result.success and result.records:
                stats['row_count'] = result.records[0]['row_count']
            
            table_stats_query = """
            SELECT schemaname, tablename, seq_scan, seq_tup_read, idx_scan, idx_tup_fetch,
                   n_tup_ins, n_tup_upd, n_tup_del
            FROM pg_stat_user_tables 
            WHERE tablename = %s
            """
            result = execute_query(self.connection, table_stats_query, (table_name,))
            if result.success and result.records:
                stats.update(result.records[0])
            
            index_stats_query = """
            SELECT indexname, idx_scan, idx_tup_read, idx_tup_fetch
            FROM pg_stat_user_indexes 
            WHERE tablename = %s
            """
            result = execute_query(self.connection, index_stats_query, (table_name,))
            if result.success:
                stats['indexes'] = result.records
            
            return stats
        
        except Exception as e:
            self.obs.log_error(f"Failed to get table statistics: {e}")
            return {}

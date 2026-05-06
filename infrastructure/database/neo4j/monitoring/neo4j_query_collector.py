import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from neo4j import GraphDatabase, Driver

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
from ..client.neo4j_client import get_driver, Neo4jConnectionConfig, execute_query


class Neo4jQueryCollector(IQueryPerformanceCollector):
    def __init__(self, driver: Driver, config: Optional[QueryMonitoringConfig] = None):
        self.driver = driver
        self.config = config or QueryMonitoringConfig()
        self.obs = ObservabilityClient(service_name="neo4j-query-collector")
        self._query_metrics_store = []
        self._max_store_size = self.config.max_query_history_size

    def collect_query_metrics(self, limit: int = 1000) -> List[QueryMetric]:
        self.obs.log_info(f"collect_query_metrics limit={limit}")
        
        metrics = []
        
        try:
            current_queries = self._get_current_queries()
            metrics.extend(current_queries)
            
            query_log = self._get_query_log()
            metrics.extend(query_log)
            
            profile_metrics = self._get_profile_metrics()
            metrics.extend(profile_metrics)
            
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

    def _get_current_queries(self) -> List[QueryMetric]:
        metrics = []
        
        try:
            query = "CALL dbms.listQueries() YIELD queryId, query, metaData, runtime, allocatedBytes, hitCount, faultCount RETURN queryId, query, metaData, runtime, allocatedBytes, hitCount, faultCount"
            
            result = execute_query(self.driver, query)
            
            if result.success:
                for record in result.records:
                    metric = self._convert_active_query_to_metric(record)
                    if metric:
                        metrics.append(metric)
        
        except Exception as e:
            self.obs.log_error(f"Failed to get current queries: {e}")
        
        return metrics

    def _get_query_log(self) -> List[QueryMetric]:
        metrics = []
        
        try:
            query = "CALL dbms.log.list() YIELD level, message, timestamp RETURN level, message, timestamp ORDER BY timestamp DESC LIMIT 100"
            
            result = execute_query(self.driver, query)
            
            if result.success:
                for record in result.records:
                    if "query" in record.get("message", "").lower():
                        metric = self._convert_log_entry_to_metric(record)
                        if metric:
                            metrics.append(metric)
        
        except Exception as e:
            self.obs.log_error(f"Failed to get query log: {e}")
        
        return metrics

    def _get_profile_metrics(self) -> List[QueryMetric]:
        metrics = []
        
        try:
            test_queries = [
                "MATCH (n) RETURN count(n) LIMIT 1",
                "MATCH ()-[r]->() RETURN count(r) LIMIT 1",
                "CALL db.labels() YIELD label RETURN count(label)"
            ]
            
            for test_query in test_queries:
                try:
                    profile_result = self._profile_query(test_query)
                    if profile_result:
                        metrics.append(profile_result)
                except:
                    continue
        
        except Exception as e:
            self.obs.log_error(f"Failed to get profile metrics: {e}")
        
        return metrics

    def _convert_active_query_to_metric(self, record: Dict[str, Any]) -> Optional[QueryMetric]:
        try:
            query_text = record.get("query", "")
            if not query_text:
                return None
            
            query_hash = QueryHashGenerator.generate_hash(query_text)
            
            runtime = record.get("runtime", 0)
            execution_time_ms = float(runtime) if runtime else 0.0
            
            performance_level = PerformanceClassifier.classify_performance(
                execution_time_ms,
                PerformanceClassifier.get_default_thresholds()
            )
            
            meta_data = record.get("metaData", {})
            database = meta_data.get("database", "neo4j")
            
            return QueryMetric(
                query_hash=query_hash,
                query_type=self._extract_query_type(query_text),
                database=database,
                collection_table=None,
                execution_time_ms=execution_time_ms,
                status=QueryStatus.SUCCESS,
                performance_level=performance_level,
                timestamp=datetime.utcnow(),
                memory_usage_mb=self._bytes_to_mb(record.get("allocatedBytes", 0)),
                plan_details=None
            )
        
        except Exception as e:
            self.obs.log_error(f"Failed to convert active query to metric: {e}")
            return None

    def _convert_log_entry_to_metric(self, record: Dict[str, Any]) -> Optional[QueryMetric]:
        try:
            message = record.get("message", "")
            timestamp = record.get("timestamp")
            
            if not message or not timestamp:
                return None
            
            query_text = self._extract_query_from_log(message)
            if not query_text:
                return None
            
            query_hash = QueryHashGenerator.generate_hash(query_text)
            
            execution_time_ms = self._extract_execution_time_from_log(message)
            performance_level = PerformanceClassifier.classify_performance(
                execution_time_ms,
                PerformanceClassifier.get_default_thresholds()
            )
            
            return QueryMetric(
                query_hash=query_hash,
                query_type=self._extract_query_type(query_text),
                database="neo4j",
                collection_table=None,
                execution_time_ms=execution_time_ms,
                status=QueryStatus.SUCCESS,
                performance_level=performance_level,
                timestamp=timestamp,
                plan_details=None
            )
        
        except Exception as e:
            self.obs.log_error(f"Failed to convert log entry to metric: {e}")
            return None

    def _profile_query(self, query: str) -> Optional[QueryMetric]:
        try:
            profile_query = f"PROFILE {query}"
            result = execute_query(self.driver, profile_query)
            
            if result.success and result.records:
                profile_data = result.records[0].get("profile", {})
                
                query_hash = QueryHashGenerator.generate_hash(query)
                
                performance_level = PerformanceClassifier.classify_performance(
                    result.execution_time_ms,
                    PerformanceClassifier.get_default_thresholds()
                )
                
                return QueryMetric(
                    query_hash=query_hash,
                    query_type=self._extract_query_type(query),
                    database="neo4j",
                    collection_table=None,
                    execution_time_ms=result.execution_time_ms,
                    status=QueryStatus.SUCCESS,
                    performance_level=performance_level,
                    timestamp=datetime.utcnow(),
                    affected_rows=profile_data.get("rows", 0),
                    plan_details=profile_data,
                    memory_usage_mb=self._bytes_to_mb(profile_data.get("memory", 0))
                )
        
        except Exception as e:
            self.obs.log_error(f"Failed to profile query: {e}")
        
        return None

    def _extract_query_type(self, query: str) -> str:
        query_upper = query.strip().upper()
        
        if query_upper.startswith("MATCH"):
            return "match"
        elif query_upper.startswith("CREATE"):
            return "create"
        elif query_upper.startswith("MERGE"):
            return "merge"
        elif query_upper.startswith("DELETE"):
            return "delete"
        elif query_upper.startswith("SET"):
            return "set"
        elif query_upper.startswith("REMOVE"):
            return "remove"
        elif query_upper.startswith("CALL"):
            return "call"
        elif query_upper.startswith("WITH"):
            return "with"
        elif query_upper.startswith("UNWIND"):
            return "unwind"
        else:
            return "unknown"

    def _extract_query_from_log(self, message: str) -> Optional[str]:
        try:
            if "query:" in message.lower():
                start = message.lower().find("query:")
                if start != -1:
                    query_part = message[start + 6:].strip()
                    if query_part.startswith('"') and query_part.endswith('"'):
                        return query_part[1:-1]
                    return query_part
        except:
            pass
        return None

    def _extract_execution_time_from_log(self, message: str) -> float:
        try:
            import re
            time_match = re.search(r'(\d+(?:\.\d+)?)\s*ms', message)
            if time_match:
                return float(time_match.group(1))
        except:
            pass
        return 0.0

    def _bytes_to_mb(self, bytes_value: int) -> float:
        return bytes_value / (1024 * 1024) if bytes_value else 0.0

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
            
            label_analysis = {}
            for metric in slow_queries:
                query_type = metric.query_type
                if query_type not in label_analysis:
                    label_analysis[query_type] = {
                        'slow_queries': [],
                        'avg_execution_time': 0
                    }
                
                label_analysis[query_type]['slow_queries'].append(metric)
            
            for query_type, analysis in label_analysis.items():
                if len(analysis['slow_queries']) > 5:
                    avg_time = sum(q.execution_time_ms for q in analysis['slow_queries']) / len(analysis['slow_queries'])
                    
                    gaps.append({
                        'query_type': query_type,
                        'slow_query_count': len(analysis['slow_queries']),
                        'avg_execution_time': avg_time,
                        'recommendation': f"Consider optimizing {query_type} queries or adding appropriate indexes"
                    })
        
        except Exception as e:
            self.obs.log_error(f"Failed to identify index gaps: {e}")
        
        return gaps

    def get_database_metrics(self) -> Dict[str, Any]:
        self.obs.log_info("get_database_metrics")
        
        try:
            metrics = {}
            
            node_count_query = "MATCH (n) RETURN count(n) as node_count"
            result = execute_query(self.driver, node_count_query)
            if result.success and result.records:
                metrics['node_count'] = result.records[0]['node_count']
            
            relationship_count_query = "MATCH ()-[r]->() RETURN count(r) as relationship_count"
            result = execute_query(self.driver, relationship_count_query)
            if result.success and result.records:
                metrics['relationship_count'] = result.records[0]['relationship_count']
            
            label_query = "CALL db.labels() YIELD label RETURN count(label) as label_count"
            result = execute_query(self.driver, label_query)
            if result.success and result.records:
                metrics['label_count'] = result.records[0]['label_count']
            
            relationship_type_query = "CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) as type_count"
            result = execute_query(self.driver, relationship_type_query)
            if result.success and result.records:
                metrics['relationship_type_count'] = result.records[0]['type_count']
            
            index_query = "CALL db.indexes() YIELD name RETURN count(name) as index_count"
            result = execute_query(self.driver, index_query)
            if result.success and result.records:
                metrics['index_count'] = result.records[0]['index_count']
            
            return metrics
        
        except Exception as e:
            self.obs.log_error(f"Failed to get database metrics: {e}")
            return {}

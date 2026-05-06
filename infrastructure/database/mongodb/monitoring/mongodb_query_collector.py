import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

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


class MongoDBQueryCollector(IQueryPerformanceCollector):
    def __init__(self, client: MongoClient, config: Optional[QueryMonitoringConfig] = None):
        self.client = client
        self.config = config or QueryMonitoringConfig()
        self.obs = ObservabilityClient(service_name="mongodb-query-collector")
        self._query_metrics_store = []
        self._max_store_size = self.config.max_query_history_size

    def collect_query_metrics(self, limit: int = 1000) -> List[QueryMetric]:
        self.obs.log_info(f"collect_query_metrics limit={limit}")
        
        metrics = []
        
        try:
            admin_db = self.client.admin
            
            slow_query_stats = admin_db.command("profile", -1)
            if isinstance(slow_query_stats, dict):
                metrics.extend(self._parse_slow_query_stats(slow_query_stats))
            
            system_profile = self._get_system_profile()
            if system_profile:
                metrics.extend(self._parse_system_profile(system_profile))
            
            metrics.extend(self._get_recent_operations(limit))
            
        except Exception as e:
            self.obs.log_error(f"Failed to collect query metrics: {e}")
        
        return metrics[:limit]

    def get_slow_queries(self, threshold_ms: float = 1000.0, limit: int = 50) -> List[QueryMetric]:
        self.obs.log_info(f"get_slow_queries threshold_ms={threshold_ms} limit={limit}")
        
        try:
            admin_db = self.client.admin
            
            profile_data = admin_db.command("profile", 0)
            if profile_data.get("ok", 0) == 1:
                slow_ops = profile_data.get("operations", [])
                
                slow_metrics = []
                for op in slow_ops:
                    if op.get("millis", 0) >= threshold_ms:
                        metric = self._convert_operation_to_metric(op)
                        if metric:
                            slow_metrics.append(metric)
                
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

    def _parse_slow_query_stats(self, stats: Dict[str, Any]) -> List[QueryMetric]:
        metrics = []
        
        if "operations" in stats:
            for op in stats["operations"]:
                metric = self._convert_operation_to_metric(op)
                if metric:
                    metrics.append(metric)
        
        return metrics

    def _parse_system_profile(self, profile_data: Dict[str, Any]) -> List[QueryMetric]:
        metrics = []
        
        if "op" in profile_data:
            metric = self._convert_operation_to_metric(profile_data)
            if metric:
                metrics.append(metric)
        
        return metrics

    def _get_recent_operations(self, limit: int) -> List[QueryMetric]:
        metrics = []
        
        try:
            admin_db = self.client.admin
            
            current_op = admin_db.command("currentOp")
            if isinstance(current_op, dict) and "inprog" in current_op:
                for op in current_op["inprog"][:limit]:
                    if op.get("millis", 0) > 0:
                        metric = self._convert_operation_to_metric(op)
                        if metric:
                            metrics.append(metric)
        
        except Exception as e:
            self.obs.log_error(f"Failed to get recent operations: {e}")
        
        return metrics

    def _convert_operation_to_metric(self, op: Dict[str, Any]) -> Optional[QueryMetric]:
        try:
            command = op.get("command", {})
            query = command.get("query") or command.get("aggregate") or command.get("find") or {}
            
            if isinstance(query, dict) and query:
                query_text = str(query)
            elif isinstance(query, str):
                query_text = query
            else:
                query_text = str(command)
            
            query_hash = QueryHashGenerator.generate_hash(query_text)
            
            execution_time_ms = float(op.get("millis", 0))
            performance_level = PerformanceClassifier.classify_performance(
                execution_time_ms, 
                PerformanceClassifier.get_default_thresholds()
            )
            
            status = QueryStatus.SUCCESS
            if op.get("errmsg"):
                status = QueryStatus.ERROR
            
            collection_name = command.get("find") or command.get("aggregate") or op.get("ns", "").split(".")[-1]
            
            plan_details = None
            if self.config.enable_query_plans:
                plan_details = self._extract_plan_details(op)
            
            indexes_used = []
            if plan_details:
                indexes_used = QueryPlanAnalyzer.extract_indexes_from_plan(plan_details)
            
            return QueryMetric(
                query_hash=query_hash,
                query_type=op.get("op", "unknown"),
                database="mongodb",
                collection_table=collection_name,
                execution_time_ms=execution_time_ms,
                status=status,
                performance_level=performance_level,
                timestamp=datetime.utcnow(),
                affected_rows=op.get("nreturned"),
                error_message=op.get("errmsg"),
                plan_details=plan_details,
                indexes_used=indexes_used,
                memory_usage_mb=self._extract_memory_usage(op)
            )
        
        except Exception as e:
            self.obs.log_error(f"Failed to convert operation to metric: {e}")
            return None

    def _extract_plan_details(self, op: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.config.enable_query_plans:
            return None
        
        try:
            if "explain" in op:
                return op["explain"]
            
            command = op.get("command", {})
            if "explain" in command:
                return command["explain"]
        
        except Exception as e:
            self.obs.log_error(f"Failed to extract plan details: {e}")
        
        return None

    def _extract_memory_usage(self, op: Dict[str, Any]) -> Optional[float]:
        if not self.config.enable_memory_tracking:
            return None
        
        try:
            if "stats" in op:
                stats = op["stats"]
                if "memoryUsage" in stats:
                    return float(stats["memoryUsage"]) / (1024 * 1024)  # Convert to MB
                elif "memory" in stats:
                    return float(stats["memory"]) / (1024 * 1024)
        
        except Exception as e:
            self.obs.log_error(f"Failed to extract memory usage: {e}")
        
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

    def get_collection_performance(self, collection_name: str, period_minutes: int = 60) -> Dict[str, Any]:
        self.obs.log_info(f"get_collection_performance collection={collection_name} period_minutes={period_minutes}")
        
        time_window = TimeWindowCalculator.get_time_windows(period_minutes)
        collection_metrics = [
            m for m in self._query_metrics_store
            if m.collection_table == collection_name and 
            time_window['period_start'] <= m.timestamp <= time_window['period_end']
        ]
        
        return QueryMetricsAggregator.aggregate_metrics(collection_metrics)

    def identify_index_gaps(self) -> List[Dict[str, Any]]:
        self.obs.log_info("identify_index_gaps")
        
        gaps = []
        
        try:
            slow_queries = self.get_slow_queries(threshold_ms=self.config.slow_query_threshold_ms)
            
            collection_analysis = {}
            for metric in slow_queries:
                if metric.collection_table:
                    if metric.collection_table not in collection_analysis:
                        collection_analysis[metric.collection_table] = {
                            'slow_queries': [],
                            'indexes_used': set(),
                            'avg_execution_time': 0
                        }
                    
                    collection_analysis[metric.collection_table]['slow_queries'].append(metric)
                    if metric.indexes_used:
                        collection_analysis[metric.collection_table]['indexes_used'].update(metric.indexes_used)
            
            for collection, analysis in collection_analysis.items():
                if len(analysis['slow_queries']) > 5 and len(analysis['indexes_used']) == 0:
                    gaps.append({
                        'collection': collection,
                        'slow_query_count': len(analysis['slow_queries']),
                        'avg_execution_time': sum(q.execution_time_ms for q in analysis['slow_queries']) / len(analysis['slow_queries']),
                        'recommendation': f"Consider adding indexes to collection '{collection}' to improve query performance"
                    })
        
        except Exception as e:
            self.obs.log_error(f"Failed to identify index gaps: {e}")
        
        return gaps

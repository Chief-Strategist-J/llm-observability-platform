import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests
from requests import Session

project_root = Path(__file__).resolve().parents[4)
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
from ..client.qdrant_client import (
    execute_request, get_http_client, QdrantConnectionConfig,
    list_collections, get_collection_info, search_points, scroll_points,
    count_points, get_cluster_info, get_metrics
)


class QdrantQueryCollector(IQueryPerformanceCollector):
    def __init__(self, session: Session, config: Optional[QueryMonitoringConfig] = None):
        self.session = session
        self.config = config or QueryMonitoringConfig()
        self.obs = ObservabilityClient(service_name="qdrant-query-collector")
        self._query_metrics_store = []
        self._max_store_size = self.config.max_query_history_size

    def collect_query_metrics(self, limit: int = 1000) -> List[QueryMetric]:
        self.obs.log_info(f"collect_query_metrics limit={limit}")
        
        metrics = []
        
        try:
            search_metrics = self._get_search_metrics()
            metrics.extend(search_metrics)
            
            collection_metrics = self._get_collection_metrics()
            metrics.extend(collection_metrics)
            
            cluster_metrics = self._get_cluster_metrics()
            metrics.extend(cluster_metrics)
            
            performance_metrics = self._get_performance_metrics()
            metrics.extend(performance_metrics)
            
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

    def _get_search_metrics(self) -> List[QueryMetric]:
        metrics = []
        
        try:
            # Get all collections
            collections_result = list_collections(self.session)
            
            if collections_result.success and collections_result.result:
                collections = collections_result.result.get("collections", [])
                
                for collection in collections[:5]:  # Limit to first 5 collections
                    collection_name = collection.get("name", "unknown")
                    
                    # Perform sample search
                    try:
                        # Create a dummy vector for testing
                        dummy_vector = [0.1] * 128  # Assuming 128-dimensional vectors
                        
                        search_result = search_points(
                            self.session,
                            collection_name,
                            dummy_vector,
                            limit=10
                        )
                        
                        if search_result.success:
                            performance_level = PerformanceClassifier.classify_performance(
                                search_result.execution_time_ms,
                                PerformanceClassifier.get_default_thresholds()
                            )
                            
                            metric = QueryMetric(
                                query_hash=QueryHashGenerator.generate_hash(f"search_{collection_name}"),
                                query_type="search",
                                database="qdrant",
                                collection_table=collection_name,
                                execution_time_ms=search_result.execution_time_ms,
                                status=QueryStatus.SUCCESS,
                                performance_level=performance_level,
                                timestamp=datetime.utcnow(),
                                affected_rows=search_result.result_count,
                                plan_details={
                                    "collection": collection_name,
                                    "vector_size": len(dummy_vector),
                                    "limit": 10,
                                    "result_count": search_result.result_count
                                }
                            )
                            metrics.append(metric)
                    except Exception:
                        pass  # Skip collections that can't be searched
        except Exception as e:
            self.obs.log_error(f"Failed to get search metrics: {e}")
        
        return metrics

    def _get_collection_metrics(self) -> List[QueryMetric]:
        metrics = []
        
        try:
            # Get collection info metrics
            collections_result = list_collections(self.session)
            
            if collections_result.success and collections_result.result:
                collections = collections_result.result.get("collections", [])
                
                for collection in collections:
                    collection_name = collection.get("name", "unknown")
                    
                    # Get detailed collection info
                    info_result = get_collection_info(self.session, collection_name)
                    
                    if info_result.success:
                        performance_level = PerformanceClassifier.classify_performance(
                            info_result.execution_time_ms,
                            PerformanceClassifier.get_default_thresholds()
                        )
                        
                        metric = QueryMetric(
                            query_hash=QueryHashGenerator.generate_hash(f"info_{collection_name}"),
                            query_type="collection_info",
                            database="qdrant",
                            collection_table=collection_name,
                            execution_time_ms=info_result.execution_time_ms,
                            status=QueryStatus.SUCCESS,
                            performance_level=performance_level,
                            timestamp=datetime.utcnow(),
                            plan_details={
                                "collection": collection_name,
                                "collection_info": info_result.result
                            }
                        )
                        metrics.append(metric)
                    
                    # Get point count
                    count_result = count_points(self.session, collection_name)
                    
                    if count_result.success:
                        performance_level = PerformanceClassifier.classify_performance(
                            count_result.execution_time_ms,
                            PerformanceClassifier.get_default_thresholds()
                        )
                        
                        metric = QueryMetric(
                            query_hash=QueryHashGenerator.generate_hash(f"count_{collection_name}"),
                            query_type="count",
                            database="qdrant",
                            collection_table=collection_name,
                            execution_time_ms=count_result.execution_time_ms,
                            status=QueryStatus.SUCCESS,
                            performance_level=performance_level,
                            timestamp=datetime.utcnow(),
                            affected_rows=count_result.result.get("result", {}).get("count", 0),
                            plan_details={
                                "collection": collection_name,
                                "point_count": count_result.result.get("result", {}).get("count", 0)
                            }
                        )
                        metrics.append(metric)
        except Exception as e:
            self.obs.log_error(f"Failed to get collection metrics: {e}")
        
        return metrics

    def _get_cluster_metrics(self) -> List[QueryMetric]:
        metrics = []
        
        try:
            # Get cluster info
            cluster_result = get_cluster_info(self.session)
            
            if cluster_result.success:
                performance_level = PerformanceClassifier.classify_performance(
                    cluster_result.execution_time_ms,
                    PerformanceClassifier.get_default_thresholds()
                )
                
                metric = QueryMetric(
                    query_hash=QueryHashGenerator.generate_hash("cluster_info"),
                    query_type="cluster_info",
                    database="qdrant",
                    collection_table=None,
                    execution_time_ms=cluster_result.execution_time_ms,
                    status=QueryStatus.SUCCESS,
                    performance_level=performance_level,
                    timestamp=datetime.utcnow(),
                    plan_details={
                        "cluster_info": cluster_result.result
                    }
                )
                metrics.append(metric)
            
            # Get performance metrics
            metrics_result = get_metrics(self.session)
            
            if metrics_result.success:
                performance_level = PerformanceClassifier.classify_performance(
                    metrics_result.execution_time_ms,
                    PerformanceClassifier.get_default_thresholds()
                )
                
                metric = QueryMetric(
                    query_hash=QueryHashGenerator.generate_hash("performance_metrics"),
                    query_type="performance_metrics",
                    database="qdrant",
                    collection_table=None,
                    execution_time_ms=metrics_result.execution_time_ms,
                    status=QueryStatus.SUCCESS,
                    performance_level=performance_level,
                    timestamp=datetime.utcnow(),
                    plan_details={
                        "performance_metrics": metrics_result.result
                    }
                )
                metrics.append(metric)
            
            # Get health check
            health_result = execute_request(self.session, "GET", "/health")
            
            if health_result.success:
                performance_level = PerformanceClassifier.classify_performance(
                    health_result.execution_time_ms,
                    PerformanceClassifier.get_default_thresholds()
                )
                
                metric = QueryMetric(
                    query_hash=QueryHashGenerator.generate_hash("health_check"),
                    query_type="health_check",
                    database="qdrant",
                    collection_table=None,
                    execution_time_ms=health_result.execution_time_ms,
                    status=QueryStatus.SUCCESS,
                    performance_level=performance_level,
                    timestamp=datetime.utcnow(),
                    plan_details={
                        "health_check": health_result.result
                    }
                )
                metrics.append(metric)
        
        except Exception as e:
            self.obs.log_error(f"Failed to get cluster metrics: {e}")
        
        return metrics

    def _get_performance_metrics(self) -> List[QueryMetric]:
        metrics = []
        
        try:
            # Simulate vector search performance with different vector sizes
            vector_sizes = [64, 128, 256, 512]
            
            collections_result = list_collections(self.session)
            
            if collections_result.success and collections_result.result:
                collections = collections_result.result.get("collections", [])
                
                if collections:
                    collection_name = collections[0].get("name", "test_collection")
                    
                    for vector_size in vector_sizes:
                        dummy_vector = [0.1] * vector_size
                        
                        try:
                            search_result = search_points(
                                self.session,
                                collection_name,
                                dummy_vector,
                                limit=5
                            )
                            
                            if search_result.success:
                                performance_level = PerformanceClassifier.classify_performance(
                                    search_result.execution_time_ms,
                                    PerformanceClassifier.get_default_thresholds()
                                )
                                
                                metric = QueryMetric(
                                    query_hash=QueryHashGenerator.generate_hash(f"search_{vector_size}"),
                                    query_type="vector_search",
                                    database="qdrant",
                                    collection_table=collection_name,
                                    execution_time_ms=search_result.execution_time_ms,
                                    status=QueryStatus.SUCCESS,
                                    performance_level=performance_level,
                                    timestamp=datetime.utcnow(),
                                    affected_rows=search_result.result_count,
                                    plan_details={
                                        "collection": collection_name,
                                        "vector_size": vector_size,
                                        "limit": 5
                                    }
                                )
                                metrics.append(metric)
                        except Exception:
                            pass  # Skip failed searches
        except Exception as e:
            self.obs.log_error(f"Failed to get performance metrics: {e}")
        
        return metrics

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
            
            collection_analysis = {}
            for metric in slow_queries:
                collection = metric.collection_table
                if collection:
                    if collection not in collection_analysis:
                        collection_analysis[collection] = {
                            'slow_queries': [],
                            'avg_execution_time': 0
                        }
                    
                    collection_analysis[collection]['slow_queries'].append(metric)
            
            for collection, analysis in collection_analysis.items():
                if len(analysis['slow_queries']) > 5:
                    avg_time = sum(q.execution_time_ms for q in analysis['slow_queries']) / len(analysis['slow_queries'])
                    
                    gaps.append({
                        'collection': collection,
                        'slow_query_count': len(analysis['slow_queries']),
                        'avg_execution_time': avg_time,
                        'recommendation': f"Consider optimizing collection '{collection}' or adjusting HNSW parameters"
                    })
        
        except Exception as e:
            self.obs.log_error(f"Failed to identify index gaps: {e}")
        
        return gaps

    def get_database_metrics(self) -> Dict[str, Any]:
        self.obs.log_info("get_database_metrics")
        
        try:
            metrics = {}
            
            # Get cluster info
            cluster_result = get_cluster_info(self.session)
            if cluster_result.success:
                cluster_info = cluster_result.result.get("result", {})
                metrics["cluster_info"] = cluster_info
                metrics["collections_count"] = len(cluster_info.get("collections", []))
            
            # Get performance metrics
            metrics_result = get_metrics(self.session)
            if metrics_result.success:
                metrics["performance_metrics"] = metrics_result.result.get("result", {})
            
            # Get collection details
            collections_result = list_collections(self.session)
            if collections_result.success:
                collections = collections_result.result.get("collections", [])
                metrics["collections"] = collections
                metrics["total_collections"] = len(collections)
            
            return metrics
        
        except Exception as e:
            self.obs.log_error(f"Failed to get database metrics: {e}")
            return {}

    def get_collection_statistics(self, collection_name: str) -> Dict[str, Any]:
        self.obs.log_info(f"get_collection_statistics collection={collection_name}")
        
        try:
            stats = {}
            
            # Get collection info
            info_result = get_collection_info(self.session, collection_name)
            if info_result.success:
                stats["collection_info"] = info_result.result
            
            # Get point count
            count_result = count_points(self.session, collection_name)
            if count_result.success:
                stats["point_count"] = count_result.result.get("result", {}).get("count", 0)
            
            # Get sample points to estimate data characteristics
            scroll_result = scroll_points(self.session, collection_name, limit=10)
            if scroll_result.success:
                points = scroll_result.result.get("result", {}).get("points", [])
                stats["sample_points"] = points
                
                if points:
                    # Analyze vector dimensions
                    first_point = points[0]
                    if "vector" in first_point:
                        vector_size = len(first_point["vector"])
                        stats["vector_size"] = vector_size
                    
                    # Analyze payload presence
                    has_payload = any("payload" in point for point in points)
                    stats["has_payload"] = has_payload
            
            return stats
        
        except Exception as e:
            self.obs.log_error(f"Failed to get collection statistics: {e}")
            return {}

    def get_vector_search_performance(self, collection_name: str) -> Dict[str, Any]:
        self.obs.log_info(f"get_vector_search_performance collection={collection_name}")
        
        try:
            performance_data = {
                "vector_sizes": [],
                "search_times": [],
                "result_counts": []
            }
            
            # Test search performance with different vector sizes
            vector_sizes = [64, 128, 256, 512, 1024]
            limits = [1, 10, 50, 100]
            
            for vector_size in vector_sizes:
                dummy_vector = [0.1] * vector_size
                
                for limit in limits:
                    try:
                        search_result = search_points(
                            self.session,
                            collection_name,
                            dummy_vector,
                            limit=limit
                        )
                        
                        if search_result.success:
                            performance_data["vector_sizes"].append(vector_size)
                            performance_data["search_times"].append(search_result.execution_time_ms)
                            performance_data["result_counts"].append(search_result.result_count or 0)
                    except Exception:
                        pass  # Skip failed searches
            
            return performance_data
        
        except Exception as e:
            self.obs.log_error(f"Failed to get vector search performance: {e}")
            return {}

    def get_hnsw_performance_analysis(self, collection_name: str) -> Dict[str, Any]:
        self.obs.log_info(f"get_hnsw_performance_analysis collection={collection_name}")
        
        try:
            analysis = {}
            
            # Get collection info to extract HNSW parameters
            info_result = get_collection_info(self.session, collection_name)
            if info_result.success:
                collection_info = info_result.result.get("result", {})
                hnsw_config = collection_info.get("config", {}).get("hnsw_config", {})
                
                if hnsw_config:
                    analysis["hnsw_config"] = hnsw_config
                    analysis["hnsw_parameters"] = {
                        "m": hnsw_config.get("m"),
                        "ef_construct": hnsw_config.get("ef_construct"),
                        "ef_search": hnsw_config.get("ef_search"),
                        "max_links": hnsw_config.get("max_links")
                    }
                
                # Get performance metrics for analysis
                performance_data = self.get_vector_search_performance(collection_name)
                if performance_data:
                    analysis["performance_data"] = performance_data
                    
                    # Calculate averages
                    avg_search_time = sum(performance_data["search_times"]) / len(performance_data["search_times"]) if performance_data["search_times"] else 0
                    avg_result_count = sum(performance_data["result_counts"]) / len(performance_data["result_counts"]) if performance_data["result_counts"] else 0
                    
                    analysis["averages"] = {
                        "avg_search_time_ms": avg_search_time,
                        "avg_result_count": avg_result_count
                    }
                
                # Generate recommendations
                recommendations = []
                if hnsw_config:
                    m = hnsw_config.get("m", 16)
                    ef_construct = hnsw_config.get("ef_construct", 200)
                    ef_search = hnsw_config.get("ef_search", 64)
                    
                    if m > 32:
                        recommendations.append("Consider reducing M parameter for better memory usage")
                    if ef_construct > 400:
                        recommendations.append("Consider reducing ef_construct for faster indexing")
                    if ef_search > 128:
                        recommendations.append("Consider reducing ef_search for faster search")
                
                if avg_search_time > 100:
                    recommendations.append("High average search time detected - consider optimization")
                
                analysis["recommendations"] = recommendations
            
            return analysis
        
        except Exception as e:
            self.obs.log_error(f"Failed to get HNSW performance analysis: {e}")
            return {}

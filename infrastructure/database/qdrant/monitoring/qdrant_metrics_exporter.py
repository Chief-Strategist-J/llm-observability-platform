import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from requests import Session

project_root = Path(__file__).resolve().parents[4)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.database.shared.query_monitoring_interfaces import (
    IMetricsExporter, QueryMetric, QueryMonitoringConfig
)
from infrastructure.database.shared.query_monitoring_utils import MetricsFormatter
from infrastructure.observability.scripts.observability_client import ObservabilityClient
from ..client.qdrant_client import (
    execute_request, get_http_client, QdrantConnectionConfig,
    list_collections, get_collection_info, search_points, scroll_points,
    count_points, get_cluster_info, get_metrics
)


class QdrantMetricsExporter(IMetricsExporter):
    def __init__(self, session: Session, config: Optional[QueryMonitoringConfig] = None):
        self.session = session
        self.config = config or QueryMonitoringConfig()
        self.obs = ObservabilityClient(service_name="qdrant-metrics-exporter")
        self._cached_metrics = {}
        self._cache_timestamp = None
        self._cache_ttl_seconds = 30

    def export_query_metrics(self, metrics: List[QueryMetric]) -> str:
        self.obs.log_info(f"export_query_metrics count={len(metrics)}")
        
        try:
            prometheus_format = MetricsFormatter.format_for_prometheus(metrics, "qdrant")
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
            
            prometheus_lines.append(f"# HELP qdrant_database_info Database information")
            prometheus_lines.append(f"# TYPE qdrant_database_info gauge")
            prometheus_lines.append(f'qdrant_database_info{{database="{database}"}} 1')
            
            if 'collections_count' in metrics:
                prometheus_lines.append(f"# HELP qdrant_collections_total Total number of collections")
                prometheus_lines.append(f"# TYPE qdrant_collections_total gauge")
                prometheus_lines.append(f'qdrant_collections_total{{database="{database}"}} {metrics["collections_count"]}')
            
            if 'total_collections' in metrics:
                prometheus_lines.append(f"# HELP qdrant_total_collections Total collections in cluster")
                prometheus_lines.append(f"# TYPE qdrant_total_collections gauge")
                prometheus_lines.append(f'qdrant_total_collections{{database="{database}"}} {metrics["total_collections"]}')
            
            # Export collection-specific metrics
            collections = metrics.get('collections', [])
            for collection in collections:
                collection_name = collection.get('name', 'unknown')
                vectors_config = collection.get('vectors', {})
                
                if 'size' in vectors_config:
                    prometheus_lines.append(f"# HELP qdrant_collection_vector_size Vector size for collection")
                    prometheus_lines.append(f"# TYPE qdrant_collection_vector_size gauge")
                    prometheus_lines.append(f'qdrant_collection_vector_size{{database="{database}",collection="{collection_name}"}} {vectors_config["size"]}')
                
                if 'distance' in vectors_config:
                    distance_value = self._distance_to_number(vectors_config['distance'])
                    prometheus_lines.append(f"# HELP qdrant_collection_distance Distance metric for collection")
                    prometheus_lines.append(f"# TYPE qdrant_collection_distance gauge")
                    prometheus_lines.append(f'qdrant_collection_distance{{database="{database}",collection="{collection_name}"}} {distance_value}')
            
            prometheus_lines.append(f"# HELP qdrant_export_timestamp_seconds Last export timestamp")
            prometheus_lines.append(f"# TYPE qdrant_export_timestamp_seconds gauge")
            prometheus_lines.append(f'qdrant_export_timestamp_seconds{{database="{database}"}} {datetime.utcnow().timestamp()}')
            
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
            from .qdrant_query_collector import QdrantQueryCollector
            collector = QdrantQueryCollector(self.session, self.config)
            
            metrics = collector.collect_query_metrics(limit=1000)
            return self.export_query_metrics(metrics)
        
        except Exception as e:
            self.obs.log_error(f"Failed to collect query metrics: {e}")
            return ""

    def _collect_database_status_metrics(self) -> str:
        try:
            from .qdrant_query_collector import QdrantQueryCollector
            collector = QdrantQueryCollector(self.session, self.config)
            
            db_metrics = collector.get_database_metrics()
            
            all_db_metrics = []
            for db_name in ["qdrant"]:
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
            
            # Get cluster info
            cluster_lines = self._get_cluster_metrics()
            prometheus_lines.extend(cluster_lines)
            
            # Get performance metrics
            performance_lines = self._get_performance_metrics()
            prometheus_lines.extend(performance_lines)
            
            # Get collection metrics
            collection_lines = self._get_collection_metrics()
            prometheus_lines.extend(collection_lines)
            
            # Get system metrics
            system_lines = self._get_system_metrics()
            prometheus_lines.extend(system_lines)
            
            prometheus_lines.append(f"# HELP qdrant_metrics_export_timestamp_seconds Last metrics export timestamp")
            prometheus_lines.append(f"# TYPE qdrant_metrics_export_timestamp_seconds gauge")
            prometheus_lines.append(f'qdrant_metrics_export_timestamp_seconds {datetime.utcnow().timestamp()}')
            
            return "\n".join(prometheus_lines)
        
        except Exception as e:
            self.obs.log_error(f"Failed to collect server metrics: {e}")
            return ""

    def _get_cluster_metrics(self) -> List[str]:
        lines = []
        
        try:
            cluster_result = get_cluster_info(self.session)
            if cluster_result.success:
                cluster_info = cluster_result.result.get("result", {})
                
                # Node count
                if "collections" in cluster_info:
                    node_count = len(cluster_info["collections"])
                    lines.append(f"# HELP qdrant_cluster_nodes_count Number of nodes in cluster")
                    lines.append(f"# TYPE qdrant_cluster_nodes_count gauge")
                    lines.append(f'qdrant_cluster_nodes_count {node_count}')
        
        except Exception as e:
            self.obs.log_error(f"Failed to get cluster metrics: {e}")
        
        return lines

    def _get_performance_metrics(self) -> List[str]:
        lines = []
        
        try:
            metrics_result = get_metrics(self.session)
            if metrics_result.success:
                metrics_data = metrics_result.result.get("result", {})
                
                # Extract performance metrics from the metrics data
                if isinstance(metrics_data, dict):
                    for key, value in metrics_data.items():
                        if isinstance(value, (int, float)):
                            metric_name = key.replace(".", "_").replace("-", "_")
                            lines.append(f"# HELP qdrant_performance_{metric_name} Performance metric: {metric_name}")
                            lines.append(f"# TYPE qdrant_performance_{metric_name} gauge")
                            lines.append(f'qdrant_performance_{metric_name} {value}')
        
        except Exception as e:
            self.obs.log_error(f"Failed to get performance metrics: {e}")
        
        return lines

    def _get_collection_metrics(self) -> List[str]:
        lines = []
        
        try:
            collections_result = list_collections(self.session)
            if collections_result.success:
                collections = collections_result.result.get("collections", [])
                
                for collection in collections:
                    collection_name = collection.get("name", "unknown")
                    
                    # Get collection info for detailed metrics
                    info_result = get_collection_info(self.session, collection_name)
                    if info_result.success:
                        collection_info = info_result.result.get("result", {})
                        
                        # Point count
                        count_result = count_points(self.session, collection_name)
                        if count_result.success:
                            point_count = count_result.result.get("result", {}).get("count", 0)
                            lines.append(f"# HELP qdrant_collection_points_count Number of points in collection")
                            lines.append(f"# TYPE qdrant_collection_points_count gauge")
                            lines.append(f'qdrant_collection_points_count{{collection="{collection_name}"}} {point_count}')
                        
                        # Vector configuration
                        vectors_config = collection_info.get("config", {}).get("vectors", {})
                        if isinstance(vectors_config, dict):
                            if "size" in vectors_config:
                                lines.append(f"# HELP qdrant_collection_vector_size Vector size for collection")
                                lines.append(f"# TYPE qdrant_collection_vector_size gauge")
                                lines.append(f'qdrant_collection_vector_size{{collection="{collection_name}"}} {vectors_config["size"]}')
                            
                            if "distance" in vectors_config:
                                distance_value = self._distance_to_number(vectors_config["distance"])
                                lines.append(f"# HELP qdrant_collection_distance Distance metric for collection")
                                lines.append(f"# TYPE qdrant_collection_distance gauge")
                                lines.append(f'qdrant_collection_distance{{collection="{collection_name}"}} {distance_value}')
                        
                        # HNSW configuration
                        hnsw_config = collection_info.get("config", {}).get("hnsw_config", {})
                        if isinstance(hnsw_config, dict):
                            for param_name, param_value in hnsw_config.items():
                                if isinstance(param_value, (int, float)):
                                    lines.append(f"# HELP qdrant_collection_hnsw_{param_name} HNSW parameter: {param_name}")
                                    lines.append(f"# TYPE qdrant_collection_hnsw_{param_name} gauge")
                                    lines.append(f'qdrant_collection_hnsw_{param_name}{{collection="{collection_name}"}} {param_value}')
                        
                        # Storage configuration
                        on_disk = collection_info.get("config", {}).get("on_disk", False)
                        lines.append(f"# HELP qdrant_collection_on_disk Whether collection is stored on disk")
                        lines.append(f"# TYPE qdrant_collection_on_disk gauge")
                        lines.append(f'qdrant_collection_on_disk{{collection="{collection_name}"}} {1 if on_disk else 0}')
        
        except Exception as e:
            self.obs.log_error(f"Failed to get collection metrics: {e}")
        
        return lines

    def _get_system_metrics(self) -> List[str]:
        lines = []
        
        try:
            # Get health check
            health_result = execute_request(self.session, "GET", "/health")
            if health_result.success:
                health_data = health_result.result.get("result", {})
                
                if "commit" in health_data:
                    lines.append(f"# HELP qdrant_version_info Qdrant version information")
                    lines.append(f"# TYPE qdrant_version_info gauge")
                    lines.append(f'qdrant_version_info 1')
                
                if "uptime" in health_data:
                    lines.append(f"# HELP qdrant_uptime_seconds Qdrant uptime in seconds")
                    lines.append(f"# TYPE qdrant_uptime_seconds gauge")
                    lines.append(f'qdrant_uptime_seconds {health_data["uptime"]}')
        
        except Exception as e:
            self.obs.log_error(f"Failed to get system metrics: {e}")
        
        return lines

    def _distance_to_number(self, distance: str) -> float:
        """Convert distance metric string to numeric value"""
        distance_mapping = {
            "Cosine": 1,
            "Euclidean": 2,
            "Manhattan": 3,
            "DotProduct": 4
        }
        return distance_mapping.get(distance, 0)

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
            
            collection_health = self._check_collection_health()
            if not collection_health["healthy"]:
                health_score -= 20
                issues.append("Collection health issues detected")
            
            performance_health = self._check_performance_health()
            if not performance_health["healthy"]:
                health_score -= 15
                issues.append("Performance health issues detected")
            
            return {
                "healthy": health_score >= 70,
                "health_score": health_score,
                "connectivity": connectivity_result,
                "query_test": query_result,
                "collection_health": collection_health,
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
            result = execute_request(self.session, "GET", "/health")
            
            return {
                "success": result.success,
                "error": result.error_message if not result.success else None
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _test_simple_query(self) -> Dict[str, Any]:
        try:
            result = list_collections(self.session)
            
            return {
                "success": result.success,
                "collection_count": len(result.result.get("collections", [])) if result.success else 0,
                "error": result.error_message if not result.success else None
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _check_collection_health(self) -> Dict[str, Any]:
        try:
            collections_result = list_collections(self.session)
            
            if not collections_result.success:
                return {
                    "healthy": False,
                    "error": collections_result.error_message
                }
            
            collections = collections_result.result.get("collections", [])
            healthy_collections = 0
            
            for collection in collections[:10]:  # Check first 10 collections
                collection_name = collection.get("name", "unknown")
                
                # Try to get collection info
                info_result = get_collection_info(self.session, collection_name)
                if info_result.success:
                    healthy_collections += 1
            
            health_ratio = healthy_collections / len(collections) if collections else 0
            healthy = health_ratio >= 0.8  # 80% of collections healthy
            
            return {
                "healthy": healthy,
                "total_collections": len(collections),
                "healthy_collections": healthy_collections,
                "health_ratio": health_ratio
            }
        
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    def _check_performance_health(self) -> Dict[str, Any]:
        try:
            metrics_result = get_metrics(self.session)
            
            if not metrics_result.success:
                return {
                    "healthy": False,
                    "error": metrics_result.error_message
                }
            
            metrics_data = metrics_result.result.get("result", {})
            
            # Check for performance indicators
            healthy = True
            
            # If we have performance metrics, we could analyze them here
            # For now, we'll assume healthy if we can get metrics
            if isinstance(metrics_data, dict) and len(metrics_data) > 0:
                healthy = True
            else:
                healthy = False
            
            return {
                "healthy": healthy,
                "metrics_available": isinstance(metrics_data, dict) and len(metrics_data) > 0,
                "metrics_count": len(metrics_data) if isinstance(metrics_data, dict) else 0
            }
        
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    def export_json_metrics(self) -> Dict[str, Any]:
        self.obs.log_info("export_json_metrics")
        
        try:
            from .qdrant_query_collector import QdrantQueryCollector
            collector = QdrantQueryCollector(self.session, self.config)
            
            query_metrics = collector.collect_query_metrics(limit=1000)
            
            db_metrics = collector.get_database_metrics()
            
            health = self.get_health_status()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "database": "qdrant",
                "query_metrics": MetricsFormatter.format_for_json_export(query_metrics, "qdrant"),
                "database_metrics": db_metrics,
                "health": health
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to export JSON metrics: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "database": "qdrant",
                "error": str(e)
            }

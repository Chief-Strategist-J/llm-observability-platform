import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import requests
from requests import Session

project_root = Path(__file__).resolve().parents[4)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.database.qdrant.monitoring.qdrant_query_collector import QdrantQueryCollector
from infrastructure.database.qdrant.monitoring.qdrant_query_analyzer import QdrantQueryAnalyzer
from infrastructure.database.qdrant.monitoring.qdrant_metrics_exporter import QdrantMetricsExporter
from infrastructure.database.qdrant.monitoring.qdrant_monitoring_client import QdrantMonitoringClient
from infrastructure.database.shared.query_monitoring_interfaces import (
    QueryMetric, QueryStatus, QueryPerformanceLevel, QueryMonitoringConfig
)


class TestQdrantQueryCollector(unittest.TestCase):
    def setUp(self):
        self.mock_session = Mock(spec=Session)
        self.config = QueryMonitoringConfig()
        self.collector = QdrantQueryCollector(self.mock_session, self.config)

    def test_collect_query_metrics(self):
        self.obs.log_info("test_collect_query_metrics")
        
        with patch.object(self.collector, '_get_search_metrics', return_value=[]):
            with patch.object(self.collector, '_get_collection_metrics', return_value=[]):
                with patch.object(self.collector, '_get_cluster_metrics', return_value=[]):
                    with patch.object(self.collector, '_get_performance_metrics', return_value=[]):
                        metrics = self.collector.collect_query_metrics(limit=10)
                        
                        self.assertIsInstance(metrics, list)

    def test_get_slow_queries(self):
        with patch.object(self.collector, 'collect_query_metrics') as mock_collect:
            mock_metrics = [
                QueryMetric(
                    query_hash="slow_hash",
                    query_type="search",
                    database="qdrant",
                    collection_table="test_collection",
                    execution_time_ms=1500.0,
                    status=QueryStatus.SUCCESS,
                    performance_level=QueryPerformanceLevel.SLOW,
                    timestamp=datetime.utcnow()
                ),
                QueryMetric(
                    query_hash="fast_hash",
                    query_type="info",
                    database="qdrant",
                    collection_table="test_collection",
                    execution_time_ms=500.0,
                    status=QueryStatus.SUCCESS,
                    performance_level=QueryPerformanceLevel.NORMAL,
                    timestamp=datetime.utcnow()
                )
            ]
            mock_collect.return_value = mock_metrics
            
            slow_queries = self.collector.get_slow_queries(threshold_ms=1000.0, limit=10)
            
            self.assertEqual(len(slow_queries), 1)
            self.assertEqual(slow_queries[0].query_hash, "slow_hash")

    def test_record_query_execution(self):
        metric = QueryMetric(
            query_hash="test_hash",
            query_type="search",
            database="qdrant",
            collection_table="test_collection",
            execution_time_ms=100.0,
            status=QueryStatus.SUCCESS,
            performance_level=QueryPerformanceLevel.FAST,
            timestamp=datetime.utcnow()
        )
        
        initial_count = len(self.collector._query_metrics_store)
        self.collector.record_query_execution(metric)
        
        self.assertEqual(len(self.collector._query_metrics_store), initial_count + 1)
        self.assertIn(metric, self.collector._query_metrics_store)

    def test_get_performance_summary(self):
        with patch('infrastructure.database.qdrant.monitoring.qdrant_query_collector.TimeWindowCalculator') as mock_time:
            mock_time.get_time_windows.return_value = {
                'period_start': datetime.utcnow() - timedelta(hours=1),
                'period_end': datetime.utcnow()
            }
            
            summary = self.collector.get_performance_summary(period_minutes=60)
            
            self.assertIsInstance(summary, dict)

    def test_identify_index_gaps(self):
        with patch.object(self.collector, 'get_slow_queries') as mock_slow:
            mock_slow.return_value = [
                QueryMetric(
                    query_hash="slow_hash",
                    query_type="search",
                    database="qdrant",
                    collection_table="test_collection",
                    execution_time_ms=1500.0,
                    status=QueryStatus.SUCCESS,
                    performance_level=QueryPerformanceLevel.SLOW,
                    timestamp=datetime.utcnow()
                )
            ]
            
            gaps = self.collector.identify_index_gaps()
            
            self.assertIsInstance(gaps, list)

    def test_get_database_metrics(self):
        with patch('infrastructure.database.qdrant.monitoring.qdrant_query_collector.get_cluster_info') as mock_cluster:
            with patch('infrastructure.database.qdrant.monitoring.qdrant_query_collector.get_metrics') as mock_metrics:
                mock_cluster.return_value = Mock()
                mock_cluster.return_value.success = True
                mock_cluster.return_value.result = {"result": {"collections": []}}
                mock_metrics.return_value = Mock()
                mock_metrics.return_value.success = True
                mock_metrics.return_value.result = {"result": {}}
                
                metrics = self.collector.get_database_metrics()
                
                self.assertIsInstance(metrics, dict)

    def test_get_collection_statistics(self):
        with patch('infrastructure.database.qdrant.monitoring.qdrant_query_collector.get_collection_info') as mock_info:
            with patch('infrastructure.database.qdrant.monitoring.qdrant_query_collector.count_points') as mock_count:
                mock_info.return_value = Mock()
                mock_info.return_value.success = True
                mock_info.return_value.result = {"result": {"config": {}}}
                mock_count.return_value = Mock()
                mock_count.return_value.success = True
                mock_count.return_value.result = {"result": {"count": 100}}
                
                stats = self.collector.get_collection_statistics("test_collection")
                
                self.assertIsInstance(stats, dict)

    def test_get_vector_search_performance(self):
        with patch('infrastructure.database.qdrant.monitoring.qdrant_query_collector.search_points') as mock_search:
            mock_search.return_value = Mock()
            mock_search.return_value.success = True
            mock_search.return_value.execution_time_ms = 50.0
            mock_search.return_value.result_count = 10
            
            performance = self.collector.get_vector_search_performance("test_collection")
            
            self.assertIsInstance(performance, dict)
            self.assertIn("vector_sizes", performance)
            self.assertIn("search_times", performance)

    def test_get_hnsw_performance_analysis(self):
        with patch.object(self.collector, 'get_collection_statistics') as mock_stats:
            mock_stats.return_value = {
                "collection_info": {
                    "config": {
                        "hnsw_config": {
                            "m": 16,
                            "ef_construct": 200,
                            "ef_search": 64
                        }
                    }
                }
            }
            
            with patch.object(self.collector, 'get_vector_search_performance') as mock_perf:
                mock_perf.return_value = {
                    "vector_sizes": [128, 256],
                    "search_times": [50.0, 75.0],
                    "result_counts": [10, 10]
                }
                
                analysis = self.collector.get_hnsw_performance_analysis("test_collection")
                
                self.assertIsInstance(analysis, dict)
                self.assertIn("hnsw_config", analysis)
                self.assertIn("recommendations", analysis)


class TestQdrantQueryAnalyzer(unittest.TestCase):
    def setUp(self):
        self.mock_session = Mock(spec=Session)
        self.analyzer = QdrantQueryAnalyzer(self.mock_session)

    def test_analyze_query(self):
        with patch.object(self.analyzer, 'explain_query') as mock_explain:
            mock_explain.return_value = {"operation": "search", "success": True}
            
            result = self.analyzer.analyze_query("search collection_name", "qdrant")
            
            self.assertIsNotNone(result)
            self.assertEqual(result.query_text, "search collection_name")
            mock_explain.assert_called_once_with("search collection_name", "qdrant")

    def test_explain_query(self):
        analysis = self.analyzer.explain_query("search collection_name", "qdrant")
        
        self.assertIsInstance(analysis, dict)
        self.assertTrue(analysis.get("success", False))
        self.assertEqual(analysis["operation"], "search")

    def test_suggest_indexes(self):
        suggestions = self.analyzer.suggest_indexes("search collection_name", "qdrant")
        
        self.assertIsInstance(suggestions, list)
        
        # Check for Qdrant-specific suggestions
        suggestion_types = [s.get("type") for s in suggestions]
        self.assertIn("hnsw_optimization", suggestion_types)

    def test_generate_performance_report(self):
        with patch.object(self.analyzer, '_get_database_name') as mock_db_name:
            mock_db_name.return_value = "qdrant"
            
            period_start = datetime.utcnow() - timedelta(hours=24)
            period_end = datetime.utcnow()
            
            report = self.analyzer.generate_performance_report("qdrant", period_start, period_end)
            
            self.assertIsNotNone(report)
            self.assertEqual(report.database, "qdrant")

    def test_get_query_plan_analysis(self):
        analysis = self.analyzer.get_query_plan_analysis("search collection_name", "qdrant")
        
        self.assertIsInstance(analysis, dict)
        self.assertIn("query", analysis)
        self.assertIn("analysis", analysis)

    def test_get_schema_analysis(self):
        with patch.object(self.analyzer, '_get_database_name') as mock_db_name:
            mock_db_name.return_value = "qdrant"
            
            analysis = self.analyzer.get_schema_analysis("qdrant")
            
            self.assertIsInstance(analysis, dict)
            self.assertTrue(analysis.get("success", False))

    def test_get_operation_info(self):
        info = self.analyzer._get_operation_info("search", ["collection_name"])
        
        self.assertIsInstance(info, dict)
        self.assertIn("complexity", info)
        self.assertIn("memory_impact", info)

    def test_extract_collection_name(self):
        self.assertEqual(self.analyzer._extract_collection_name("search collection_name"), "collection_name")
        self.assertEqual(self.analyzer._extract_collection_name("info collection=test_collection"), "test_collection")
        self.assertIsNone(self.analyzer._extract_collection_name("invalid query"))

    def test_generate_qdrant_specific_recommendations(self):
        metrics = [
            QueryMetric(
                query_hash="hash1",
                query_type="search",
                database="qdrant",
                execution_time_ms=1500.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.SLOW,
                timestamp=datetime.utcnow()
            )
        ]
        
        recommendations = self.analyzer._generate_qdrant_specific_recommendations(metrics)
        
        self.assertIsInstance(recommendations, list)


class TestQdrantMetricsExporter(unittest.TestCase):
    def setUp(self):
        self.mock_session = Mock(spec=Session)
        self.exporter = QdrantMetricsExporter(self.mock_session)

    def test_export_query_metrics(self):
        metrics = [
            QueryMetric(
                query_hash="hash1",
                query_type="search",
                database="qdrant",
                collection_table="test_collection",
                execution_time_ms=100.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.FAST,
                timestamp=datetime.utcnow()
            )
        ]
        
        result = self.exporter.export_query_metrics(metrics)
        
        self.assertIsInstance(result, str)
        self.assertIn("qdrant", result)

    def test_export_database_metrics(self):
        metrics = {
            "collections_count": 5,
            "total_collections": 5,
            "collections": [
                {"name": "collection1", "vectors": {"size": 128, "distance": "Cosine"}},
                {"name": "collection2", "vectors": {"size": 256, "distance": "Euclidean"}}
            ]
        }
        
        result = self.exporter.export_database_metrics("qdrant", metrics)
        
        self.assertIsInstance(result, str)
        self.assertIn("qdrant", result)

    def test_get_prometheus_metrics(self):
        with patch.object(self.exporter, '_collect_database_query_metrics') as mock_db_metrics:
            with patch.object(self.exporter, '_collect_server_metrics') as mock_server:
                mock_db_metrics.return_value = "db_metrics"
                mock_server.return_value = "server_metrics"
                
                result = self.exporter.get_prometheus_metrics()
                
                self.assertIsInstance(result, str)

    def test_get_health_status(self):
        with patch('infrastructure.database.qdrant.monitoring.qdrant_metrics_exporter.execute_request') as mock_request:
            mock_request.return_value = Mock()
            mock_request.success = True
            mock_request.result = {"result": {"commit": "test"}}
            
            health = self.exporter.get_health_status()
            
            self.assertIsInstance(health, dict)
            self.assertIn("healthy", health)
            self.assertIn("health_score", health)

    def test_export_json_metrics(self):
        with patch.object(self.exporter, '_collect_database_query_metrics') as mock_db_metrics:
            with patch.object(self.exporter, 'get_database_metrics') as mock_db:
                mock_db_metrics.return_value = []
                mock_db.return_value = {}
                
                metrics = self.exporter.export_json_metrics()
                
                self.assertIsInstance(metrics, dict)
                self.assertIn("database", metrics)
                self.assertIn("timestamp", metrics)

    def test_distance_to_number(self):
        self.assertEqual(self.exporter._distance_to_number("Cosine"), 1)
        self.assertEqual(self.exporter._distance_to_number("Euclidean"), 2)
        self.assertEqual(self.exporter._distance_to_number("Manhattan"), 3)
        self.assertEqual(self.exporter._distance_to_number("DotProduct"), 4)
        self.assertEqual(self.exporter._distance_to_number("Unknown"), 0)

    def test_get_collection_metrics(self):
        with patch('infrastructure.database.qdrant.monitoring.qdrant_metrics_exporter.list_collections') as mock_collections:
            with patch('infrastructure.database.qdrant.monitoring.qdrant_metrics_exporter.get_collection_info') as mock_info:
                with patch('infrastructure.database.qdrant.monitoring.qdrant_metrics_exporter.count_points') as mock_count:
                    mock_collections.return_value = Mock()
                    mock_collections.return_value.success = True
                    mock_collections.return_value.result = {"collections": [{"name": "test_collection"}]}
                    
                    mock_info.return_value = Mock()
                    mock_info.return_value.success = True
                    mock_info.return_value.result = {"result": {"config": {"vectors": {"size": 128}}}}
                    
                    mock_count.return_value = Mock()
                    mock_count.return_value.success = True
                    mock_count.return_value.result = {"result": {"count": 100}}
                    
                    lines = self.exporter._get_collection_metrics()
                    
                    self.assertIsInstance(lines, list)
                    self.assertTrue(len(lines) > 0)


class TestQdrantMonitoringClient(unittest.TestCase):
    def setUp(self):
        self.mock_session = Mock(spec=Session)
        self.config = QueryMonitoringConfig()
        self.monitoring_client = QdrantMonitoringClient(self.mock_session, self.config)

    def test_execute_with_monitoring(self):
        with patch('infrastructure.database.qdrant.monitoring.qdrant_monitoring_client.search_points') as mock_search:
            mock_search.return_value = Mock()
            mock_search.return_value.success = True
            mock_search.return_value.result = {"points": []}
            mock_search.return_value.execution_time_ms = 100.0
            
            result = self.monitoring_client.execute_with_monitoring("search collection_name")
            
            self.assertTrue(result["success"])
            self.assertIn("execution_time_ms", result)
            self.assertIn("performance_level", result)

    def test_get_performance_summary(self):
        with patch.object(self.monitoring_client.collector, 'get_performance_summary') as mock_summary:
            with patch.object(self.monitoring_client.exporter, 'get_health_status') as mock_health:
                mock_summary.return_value = {"total_queries": 100}
                mock_health.return_value = {"healthy": True}
                
                result = self.monitoring_client.get_performance_summary(period_minutes=60)
                
                self.assertIsInstance(result, dict)
                self.assertIn("summary", result)
                self.assertIn("health", result)

    def test_identify_performance_issues(self):
        with patch.object(self.monitoring_client.collector, 'get_slow_queries') as mock_slow:
            with patch.object(self.monitoring_client.collector, 'identify_index_gaps') as mock_gaps:
                with patch.object(self.monitoring_client.exporter, 'get_health_status') as mock_health:
                    mock_slow.return_value = []
                    mock_gaps.return_value = []
                    mock_health.return_value = {"healthy": True}
                    
                    issues = self.monitoring_client.identify_performance_issues()
                    
                    self.assertIsInstance(issues, list)

    def test_get_slow_queries_analysis(self):
        with patch.object(self.monitoring_client.collector, 'get_slow_queries') as mock_slow:
            mock_slow.return_value = []
            
            analysis = self.monitoring_client.get_slow_queries_analysis(hours=24)
            
            self.assertIsInstance(analysis, dict)
            self.assertIn("period_hours", analysis)
            self.assertEqual(analysis["period_hours"], 24)

    def test_get_database_health_report(self):
        with patch.object(self.monitoring_client, 'get_performance_summary') as mock_summary:
            with patch.object(self.monitoring_client.exporter, 'get_health_status') as mock_health:
                with patch.object(self.monitoring_client, 'identify_performance_issues') as mock_issues:
                    mock_summary.return_value = {"summary": {}}
                    mock_health.return_value = {"healthy": True}
                    mock_issues.return_value = []
                    
                    report = self.monitoring_client.get_database_health_report()
                    
                    self.assertIsInstance(report, dict)
                    self.assertIn("overall_health_score", report)
                    self.assertIn("health_status", report)

    def test_get_schema_performance_analysis(self):
        with patch.object(self.monitoring_client.analyzer, 'get_schema_analysis') as mock_schema:
            mock_schema.return_value = {"success": True, "schema": {}}
            
            analysis = self.monitoring_client.get_schema_performance_analysis()
            
            self.assertIsInstance(analysis, dict)
            self.assertIn("schema", analysis)

    def test_get_collection_performance_analysis(self):
        with patch.object(self.monitoring_client.collector, 'get_collection_statistics') as mock_stats:
            with patch.object(self.monitoring_client.collector, 'get_hnsw_performance_analysis') as mock_hnsw:
                with patch.object(self.monitoring_client.collector, 'get_vector_search_performance') as mock_vector:
                    mock_stats.return_value = {
                        "collection_info": {"config": {"vectors": {"size": 128}}},
                        "point_count": 1000
                    }
                    mock_hnsw.return_value = {"hnsw_config": {"m": 16}}
                    mock_vector.return_value = {"vector_sizes": [128], "search_times": [50.0]}
                    
                    analysis = self.monitoring_client.get_collection_performance_analysis("test_collection")
                    
                    self.assertIsInstance(analysis, dict)
                    self.assertIn("statistics", analysis)
                    self.assertIn("hnsw_analysis", analysis)


class TestQdrantIntegration(unittest.TestCase):
    """Integration tests for Qdrant monitoring components"""
    
    def setUp(self):
        self.mock_session = Mock(spec=Session)
        self.config = QueryMonitoringConfig()

    def test_end_to_end_monitoring_flow(self):
        with patch('infrastructure.database.qdrant.monitoring.qdrant_monitoring_client.search_points') as mock_search:
            mock_search.return_value = Mock()
            mock_search.return_value.success = True
            mock_search.return_value.result = {"points": []}
            mock_search.return_value.execution_time_ms = 1500.0
            
            client = QdrantMonitoringClient(self.mock_session, self.config)
            result = client.execute_with_monitoring("search collection_name")
            
            self.assertTrue(result["success"])
            self.assertEqual(result["performance_level"], QueryPerformanceLevel.SLOW)

    def test_error_handling(self):
        with patch('infrastructure.database.qdrant.monitoring.qdrant_monitoring_client.search_points') as mock_search:
            mock_search.side_effect = Exception("Database error")
            
            client = QdrantMonitoringClient(self.mock_session, self.config)
            result = client.execute_with_monitoring("search collection_name")
            
            self.assertFalse(result["success"])
            self.assertIn("error", result)
            self.assertEqual(result["performance_level"], QueryPerformanceLevel.CRITICAL)

    def test_vector_search_integration(self):
        with patch.object(self.mock_session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": {"points": []}}
            mock_post.return_value = mock_response
            
            client = QdrantMonitoringClient(self.mock_session, self.config)
            
            # Test vector search with different vector sizes
            vector_sizes = [64, 128, 256, 512]
            for vector_size in vector_sizes:
                dummy_vector = [0.1] * vector_size
                result = client.execute_with_monitoring(f"search collection_name", {"vector_size": vector_size})
                self.assertTrue(result["success"])

    def test_hnsw_analysis_integration(self):
        with patch.object(self.mock_session, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": {"config": {"hnsw_config": {"m": 16}}}}
            mock_post.return_value = mock_response
            
            client = QdrantMonitoringClient(self.mock_session, self.config)
            analysis = client.collector.get_hnsw_performance_analysis("test_collection")
            
            self.assertIsInstance(analysis, dict)
            self.assertIn("hnsw_config", analysis)


if __name__ == '__main__':
    unittest.main()

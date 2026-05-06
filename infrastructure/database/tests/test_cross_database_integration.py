import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.database.shared.query_monitoring_interfaces import (
    QueryMetric, QueryStatus, QueryPerformanceLevel, QueryMonitoringConfig
)


class TestCrossDatabaseIntegration(unittest.TestCase):
    """Integration tests for all database monitoring components"""
    
    def setUp(self):
        self.config = QueryMonitoringConfig()
        
        # Mock clients for all databases
        self.mock_mongo_client = Mock()
        self.mock_neo4j_session = Mock()
        self.mock_postgres_cursor = Mock()
        self.mock_cassandra_session = Mock()
        self.mock_redis_client = Mock()
        self.mock_qdrant_session = Mock()

    def test_all_databases_query_monitoring_consistency(self):
        """Test that all database monitoring clients follow the same interface"""
        databases = {
            'mongodb': self.mock_mongo_client,
            'neo4j': self.mock_neo4j_session,
            'postgres': self.mock_postgres_cursor,
            'cassandra': self.mock_cassandra_session,
            'redis': self.mock_redis_client,
            'qdrant': self.mock_qdrant_session
        }
        
        for db_name, mock_client in databases.items():
            with self.subTest(database=db_name):
                # Import the appropriate monitoring client
                if db_name == 'mongodb':
                    from infrastructure.database.mongodb.monitoring.mongodb_monitoring_client import MongoDBMonitoringClient
                    client = MongoDBMonitoringClient(mock_client, self.config)
                elif db_name == 'neo4j':
                    from infrastructure.database.neo4j.monitoring.neo4j_monitoring_client import Neo4jMonitoringClient
                    client = Neo4jMonitoringClient(mock_client, self.config)
                elif db_name == 'postgres':
                    from infrastructure.database.postgres.monitoring.postgres_monitoring_client import PostgreSQLMonitoringClient
                    client = PostgreSQLMonitoringClient(mock_client, self.config)
                elif db_name == 'cassandra':
                    from infrastructure.database.cassandra.monitoring.cassandra_monitoring_client import CassandraMonitoringClient
                    client = CassandraMonitoringClient(mock_client, self.config)
                elif db_name == 'redis':
                    from infrastructure.database.redis.monitoring.redis_monitoring_client import RedisMonitoringClient
                    client = RedisMonitoringClient(mock_client, self.config)
                elif db_name == 'qdrant':
                    from infrastructure.database.qdrant.monitoring.qdrant_monitoring_client import QdrantMonitoringClient
                    client = QdrantMonitoringClient(mock_client, self.config)
                
                # Test that all clients have the same interface
                self.assertTrue(hasattr(client, 'execute_with_monitoring'))
                self.assertTrue(hasattr(client, 'get_performance_summary'))
                self.assertTrue(hasattr(client, 'identify_performance_issues'))
                self.assertTrue(hasattr(client, 'get_database_health_report'))
                self.assertTrue(hasattr(client, 'get_schema_performance_analysis'))

    def test_all_databases_collector_interface_consistency(self):
        """Test that all query collectors follow the same interface"""
        databases = {
            'mongodb': self.mock_mongo_client,
            'neo4j': self.mock_neo4j_session,
            'postgres': self.mock_postgres_cursor,
            'cassandra': self.mock_cassandra_session,
            'redis': self.mock_redis_client,
            'qdrant': self.mock_qdrant_session
        }
        
        for db_name, mock_client in databases.items():
            with self.subTest(database=db_name):
                # Import the appropriate collector
                if db_name == 'mongodb':
                    from infrastructure.database.mongodb.monitoring.mongodb_query_collector import MongoDBQueryCollector
                    collector = MongoDBQueryCollector(mock_client, self.config)
                elif db_name == 'neo4j':
                    from infrastructure.database.neo4j.monitoring.neo4j_query_collector import Neo4jQueryCollector
                    collector = Neo4jQueryCollector(mock_client, self.config)
                elif db_name == 'postgres':
                    from infrastructure.database.postgres.monitoring.postgres_query_collector import PostgreSQLQueryCollector
                    collector = PostgreSQLQueryCollector(mock_client, self.config)
                elif db_name == 'cassandra':
                    from infrastructure.database.cassandra.monitoring.cassandra_query_collector import CassandraQueryCollector
                    collector = CassandraQueryCollector(mock_client, self.config)
                elif db_name == 'redis':
                    from infrastructure.database.redis.monitoring.redis_query_collector import RedisQueryCollector
                    collector = RedisQueryCollector(mock_client, self.config)
                elif db_name == 'qdrant':
                    from infrastructure.database.qdrant.monitoring.qdrant_query_collector import QdrantQueryCollector
                    collector = QdrantQueryCollector(mock_client, self.config)
                
                # Test that all collectors have the same interface
                self.assertTrue(hasattr(collector, 'collect_query_metrics'))
                self.assertTrue(hasattr(collector, 'get_slow_queries'))
                self.assertTrue(hasattr(collector, 'record_query_execution'))
                self.assertTrue(hasattr(collector, 'get_performance_summary'))
                self.assertTrue(hasattr(collector, 'identify_index_gaps'))

    def test_all_databases_analyzer_interface_consistency(self):
        """Test that all query analyzers follow the same interface"""
        databases = {
            'mongodb': self.mock_mongo_client,
            'neo4j': self.mock_neo4j_session,
            'postgres': self.mock_postgres_cursor,
            'cassandra': self.mock_cassandra_session,
            'redis': self.mock_redis_client,
            'qdrant': self.mock_qdrant_session
        }
        
        for db_name, mock_client in databases.items():
            with self.subTest(database=db_name):
                # Import the appropriate analyzer
                if db_name == 'mongodb':
                    from infrastructure.database.mongodb.monitoring.mongodb_query_analyzer import MongoDBQueryAnalyzer
                    analyzer = MongoDBQueryAnalyzer(mock_client)
                elif db_name == 'neo4j':
                    from infrastructure.database.neo4j.monitoring.neo4j_query_analyzer import Neo4jQueryAnalyzer
                    analyzer = Neo4jQueryAnalyzer(mock_client)
                elif db_name == 'postgres':
                    from infrastructure.database.postgres.monitoring.postgres_query_analyzer import PostgreSQLQueryAnalyzer
                    analyzer = PostgreSQLQueryAnalyzer(mock_client)
                elif db_name == 'cassandra':
                    from infrastructure.database.cassandra.monitoring.cassandra_query_analyzer import CassandraQueryAnalyzer
                    analyzer = CassandraQueryAnalyzer(mock_client)
                elif db_name == 'redis':
                    from infrastructure.database.redis.monitoring.redis_query_analyzer import RedisQueryAnalyzer
                    analyzer = RedisQueryAnalyzer(mock_client)
                elif db_name == 'qdrant':
                    from infrastructure.database.qdrant.monitoring.qdrant_query_analyzer import QdrantQueryAnalyzer
                    analyzer = QdrantQueryAnalyzer(mock_client)
                
                # Test that all analyzers have the same interface
                self.assertTrue(hasattr(analyzer, 'analyze_query'))
                self.assertTrue(hasattr(analyzer, 'explain_query'))
                self.assertTrue(hasattr(analyzer, 'suggest_indexes'))
                self.assertTrue(hasattr(analyzer, 'generate_performance_report'))
                self.assertTrue(hasattr(analyzer, 'get_schema_analysis'))

    def test_all_databases_exporter_interface_consistency(self):
        """Test that all metrics exporters follow the same interface"""
        databases = {
            'mongodb': self.mock_mongo_client,
            'neo4j': self.mock_neo4j_session,
            'postgres': self.mock_postgres_cursor,
            'cassandra': self.mock_cassandra_session,
            'redis': self.mock_redis_client,
            'qdrant': self.mock_qdrant_session
        }
        
        for db_name, mock_client in databases.items():
            with self.subTest(database=db_name):
                # Import the appropriate exporter
                if db_name == 'mongodb':
                    from infrastructure.database.mongodb.monitoring.mongodb_metrics_exporter import MongoDBMetricsExporter
                    exporter = MongoDBMetricsExporter(mock_client, self.config)
                elif db_name == 'neo4j':
                    from infrastructure.database.neo4j.monitoring.neo4j_metrics_exporter import Neo4jMetricsExporter
                    exporter = Neo4jMetricsExporter(mock_client, self.config)
                elif db_name == 'postgres':
                    from infrastructure.database.postgres.monitoring.postgres_metrics_exporter import PostgreSQLMetricsExporter
                    exporter = PostgreSQLMetricsExporter(mock_client, self.config)
                elif db_name == 'cassandra':
                    from infrastructure.database.cassandra.monitoring.cassandra_metrics_exporter import CassandraMetricsExporter
                    exporter = CassandraMetricsExporter(mock_client, self.config)
                elif db_name == 'redis':
                    from infrastructure.database.redis.monitoring.redis_metrics_exporter import RedisMetricsExporter
                    exporter = RedisMetricsExporter(mock_client, self.config)
                elif db_name == 'qdrant':
                    from infrastructure.database.qdrant.monitoring.qdrant_metrics_exporter import QdrantMetricsExporter
                    exporter = QdrantMetricsExporter(mock_client, self.config)
                
                # Test that all exporters have the same interface
                self.assertTrue(hasattr(exporter, 'export_query_metrics'))
                self.assertTrue(hasattr(exporter, 'export_database_metrics'))
                self.assertTrue(hasattr(exporter, 'get_prometheus_metrics'))
                self.assertTrue(hasattr(exporter, 'get_health_status'))
                self.assertTrue(hasattr(exporter, 'export_json_metrics'))

    def test_shared_analyzer_api_all_databases(self):
        """Test that the shared analyzer API works with all databases"""
        from infrastructure.database.shared.analyzer_api import (
            _analyze_mongodb_query, _analyze_neo4j_query, _analyze_postgres_query,
            _analyze_cassandra_query, _analyze_redis_query, _analyze_qdrant_query,
            _get_mongodb_performance_summary, _get_neo4j_performance_summary,
            _get_postgres_performance_summary, _get_cassandra_performance_summary,
            _get_redis_performance_summary, _get_qdrant_performance_summary,
            _get_mongodb_health, _get_neo4j_health, _get_postgres_health,
            _get_cassandra_health, _get_redis_health, _get_qdrant_health,
            _get_mongodb_metrics, _get_neo4j_metrics, _get_postgres_metrics,
            _get_cassandra_metrics, _get_redis_metrics, _get_qdrant_metrics
        )
        
        # Test that all helper functions exist and can be called
        analysis_functions = [
            _analyze_mongodb_query, _analyze_neo4j_query, _analyze_postgres_query,
            _analyze_cassandra_query, _analyze_redis_query, _analyze_qdrant_query
        ]
        
        performance_functions = [
            _get_mongodb_performance_summary, _get_neo4j_performance_summary,
            _get_postgres_performance_summary, _get_cassandra_performance_summary,
            _get_redis_performance_summary, _get_qdrant_performance_summary
        ]
        
        health_functions = [
            _get_mongodb_health, _get_neo4j_health, _get_postgres_health,
            _get_cassandra_health, _get_redis_health, _get_qdrant_health
        ]
        
        metrics_functions = [
            _get_mongodb_metrics, _get_neo4j_metrics, _get_postgres_metrics,
            _get_cassandra_metrics, _get_redis_metrics, _get_qdrant_metrics
        ]
        
        # Test that all functions are callable
        for func in analysis_functions + performance_functions + health_functions + metrics_functions:
            self.assertTrue(callable(func))

    def test_cross_database_performance_comparison(self):
        """Test cross-database performance comparison functionality"""
        from infrastructure.database.shared.analyzer_api import _compare_performance_metrics
        
        # Mock performance data for all databases
        performance_data = {
            'mongodb': {
                'total_queries': 1000,
                'avg_execution_time_ms': 50.0,
                'slow_query_count': 10
            },
            'neo4j': {
                'total_queries': 800,
                'avg_execution_time_ms': 75.0,
                'slow_query_count': 15
            },
            'postgres': {
                'total_queries': 1200,
                'avg_execution_time_ms': 45.0,
                'slow_query_count': 8
            },
            'cassandra': {
                'total_queries': 900,
                'avg_execution_time_ms': 60.0,
                'slow_query_count': 12
            },
            'redis': {
                'total_queries': 1500,
                'avg_execution_time_ms': 25.0,
                'slow_query_count': 5
            },
            'qdrant': {
                'total_queries': 600,
                'avg_execution_time_ms': 120.0,
                'slow_query_count': 20
            }
        }
        
        comparison = _compare_performance_metrics(performance_data)
        
        self.assertIsInstance(comparison, dict)
        self.assertIn('performance_scores', comparison)
        self.assertIn('recommendations', comparison)
        self.assertIn('optimization_potential', comparison)

    def test_cross_database_health_aggregation(self):
        """Test cross-database health aggregation functionality"""
        from infrastructure.database.shared.analyzer_api import _calculate_overall_health
        
        # Mock health data for all databases
        health_data = {
            'mongodb': {'healthy': True, 'health_score': 85},
            'neo4j': {'healthy': True, 'health_score': 90},
            'postgres': {'healthy': True, 'health_score': 95},
            'cassandra': {'healthy': False, 'health_score': 60},
            'redis': {'healthy': True, 'health_score': 80},
            'qdrant': {'healthy': True, 'health_score': 75}
        }
        
        overall_health = _calculate_overall_health(health_data)
        
        self.assertIsInstance(overall_health, dict)
        self.assertIn('overall_score', overall_health)
        self.assertIn('healthy_databases', overall_health)
        self.assertIn('unhealthy_databases', overall_health)
        self.assertIn('overall_status', overall_health)

    def test_cross_database_metrics_aggregation(self):
        """Test cross-database metrics aggregation functionality"""
        from infrastructure.database.shared.analyzer_api import _aggregate_metrics
        
        # Mock metrics data for all databases
        metrics_data = {
            'mongodb': {'query_count': 1000, 'error_rate': 2.0},
            'neo4j': {'query_count': 800, 'error_rate': 1.5},
            'postgres': {'query_count': 1200, 'error_rate': 1.0},
            'cassandra': {'query_count': 900, 'error_rate': 3.0},
            'redis': {'query_count': 1500, 'error_rate': 0.5},
            'qdrant': {'query_count': 600, 'error_rate': 2.5}
        }
        
        aggregated = _aggregate_metrics(metrics_data)
        
        self.assertIsInstance(aggregated, dict)
        self.assertIn('total_queries', aggregated)
        self.assertIn('avg_error_rate', aggregated)
        self.assertIn('database_breakdown', aggregated)

    def test_all_databases_error_handling_consistency(self):
        """Test that all databases handle errors consistently"""
        databases = {
            'mongodb': self.mock_mongo_client,
            'neo4j': self.mock_neo4j_session,
            'postgres': self.mock_postgres_cursor,
            'cassandra': self.mock_cassandra_session,
            'redis': self.mock_redis_client,
            'qdrant': self.mock_qdrant_session
        }
        
        for db_name, mock_client in databases.items():
            with self.subTest(database=db_name):
                # Import and create the appropriate monitoring client
                if db_name == 'mongodb':
                    from infrastructure.database.mongodb.monitoring.mongodb_monitoring_client import MongoDBMonitoringClient
                    client = MongoDBMonitoringClient(mock_client, self.config)
                elif db_name == 'neo4j':
                    from infrastructure.database.neo4j.monitoring.neo4j_monitoring_client import Neo4jMonitoringClient
                    client = Neo4jMonitoringClient(mock_client, self.config)
                elif db_name == 'postgres':
                    from infrastructure.database.postgres.monitoring.postgres_monitoring_client import PostgreSQLMonitoringClient
                    client = PostgreSQLMonitoringClient(mock_client, self.config)
                elif db_name == 'cassandra':
                    from infrastructure.database.cassandra.monitoring.cassandra_monitoring_client import CassandraMonitoringClient
                    client = CassandraMonitoringClient(mock_client, self.config)
                elif db_name == 'redis':
                    from infrastructure.database.redis.monitoring.redis_monitoring_client import RedisMonitoringClient
                    client = RedisMonitoringClient(mock_client, self.config)
                elif db_name == 'qdrant':
                    from infrastructure.database.qdrant.monitoring.qdrant_monitoring_client import QdrantMonitoringClient
                    client = QdrantMonitoringClient(mock_client, self.config)
                
                # Test error handling in execute_with_monitoring
                # This should be handled by mocking the underlying database operations
                result = client.get_performance_summary(period_minutes=60)
                
                # All databases should return a consistent structure even on error
                self.assertIsInstance(result, dict)
                self.assertIn('summary', result)

    def test_all_databases_metrics_format_consistency(self):
        """Test that all databases produce metrics in consistent format"""
        databases = {
            'mongodb': self.mock_mongo_client,
            'neo4j': self.mock_neo4j_session,
            'postgres': self.mock_postgres_cursor,
            'cassandra': self.mock_cassandra_session,
            'redis': self.mock_redis_client,
            'qdrant': self.mock_qdrant_session
        }
        
        for db_name, mock_client in databases.items():
            with self.subTest(database=db_name):
                # Import the appropriate exporter
                if db_name == 'mongodb':
                    from infrastructure.database.mongodb.monitoring.mongodb_metrics_exporter import MongoDBMetricsExporter
                    exporter = MongoDBMetricsExporter(mock_client, self.config)
                elif db_name == 'neo4j':
                    from infrastructure.database.neo4j.monitoring.neo4j_metrics_exporter import Neo4jMetricsExporter
                    exporter = Neo4jMetricsExporter(mock_client, self.config)
                elif db_name == 'postgres':
                    from infrastructure.database.postgres.monitoring.postgres_metrics_exporter import PostgreSQLMetricsExporter
                    exporter = PostgreSQLMetricsExporter(mock_client, self.config)
                elif db_name == 'cassandra':
                    from infrastructure.database.cassandra.monitoring.cassandra_metrics_exporter import CassandraMetricsExporter
                    exporter = CassandraMetricsExporter(mock_client, self.config)
                elif db_name == 'redis':
                    from infrastructure.database.redis.monitoring.redis_metrics_exporter import RedisMetricsExporter
                    exporter = RedisMetricsExporter(mock_client, self.config)
                elif db_name == 'qdrant':
                    from infrastructure.database.qdrant.monitoring.qdrant_metrics_exporter import QdrantMetricsExporter
                    exporter = QdrantMetricsExporter(mock_client, self.config)
                
                # Test JSON export format consistency
                json_metrics = exporter.export_json_metrics()
                
                self.assertIsInstance(json_metrics, dict)
                self.assertIn('database', json_metrics)
                self.assertIn('timestamp', json_metrics)
                
                # Test that database name is correct
                expected_db_name = db_name
                if db_name == 'postgres':
                    expected_db_name = 'postgresql'  # PostgreSQL uses different naming
                self.assertEqual(json_metrics['database'], expected_db_name)

    def test_all_databases_query_metric_consistency(self):
        """Test that all databases produce QueryMetric objects consistently"""
        # Create a sample query metric
        metric = QueryMetric(
            query_hash="test_hash",
            query_type="test_query",
            database="test_db",
            collection_table="test_table",
            execution_time_ms=100.0,
            status=QueryStatus.SUCCESS,
            performance_level=QueryPerformanceLevel.FAST,
            timestamp=datetime.utcnow()
        )
        
        # Test that the metric has all required fields
        self.assertIsNotNone(metric.query_hash)
        self.assertIsNotNone(metric.query_type)
        self.assertIsNotNone(metric.database)
        self.assertIsNotNone(metric.execution_time_ms)
        self.assertIsNotNone(metric.status)
        self.assertIsNotNone(metric.performance_level)
        self.assertIsNotNone(metric.timestamp)
        
        # Test that metric can be serialized
        metric_dict = metric.dict()
        self.assertIsInstance(metric_dict, dict)
        self.assertIn('query_hash', metric_dict)
        self.assertIn('query_type', metric_dict)
        self.assertIn('database', metric_dict)


class TestSharedAnalyzerAPIIntegration(unittest.TestCase):
    """Integration tests for the shared analyzer API"""
    
    def test_cross_database_analysis_endpoints(self):
        """Test that cross-database analysis endpoints work with all databases"""
        from infrastructure.database.shared.analyzer_api import (
            CrossDatabaseAnalysisRequest, PerformanceComparisonRequest,
            OptimizationReportRequest
        )
        
        # Test request models
        analysis_request = CrossDatabaseAnalysisRequest(
            query="SELECT * FROM users",
            databases=["mongodb", "neo4j", "postgres", "cassandra", "redis", "qdrant"]
        )
        
        performance_request = PerformanceComparisonRequest(
            databases=["mongodb", "neo4j", "postgres", "cassandra", "redis", "qdrant"],
            period_hours=24
        )
        
        optimization_request = OptimizationReportRequest(
            databases=["mongodb", "neo4j", "postgres", "cassandra", "redis", "qdrant"]
        )
        
        # Test that all databases are included
        expected_databases = ["mongodb", "neo4j", "postgres", "cassandra", "redis", "qdrant"]
        
        self.assertEqual(set(analysis_request.databases), set(expected_databases))
        self.assertEqual(set(performance_request.databases), set(expected_databases))
        self.assertEqual(set(optimization_request.databases), set(expected_databases))

    def test_shared_analyzer_error_handling(self):
        """Test that shared analyzer API handles errors gracefully"""
        from infrastructure.database.shared.analyzer_api import (
            _analyze_mongodb_query, _analyze_neo4j_query, _analyze_postgres_query,
            _analyze_cassandra_query, _analyze_redis_query, _analyze_qdrant_query
        )
        
        analysis_functions = [
            _analyze_mongodb_query, _analyze_neo4j_query, _analyze_postgres_query,
            _analyze_cassandra_query, _analyze_redis_query, _analyze_qdrant_query
        ]
        
        # Test that all functions handle exceptions gracefully
        for func in analysis_functions:
            try:
                result = func("SELECT * FROM users")
                # Should return a dict with error information
                self.assertIsInstance(result, dict)
                if "error" in result:
                    self.assertIsInstance(result["error"], str)
            except Exception as e:
                self.fail(f"Function {func.__name__} raised an exception: {e}")


if __name__ == '__main__':
    unittest.main()

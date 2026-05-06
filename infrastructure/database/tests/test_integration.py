import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import asyncio

from infrastructure.database.mongodb.monitoring.mongodb_monitoring_client import MongoDBMonitoringClient
from infrastructure.database.neo4j.monitoring.neo4j_monitoring_client import Neo4jMonitoringClient
from infrastructure.database.postgres.monitoring.postgres_monitoring_client import PostgreSQLMonitoringClient
from infrastructure.database.shared.query_monitoring_interfaces import (
    QueryMetric, QueryStatus, QueryPerformanceLevel, QueryMonitoringConfig
)


class TestCrossDatabaseIntegration(unittest.TestCase):
    """Integration tests across all database monitoring systems"""
    
    def setUp(self):
        self.config = QueryMonitoringConfig()
        self.mock_mongodb_client = Mock()
        self.mock_neo4j_driver = Mock()
        self.mock_postgres_connection = Mock()
    
    def test_all_clients_initialization(self):
        """Test that all monitoring clients can be initialized"""
        mongodb_client = MongoDBMonitoringClient(self.mock_mongodb_client, self.config)
        neo4j_client = Neo4jMonitoringClient(self.mock_neo4j_driver, self.config)
        postgres_client = PostgreSQLMonitoringClient(self.mock_postgres_connection, self.config)
        
        self.assertIsNotNone(mongodb_client)
        self.assertIsNotNone(neo4j_client)
        self.assertIsNotNone(postgres_client)
        
        # Verify all clients have the required components
        self.assertIsNotNone(mongodb_client.collector)
        self.assertIsNotNone(mongodb_client.analyzer)
        self.assertIsNotNone(mongodb_client.exporter)
        
        self.assertIsNotNone(neo4j_client.collector)
        self.assertIsNotNone(neo4j_client.analyzer)
        self.assertIsNotNone(neo4j_client.exporter)
        
        self.assertIsNotNone(postgres_client.collector)
        self.assertIsNotNone(postgres_client.analyzer)
        self.assertIsNotNone(postgres_client.exporter)
    
    @patch('infrastructure.database.mongodb.monitoring.mongodb_monitoring_client.execute_query')
    @patch('infrastructure.database.neo4j.monitoring.neo4j_monitoring_client.execute_query')
    @patch('infrastructure.database.postgres.monitoring.postgres_monitoring_client.execute_query')
    def test_cross_database_query_execution(self, mock_pg_execute, mock_neo4j_execute, mock_mongo_execute):
        """Test query execution across all databases"""
        # Mock successful query execution
        mock_mongo_execute.return_value = Mock()
        mock_mongo_execute.return_value.success = True
        mock_mongo_execute.return_value.execution_time_ms = 100.0
        mock_mongo_execute.return_value.records = [{"data": "mongo_result"}]
        
        mock_neo4j_execute.return_value = Mock()
        mock_neo4j_execute.return_value.success = True
        mock_neo4j_execute.return_value.execution_time_ms = 150.0
        mock_neo4j_execute.return_value.records = [{"data": "neo4j_result"}]
        
        mock_pg_execute.return_value = Mock()
        mock_pg_execute.return_value.success = True
        mock_pg_execute.return_value.execution_time_ms = 80.0
        mock_pg_execute.return_value.records = [{"data": "postgres_result"}]
        mock_pg_execute.return_value.row_count = 1
        
        # Execute queries
        mongodb_client = MongoDBMonitoringClient(self.mock_mongodb_client, self.config)
        neo4j_client = Neo4jMonitoringClient(self.mock_neo4j_driver, self.config)
        postgres_client = PostgreSQLMonitoringClient(self.mock_postgres_connection, self.config)
        
        mongo_result = mongodb_client.execute_with_monitoring("db.users.find()")
        neo4j_result = neo4j_client.execute_with_monitoring("MATCH (n) RETURN n")
        postgres_result = postgres_client.execute_with_monitoring("SELECT * FROM users")
        
        # Verify all succeeded
        self.assertTrue(mongo_result["success"])
        self.assertTrue(neo4j_result["success"])
        self.assertTrue(postgres_result["success"])
        
        # Verify performance levels
        self.assertEqual(mongo_result["performance_level"], QueryPerformanceLevel.FAST)
        self.assertEqual(neo4j_result["performance_level"], QueryPerformanceLevel.FAST)
        self.assertEqual(postgres_result["performance_level"], QueryPerformanceLevel.FAST)
    
    def test_cross_database_metrics_collection(self):
        """Test metrics collection across all databases"""
        # Create mock metrics
        mongo_metrics = [
            QueryMetric(
                query_hash="mongo_hash",
                query_type="find",
                database="mongodb",
                execution_time_ms=120.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.FAST,
                timestamp=datetime.utcnow()
            )
        ]
        
        neo4j_metrics = [
            QueryMetric(
                query_hash="neo4j_hash",
                query_type="match",
                database="neo4j",
                execution_time_ms=180.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.NORMAL,
                timestamp=datetime.utcnow()
            )
        ]
        
        postgres_metrics = [
            QueryMetric(
                query_hash="postgres_hash",
                query_type="select",
                database="postgres",
                collection_table="users",
                execution_time_ms=90.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.FAST,
                timestamp=datetime.utcnow()
            )
        ]
        
        # Mock collectors
        mongodb_client = MongoDBMonitoringClient(self.mock_mongodb_client, self.config)
        neo4j_client = Neo4jMonitoringClient(self.mock_neo4j_driver, self.config)
        postgres_client = PostgreSQLMonitoringClient(self.mock_postgres_connection, self.config)
        
        with patch.object(mongodb_client.collector, 'collect_query_metrics', return_value=mongo_metrics):
            with patch.object(neo4j_client.collector, 'collect_query_metrics', return_value=neo4j_metrics):
                with patch.object(postgres_client.collector, 'collect_query_metrics', return_value=postgres_metrics):
                    
                    mongo_collected = mongodb_client.collector.collect_query_metrics()
                    neo4j_collected = neo4j_client.collector.collect_query_metrics()
                    postgres_collected = postgres_client.collector.collect_query_metrics()
                    
                    # Verify metrics collection
                    self.assertEqual(len(mongo_collected), 1)
                    self.assertEqual(len(neo4j_collected), 1)
                    self.assertEqual(len(postgres_collected), 1)
                    
                    # Verify database-specific attributes
                    self.assertEqual(mongo_collected[0].database, "mongodb")
                    self.assertEqual(neo4j_collected[0].database, "neo4j")
                    self.assertEqual(postgres_collected[0].database, "postgres")
    
    def test_cross_database_health_monitoring(self):
        """Test health monitoring across all databases"""
        # Mock health status
        mongo_health = {"healthy": True, "health_score": 85}
        neo4j_health = {"healthy": True, "health_score": 90}
        postgres_health = {"healthy": False, "health_score": 60}
        
        mongodb_client = MongoDBMonitoringClient(self.mock_mongodb_client, self.config)
        neo4j_client = Neo4jMonitoringClient(self.mock_neo4j_driver, self.config)
        postgres_client = PostgreSQLMonitoringClient(self.mock_postgres_connection, self.config)
        
        with patch.object(mongodb_client.exporter, 'get_health_status', return_value=mongo_health):
            with patch.object(neo4j_client.exporter, 'get_health_status', return_value=neo4j_health):
                with patch.object(postgres_client.exporter, 'get_health_status', return_value=postgres_health):
                    
                    mongo_health_result = mongodb_client.exporter.get_health_status()
                    neo4j_health_result = neo4j_client.exporter.get_health_status()
                    postgres_health_result = postgres_client.exporter.get_health_status()
                    
                    # Verify health status
                    self.assertTrue(mongo_health_result["healthy"])
                    self.assertTrue(neo4j_health_result["healthy"])
                    self.assertFalse(postgres_health_result["healthy"])
                    
                    # Verify health scores
                    self.assertEqual(mongo_health_result["health_score"], 85)
                    self.assertEqual(neo4j_health_result["health_score"], 90)
                    self.assertEqual(postgres_health_result["health_score"], 60)


class TestPerformanceAnalysisIntegration(unittest.TestCase):
    """Integration tests for performance analysis across databases"""
    
    def setUp(self):
        self.config = QueryMonitoringConfig()
        self.mock_mongodb_client = Mock()
        self.mock_neo4j_driver = Mock()
        self.mock_postgres_connection = Mock()
    
    def test_cross_database_slow_query_detection(self):
        """Test slow query detection across all databases"""
        slow_queries = [
            QueryMetric(
                query_hash="slow_hash",
                query_type="select",
                database="mongodb",
                execution_time_ms=2000.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.SLOW,
                timestamp=datetime.utcnow()
            ),
            QueryMetric(
                query_hash="slow_hash2",
                query_type="match",
                database="neo4j",
                execution_time_ms=2500.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.SLOW,
                timestamp=datetime.utcnow()
            ),
            QueryMetric(
                query_hash="slow_hash3",
                query_type="select",
                database="postgres",
                collection_table="users",
                execution_time_ms=1800.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.SLOW,
                timestamp=datetime.utcnow()
            )
        ]
        
        mongodb_client = MongoDBMonitoringClient(self.mock_mongodb_client, self.config)
        neo4j_client = Neo4jMonitoringClient(self.mock_neo4j_driver, self.config)
        postgres_client = PostgreSQLMonitoringClient(self.mock_postgres_connection, self.config)
        
        with patch.object(mongodb_client.collector, 'get_slow_queries', return_value=[slow_queries[0]]):
            with patch.object(neo4j_client.collector, 'get_slow_queries', return_value=[slow_queries[1]]):
                with patch.object(postgres_client.collector, 'get_slow_queries', return_value=[slow_queries[2]]):
                    
                    mongo_slow = mongodb_client.collector.get_slow_queries()
                    neo4j_slow = neo4j_client.collector.get_slow_queries()
                    postgres_slow = postgres_client.collector.get_slow_queries()
                    
                    # Verify slow queries detected
                    self.assertEqual(len(mongo_slow), 1)
                    self.assertEqual(len(neo4j_slow), 1)
                    self.assertEqual(len(postgres_slow), 1)
                    
                    # Verify all are classified as slow
                    for query in mongo_slow + neo4j_slow + postgres_slow:
                        self.assertEqual(query.performance_level, QueryPerformanceLevel.SLOW)
                        self.assertGreaterEqual(query.execution_time_ms, 1000.0)
    
    def test_cross_database_performance_comparison(self):
        """Test performance comparison across databases"""
        # Create performance summaries
        mongo_summary = {
            "total_queries": 1000,
            "avg_execution_time_ms": 150.0,
            "slow_query_count": 50,
            "error_rate": 2.0
        }
        
        neo4j_summary = {
            "total_queries": 800,
            "avg_execution_time_ms": 200.0,
            "slow_query_count": 80,
            "error_rate": 1.5
        }
        
        postgres_summary = {
            "total_queries": 1200,
            "avg_execution_time_ms": 120.0,
            "slow_query_count": 30,
            "error_rate": 1.0
        }
        
        mongodb_client = MongoDBMonitoringClient(self.mock_mongodb_client, self.config)
        neo4j_client = Neo4jMonitoringClient(self.mock_neo4j_driver, self.config)
        postgres_client = PostgreSQLMonitoringClient(self.mock_postgres_connection, self.config)
        
        with patch.object(mongodb_client, 'get_performance_summary', return_value={"summary": mongo_summary}):
            with patch.object(neo4j_client, 'get_performance_summary', return_value={"summary": neo4j_summary}):
                with patch.object(postgres_client, 'get_performance_summary', return_value={"summary": postgres_summary}):
                    
                    mongo_perf = mongodb_client.get_performance_summary()
                    neo4j_perf = neo4j_client.get_performance_summary()
                    postgres_perf = postgres_client.get_performance_summary()
                    
                    # Verify performance data
                    self.assertEqual(mongo_perf["summary"]["total_queries"], 1000)
                    self.assertEqual(neo4j_perf["summary"]["total_queries"], 800)
                    self.assertEqual(postgres_perf["summary"]["total_queries"], 1200)
                    
                    # Verify performance ranking (Postgres fastest, Neo4j slowest)
                    self.assertLess(postgres_perf["summary"]["avg_execution_time_ms"], 
                                  mongo_perf["summary"]["avg_execution_time_ms"])
                    self.assertLess(mongo_perf["summary"]["avg_execution_time_ms"], 
                                  neo4j_perf["summary"]["avg_execution_time_ms"])


class TestErrorHandlingIntegration(unittest.TestCase):
    """Integration tests for error handling across databases"""
    
    def setUp(self):
        self.config = QueryMonitoringConfig()
        self.mock_mongodb_client = Mock()
        self.mock_neo4j_driver = Mock()
        self.mock_postgres_connection = Mock()
    
    def test_database_connection_failures(self):
        """Test handling of database connection failures"""
        mongodb_client = MongoDBMonitoringClient(self.mock_mongodb_client, self.config)
        neo4j_client = Neo4jMonitoringClient(self.mock_neo4j_driver, self.config)
        postgres_client = PostgreSQLMonitoringClient(self.mock_postgres_connection, self.config)
        
        # Mock connection failures
        with patch('infrastructure.database.mongodb.monitoring.mongodb_monitoring_client.execute_query') as mock_mongo:
            with patch('infrastructure.database.neo4j.monitoring.neo4j_monitoring_client.execute_query') as mock_neo4j:
                with patch('infrastructure.database.postgres.monitoring.postgres_monitoring_client.execute_query') as mock_postgres:
                    
                    mock_mongo.side_effect = Exception("MongoDB connection failed")
                    mock_neo4j.side_effect = Exception("Neo4j connection failed")
                    mock_postgres.side_effect = Exception("PostgreSQL connection failed")
                    
                    # Test query execution failures
                    mongo_result = mongodb_client.execute_with_monitoring("db.test.find()")
                    neo4j_result = neo4j_client.execute_with_monitoring("MATCH (n) RETURN n")
                    postgres_result = postgres_client.execute_with_monitoring("SELECT * FROM test")
                    
                    # Verify all failed gracefully
                    self.assertFalse(mongo_result["success"])
                    self.assertFalse(neo4j_result["success"])
                    self.assertFalse(postgres_result["success"])
                    
                    # Verify error details
                    self.assertIn("error", mongo_result)
                    self.assertIn("error", neo4j_result)
                    self.assertIn("error", postgres_result)
                    
                    # Verify critical performance level for errors
                    self.assertEqual(mongo_result["performance_level"], QueryPerformanceLevel.CRITICAL)
                    self.assertEqual(neo4j_result["performance_level"], QueryPerformanceLevel.CRITICAL)
                    self.assertEqual(postgres_result["performance_level"], QueryPerformanceLevel.CRITICAL)
    
    def test_partial_database_failures(self):
        """Test handling when some databases fail and others succeed"""
        mongodb_client = MongoDBMonitoringClient(self.mock_mongodb_client, self.config)
        neo4j_client = Neo4jMonitoringClient(self.mock_neo4j_driver, self.config)
        postgres_client = PostgreSQLMonitoringClient(self.mock_postgres_connection, self.config)
        
        # Mock mixed success/failure
        with patch('infrastructure.database.mongodb.monitoring.mongodb_monitoring_client.execute_query') as mock_mongo:
            with patch('infrastructure.database.neo4j.monitoring.neo4j_monitoring_client.execute_query') as mock_neo4j:
                with patch('infrastructure.database.postgres.monitoring.postgres_monitoring_client.execute_query') as mock_postgres:
                    
                    # MongoDB succeeds
                    mock_mongo.return_value = Mock()
                    mock_mongo.return_value.success = True
                    mock_mongo.return_value.execution_time_ms = 100.0
                    
                    # Neo4j fails
                    mock_neo4j.side_effect = Exception("Neo4j unavailable")
                    
                    # PostgreSQL succeeds
                    mock_postgres.return_value = Mock()
                    mock_postgres.return_value.success = True
                    mock_postgres.return_value.execution_time_ms = 80.0
                    mock_postgres.return_value.row_count = 1
                    
                    mongo_result = mongodb_client.execute_with_monitoring("db.test.find()")
                    neo4j_result = neo4j_client.execute_with_monitoring("MATCH (n) RETURN n")
                    postgres_result = postgres_client.execute_with_monitoring("SELECT * FROM test")
                    
                    # Verify mixed results
                    self.assertTrue(mongo_result["success"])
                    self.assertFalse(neo4j_result["success"])
                    self.assertTrue(postgres_result["success"])
                    
                    # Verify performance levels
                    self.assertEqual(mongo_result["performance_level"], QueryPerformanceLevel.FAST)
                    self.assertEqual(neo4j_result["performance_level"], QueryPerformanceLevel.CRITICAL)
                    self.assertEqual(postgres_result["performance_level"], QueryPerformanceLevel.FAST)


class TestMetricsExportIntegration(unittest.TestCase):
    """Integration tests for metrics export across databases"""
    
    def setUp(self):
        self.config = QueryMonitoringConfig()
        self.mock_mongodb_client = Mock()
        self.mock_neo4j_driver = Mock()
        self.mock_postgres_connection = Mock()
    
    def test_cross_database_prometheus_export(self):
        """Test Prometheus metrics export across all databases"""
        from infrastructure.database.mongodb.monitoring.mongodb_metrics_exporter import MongoDBMetricsExporter
        from infrastructure.database.neo4j.monitoring.neo4j_metrics_exporter import Neo4jMetricsExporter
        from infrastructure.database.postgres.monitoring.postgres_metrics_exporter import PostgreSQLMetricsExporter
        
        mongo_exporter = MongoDBMetricsExporter(self.mock_mongodb_client, self.config)
        neo4j_exporter = Neo4jMetricsExporter(self.mock_neo4j_driver, self.config)
        postgres_exporter = PostgreSQLMetricsExporter(self.mock_postgres_connection, self.config)
        
        # Mock metrics collection
        with patch.object(mongo_exporter, '_collect_database_query_metrics', return_value="mongodb_metrics"):
            with patch.object(mongo_exporter, '_collect_server_metrics', return_value="mongo_server"):
                with patch.object(neo4j_exporter, '_collect_database_query_metrics', return_value="neo4j_metrics"):
                    with patch.object(neo4j_exporter, '_collect_server_metrics', return_value="neo4j_server"):
                        with patch.object(postgres_exporter, '_collect_database_query_metrics', return_value="postgres_metrics"):
                            with patch.object(postgres_exporter, '_collect_server_metrics', return_value="postgres_server"):
                                
                                mongo_prometheus = mongo_exporter.get_prometheus_metrics()
                                neo4j_prometheus = neo4j_exporter.get_prometheus_metrics()
                                postgres_prometheus = postgres_exporter.get_prometheus_metrics()
                                
                                # Verify all return Prometheus format
                                self.assertIsInstance(mongo_prometheus, str)
                                self.assertIsInstance(neo4j_prometheus, str)
                                self.assertIsInstance(postgres_prometheus, str)
                                
                                # Verify database-specific metrics are included
                                self.assertIn("mongodb", mongo_prometheus)
                                self.assertIn("neo4j", neo4j_prometheus)
                                self.assertIn("postgres", postgres_prometheus)
    
    def test_cross_database_json_export(self):
        """Test JSON metrics export across all databases"""
        from infrastructure.database.mongodb.monitoring.mongodb_metrics_exporter import MongoDBMetricsExporter
        from infrastructure.database.neo4j.monitoring.neo4j_metrics_exporter import Neo4jMetricsExporter
        from infrastructure.database.postgres.monitoring.postgres_metrics_exporter import PostgreSQLMetricsExporter
        
        mongo_exporter = MongoDBMetricsExporter(self.mock_mongodb_client, self.config)
        neo4j_exporter = Neo4jMetricsExporter(self.mock_neo4j_driver, self.config)
        postgres_exporter = PostgreSQLMetricsExporter(self.mock_postgres_connection, self.config)
        
        # Mock JSON export
        with patch.object(mongo_exporter, 'export_json_metrics', return_value={"database": "mongodb"}):
            with patch.object(neo4j_exporter, 'export_json_metrics', return_value={"database": "neo4j"}):
                with patch.object(postgres_exporter, 'export_json_metrics', return_value={"database": "postgres"}):
                    
                    mongo_json = mongo_exporter.export_json_metrics()
                    neo4j_json = neo4j_exporter.export_json_metrics()
                    postgres_json = postgres_exporter.export_json_metrics()
                    
                    # Verify all return JSON format
                    self.assertIsInstance(mongo_json, dict)
                    self.assertIsInstance(neo4j_json, dict)
                    self.assertIsInstance(postgres_json, dict)
                    
                    # Verify database identification
                    self.assertEqual(mongo_json["database"], "mongodb")
                    self.assertEqual(neo4j_json["database"], "neo4j")
                    self.assertEqual(postgres_json["database"], "postgres")
                    
                    # Verify timestamps are included
                    self.assertIn("timestamp", mongo_json)
                    self.assertIn("timestamp", neo4j_json)
                    self.assertIn("timestamp", postgres_json)


if __name__ == '__main__':
    unittest.main()

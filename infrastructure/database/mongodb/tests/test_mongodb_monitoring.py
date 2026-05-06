import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from infrastructure.database.mongodb.monitoring.mongodb_query_collector import MongoDBQueryCollector
from infrastructure.database.mongodb.monitoring.mongodb_query_analyzer import MongoDBQueryAnalyzer
from infrastructure.database.mongodb.monitoring.mongodb_metrics_exporter import MongoDBMetricsExporter
from infrastructure.database.mongodb.monitoring.mongodb_monitoring_client import MongoDBMonitoringClient
from infrastructure.database.shared.query_monitoring_interfaces import (
    QueryMetric, QueryStatus, QueryPerformanceLevel, QueryMonitoringConfig
)


class TestMongoDBQueryCollector(unittest.TestCase):
    def setUp(self):
        self.mock_client = Mock()
        self.config = QueryMonitoringConfig()
        self.collector = MongoDBQueryCollector(self.mock_client, self.config)
    
    @patch('infrastructure.database.mongodb.monitoring.mongodb_query_collector.MongoDBQueryCollector._get_system_profile')
    @patch('infrastructure.database.mongodb.monitoring.mongodb_query_collector.MongoDBQueryCollector._get_recent_operations')
    def test_collect_query_metrics(self, mock_recent_ops, mock_system_profile):
        mock_system_profile.return_value = []
        mock_recent_ops.return_value = []
        
        metrics = self.collector.collect_query_metrics(limit=10)
        
        self.assertIsInstance(metrics, list)
        mock_system_profile.assert_called_once()
        mock_recent_ops.assert_called_once()
    
    def test_get_slow_queries(self):
        with patch.object(self.collector, 'collect_query_metrics') as mock_collect:
            mock_metrics = [
                QueryMetric(
                    query_hash="hash1",
                    query_type="find",
                    database="mongodb",
                    execution_time_ms=1500.0,
                    status=QueryStatus.SUCCESS,
                    performance_level=QueryPerformanceLevel.SLOW,
                    timestamp=datetime.utcnow()
                ),
                QueryMetric(
                    query_hash="hash2",
                    query_type="insert",
                    database="mongodb",
                    execution_time_ms=500.0,
                    status=QueryStatus.SUCCESS,
                    performance_level=QueryPerformanceLevel.NORMAL,
                    timestamp=datetime.utcnow()
                )
            ]
            mock_collect.return_value = mock_metrics
            
            slow_queries = self.collector.get_slow_queries(threshold_ms=1000.0, limit=10)
            
            self.assertEqual(len(slow_queries), 1)
            self.assertEqual(slow_queries[0].query_hash, "hash1")
    
    def test_record_query_execution(self):
        metric = QueryMetric(
            query_hash="test_hash",
            query_type="find",
            database="mongodb",
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
        with patch('infrastructure.database.mongodb.monitoring.mongodb_query_collector.TimeWindowCalculator') as mock_time:
            mock_time.get_time_windows.return_value = {
                'period_start': datetime.utcnow() - timedelta(hours=1),
                'period_end': datetime.utcnow()
            }
            
            summary = self.collector.get_performance_summary(period_minutes=60)
            
            self.assertIsInstance(summary, dict)


class TestMongoDBQueryAnalyzer(unittest.TestCase):
    def setUp(self):
        self.mock_client = Mock()
        self.analyzer = MongoDBQueryAnalyzer(self.mock_client)
    
    def test_analyze_query(self):
        with patch.object(self.analyzer, 'explain_query') as mock_explain:
            mock_explain.return_value = {"plan": {}}
            
            result = self.analyzer.analyze_query("db.users.find()", "test_db")
            
            self.assertIsNotNone(result)
            self.assertEqual(result.query_text, "db.users.find()")
            mock_explain.assert_called_once_with("db.users.find()", "test_db")
    
    def test_explain_query(self):
        with patch('infrastructure.database.mongodb.monitoring.mongodb_query_analyzer.execute_query') as mock_execute:
            mock_execute.return_value = Mock()
            mock_execute.return_value.success = True
            mock_execute.return_value.records = [{"plan": "test_plan"}]
            
            result = self.analyzer.explain_query("db.users.find()", "test_db")
            
            self.assertIsInstance(result, dict)
            mock_execute.assert_called_once()
    
    def test_suggest_indexes(self):
        with patch.object(self.analyzer, 'explain_query') as mock_explain:
            mock_explain.return_value = {"plan": {"collectionScan": True}}
            
            suggestions = self.analyzer.suggest_indexes("db.users.find()", "test_db")
            
            self.assertIsInstance(suggestions, list)
    
    def test_generate_performance_report(self):
        with patch.object(self.analyzer, '_get_database_name') as mock_db_name:
            mock_db_name.return_value = "test_db"
            
            period_start = datetime.utcnow() - timedelta(hours=24)
            period_end = datetime.utcnow()
            
            report = self.analyzer.generate_performance_report("test_db", period_start, period_end)
            
            self.assertIsNotNone(report)
            self.assertEqual(report.database, "test_db")


class TestMongoDBMetricsExporter(unittest.TestCase):
    def setUp(self):
        self.mock_client = Mock()
        self.exporter = MongoDBMetricsExporter(self.mock_client)
    
    def test_export_query_metrics(self):
        metrics = [
            QueryMetric(
                query_hash="hash1",
                query_type="find",
                database="mongodb",
                execution_time_ms=100.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.FAST,
                timestamp=datetime.utcnow()
            )
        ]
        
        result = self.exporter.export_query_metrics(metrics)
        
        self.assertIsInstance(result, str)
        self.assertIn("mongodb", result)
    
    def test_export_database_metrics(self):
        metrics = {
            "collections": 10,
            "data_size": 1024000,
            "storage_size": 2048000
        }
        
        result = self.exporter.export_database_metrics("test_db", metrics)
        
        self.assertIsInstance(result, str)
        self.assertIn("test_db", result)
    
    def test_get_prometheus_metrics(self):
        with patch.object(self.exporter, '_collect_database_query_metrics') as mock_db_metrics:
            with patch.object(self.exporter, '_collect_server_metrics') as mock_server_metrics:
                mock_db_metrics.return_value = "db_metrics"
                mock_server_metrics.return_value = "server_metrics"
                
                result = self.exporter.get_prometheus_metrics()
                
                self.assertIsInstance(result, str)
                self.assertIn("db_metrics", result)
                self.assertIn("server_metrics", result)
    
    def test_get_health_status(self):
        with patch('infrastructure.database.mongodb.monitoring.mongodb_metrics_exporter.execute_query') as mock_execute:
            mock_execute.return_value = Mock()
            mock_execute.return_value.success = True
            mock_execute.return_value.records = [{"uptime": 1000}]
            
            health = self.exporter.get_health_status()
            
            self.assertIsInstance(health, dict)
            self.assertIn("healthy", health)
            self.assertIn("health_score", health)


class TestMongoDBMonitoringClient(unittest.TestCase):
    def setUp(self):
        self.mock_client = Mock()
        self.config = QueryMonitoringConfig()
        self.monitoring_client = MongoDBMonitoringClient(self.mock_client, self.config)
    
    def test_execute_with_monitoring(self):
        with patch('infrastructure.database.mongodb.monitoring.mongodb_monitoring_client.execute_query') as mock_execute:
            mock_execute.return_value = Mock()
            mock_execute.return_value.success = True
            mock_execute.return_value.records = [{"data": "test"}]
            mock_execute.return_value.execution_time_ms = 100.0
            
            result = self.monitoring_client.execute_with_monitoring("db.users.find()")
            
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


class TestMongoDBIntegration(unittest.TestCase):
    """Integration tests for MongoDB monitoring components"""
    
    def setUp(self):
        self.mock_client = Mock()
        self.config = QueryMonitoringConfig()
    
    def test_end_to_end_monitoring_flow(self):
        collector = MongoDBQueryCollector(self.mock_client, self.config)
        analyzer = MongoDBQueryAnalyzer(self.mock_client)
        exporter = MongoDBMetricsExporter(self.mock_client)
        client = MongoDBMonitoringClient(self.mock_client, self.config)
        
        with patch('infrastructure.database.mongodb.monitoring.mongodb_query_collector.execute_query') as mock_execute:
            mock_execute.return_value = Mock()
            mock_execute.return_value.success = True
            mock_execute.return_value.records = [{"data": "test"}]
            mock_execute.return_value.execution_time_ms = 1500.0
            
            result = client.execute_with_monitoring("db.users.find()")
            
            self.assertTrue(result["success"])
            self.assertEqual(result["performance_level"], QueryPerformanceLevel.SLOW)
    
    def test_error_handling(self):
        client = MongoDBMonitoringClient(self.mock_client, self.config)
        
        with patch('infrastructure.database.mongodb.monitoring.mongodb_monitoring_client.execute_query') as mock_execute:
            mock_execute.side_effect = Exception("Database error")
            
            result = client.execute_with_monitoring("db.users.find()")
            
            self.assertFalse(result["success"])
            self.assertIn("error", result)
            self.assertEqual(result["performance_level"], QueryPerformanceLevel.CRITICAL)


if __name__ == '__main__':
    unittest.main()

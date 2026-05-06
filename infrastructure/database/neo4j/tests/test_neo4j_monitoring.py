import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from infrastructure.database.neo4j.monitoring.neo4j_query_collector import Neo4jQueryCollector
from infrastructure.database.neo4j.monitoring.neo4j_query_analyzer import Neo4jQueryAnalyzer
from infrastructure.database.neo4j.monitoring.neo4j_metrics_exporter import Neo4jMetricsExporter
from infrastructure.database.neo4j.monitoring.neo4j_monitoring_client import Neo4jMonitoringClient
from infrastructure.database.shared.query_monitoring_interfaces import (
    QueryMetric, QueryStatus, QueryPerformanceLevel, QueryMonitoringConfig
)


class TestNeo4jQueryCollector(unittest.TestCase):
    def setUp(self):
        self.mock_driver = Mock()
        self.config = QueryMonitoringConfig()
        self.collector = Neo4jQueryCollector(self.mock_driver, self.config)
    
    @patch('infrastructure.database.neo4j.monitoring.neo4j_query_collector.execute_query')
    def test_collect_query_metrics(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = []
        
        metrics = self.collector.collect_query_metrics(limit=10)
        
        self.assertIsInstance(metrics, list)
    
    def test_get_slow_queries(self):
        with patch.object(self.collector, 'collect_query_metrics') as mock_collect:
            mock_metrics = [
                QueryMetric(
                    query_hash="hash1",
                    query_type="match",
                    database="neo4j",
                    execution_time_ms=1500.0,
                    status=QueryStatus.SUCCESS,
                    performance_level=QueryPerformanceLevel.SLOW,
                    timestamp=datetime.utcnow()
                ),
                QueryMetric(
                    query_hash="hash2",
                    query_type="create",
                    database="neo4j",
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
            query_type="match",
            database="neo4j",
            execution_time_ms=100.0,
            status=QueryStatus.SUCCESS,
            performance_level=QueryPerformanceLevel.FAST,
            timestamp=datetime.utcnow()
        )
        
        initial_count = len(self.collector._query_metrics_store)
        self.collector.record_query_execution(metric)
        
        self.assertEqual(len(self.collector._query_metrics_store), initial_count + 1)
        self.assertIn(metric, self.collector._query_metrics_store)
    
    @patch('infrastructure.database.neo4j.monitoring.neo4j_query_collector.execute_query')
    def test_get_database_metrics(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = [{"node_count": 100}]
        
        metrics = self.collector.get_database_metrics()
        
        self.assertIsInstance(metrics, dict)
    
    def test_identify_index_gaps(self):
        with patch.object(self.collector, 'get_slow_queries') as mock_slow:
            mock_slow.return_value = [
                QueryMetric(
                    query_hash="hash1",
                    query_type="match",
                    database="neo4j",
                    execution_time_ms=1500.0,
                    status=QueryStatus.SUCCESS,
                    performance_level=QueryPerformanceLevel.SLOW,
                    timestamp=datetime.utcnow()
                )
            ]
            
            gaps = self.collector.identify_index_gaps()
            
            self.assertIsInstance(gaps, list)


class TestNeo4jQueryAnalyzer(unittest.TestCase):
    def setUp(self):
        self.mock_driver = Mock()
        self.analyzer = Neo4jQueryAnalyzer(self.mock_driver)
    
    def test_analyze_query(self):
        with patch.object(self.analyzer, 'explain_query') as mock_explain:
            mock_explain.return_value = {"plan": {}, "success": True}
            
            result = self.analyzer.analyze_query("MATCH (n) RETURN n", "neo4j")
            
            self.assertIsNotNone(result)
            self.assertEqual(result.query_text, "MATCH (n) RETURN n")
            mock_explain.assert_called_once_with("MATCH (n) RETURN n", "neo4j")
    
    @patch('infrastructure.database.neo4j.monitoring.neo4j_query_analyzer.execute_query')
    def test_explain_query(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = [{"plan": "test_plan"}]
        
        result = self.analyzer.explain_query("MATCH (n) RETURN n", "neo4j")
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("success", False))
    
    def test_suggest_indexes(self):
        with patch.object(self.analyzer, 'explain_query') as mock_explain:
            mock_explain.return_value = {"plan": {"collectionScan": True}}
            
            suggestions = self.analyzer.suggest_indexes("MATCH (n:User) RETURN n", "neo4j")
            
            self.assertIsInstance(suggestions, list)
    
    def test_generate_performance_report(self):
        with patch.object(self.analyzer, '_get_database_name') as mock_db_name:
            mock_db_name.return_value = "neo4j"
            
            period_start = datetime.utcnow() - timedelta(hours=24)
            period_end = datetime.utcnow()
            
            report = self.analyzer.generate_performance_report("neo4j", period_start, period_end)
            
            self.assertIsNotNone(report)
            self.assertEqual(report.database, "neo4j")
    
    @patch('infrastructure.database.neo4j.monitoring.neo4j_query_analyzer.execute_query')
    def test_get_schema_analysis(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = [{"label": "User"}]
        
        analysis = self.analyzer.get_schema_analysis("neo4j")
        
        self.assertIsInstance(analysis, dict)
        self.assertTrue(analysis.get("success", False))
    
    def test_get_query_plan_analysis(self):
        with patch.object(self.analyzer, 'explain_query') as mock_explain:
            mock_explain.return_value = {"plan": {"operations": []}, "success": True}
            
            analysis = self.analyzer.get_query_plan_analysis("MATCH (n) RETURN n", "neo4j")
            
            self.assertIsInstance(analysis, dict)
            self.assertIn("query", analysis)
            self.assertIn("analysis", analysis)


class TestNeo4jMetricsExporter(unittest.TestCase):
    def setUp(self):
        self.mock_driver = Mock()
        self.exporter = Neo4jMetricsExporter(self.mock_driver)
    
    def test_export_query_metrics(self):
        metrics = [
            QueryMetric(
                query_hash="hash1",
                query_type="match",
                database="neo4j",
                execution_time_ms=100.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.FAST,
                timestamp=datetime.utcnow()
            )
        ]
        
        result = self.exporter.export_query_metrics(metrics)
        
        self.assertIsInstance(result, str)
        self.assertIn("neo4j", result)
    
    def test_export_database_metrics(self):
        metrics = {
            "node_count": 1000,
            "relationship_count": 2000,
            "label_count": 10
        }
        
        result = self.exporter.export_database_metrics("neo4j", metrics)
        
        self.assertIsInstance(result, str)
        self.assertIn("neo4j", result)
    
    @patch('infrastructure.database.neo4j.monitoring.neo4j_metrics_exporter.execute_query')
    def test_get_prometheus_metrics(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = [{"attributes": {"TotalMemory": 1024000}}]
        
        result = self.exporter.get_prometheus_metrics()
        
        self.assertIsInstance(result, str)
    
    @patch('infrastructure.database.neo4j.monitoring.neo4j_metrics_exporter.execute_query')
    def test_get_health_status(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = [{"test": 1}]
        
        health = self.exporter.get_health_status()
        
        self.assertIsInstance(health, dict)
        self.assertIn("healthy", health)
        self.assertIn("health_score", health)
    
    @patch('infrastructure.database.neo4j.monitoring.neo4j_metrics_exporter.execute_query')
    def test_export_json_metrics(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = [{"test": "data"}]
        
        metrics = self.exporter.export_json_metrics()
        
        self.assertIsInstance(metrics, dict)
        self.assertIn("database", metrics)
        self.assertIn("timestamp", metrics)


class TestNeo4jMonitoringClient(unittest.TestCase):
    def setUp(self):
        self.mock_driver = Mock()
        self.config = QueryMonitoringConfig()
        self.monitoring_client = Neo4jMonitoringClient(self.mock_driver, self.config)
    
    @patch('infrastructure.database.neo4j.monitoring.neo4j_monitoring_client.execute_query')
    def test_execute_with_monitoring(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = [{"data": "test"}]
        mock_execute.return_value.execution_time_ms = 100.0
        
        result = self.monitoring_client.execute_with_monitoring("MATCH (n) RETURN n")
        
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


class TestNeo4jIntegration(unittest.TestCase):
    """Integration tests for Neo4j monitoring components"""
    
    def setUp(self):
        self.mock_driver = Mock()
        self.config = QueryMonitoringConfig()
    
    @patch('infrastructure.database.neo4j.monitoring.neo4j_monitoring_client.execute_query')
    def test_end_to_end_monitoring_flow(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = [{"data": "test"}]
        mock_execute.return_value.execution_time_ms = 1500.0
        
        client = Neo4jMonitoringClient(self.mock_driver, self.config)
        result = client.execute_with_monitoring("MATCH (n) RETURN n")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["performance_level"], QueryPerformanceLevel.SLOW)
    
    @patch('infrastructure.database.neo4j.monitoring.neo4j_monitoring_client.execute_query')
    def test_error_handling(self, mock_execute):
        mock_execute.side_effect = Exception("Database error")
        
        client = Neo4jMonitoringClient(self.mock_driver, self.config)
        result = client.execute_with_monitoring("MATCH (n) RETURN n")
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertEqual(result["performance_level"], QueryPerformanceLevel.CRITICAL)


if __name__ == '__main__':
    unittest.main()

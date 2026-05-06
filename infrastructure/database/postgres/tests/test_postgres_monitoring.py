import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import psycopg2
from infrastructure.database.postgres.monitoring.postgres_query_collector import PostgreSQLQueryCollector
from infrastructure.database.postgres.monitoring.postgres_query_analyzer import PostgreSQLQueryAnalyzer
from infrastructure.database.postgres.monitoring.postgres_metrics_exporter import PostgreSQLMetricsExporter
from infrastructure.database.postgres.monitoring.postgres_monitoring_client import PostgreSQLMonitoringClient
from infrastructure.database.shared.query_monitoring_interfaces import (
    QueryMetric, QueryStatus, QueryPerformanceLevel, QueryMonitoringConfig
)


class TestPostgreSQLQueryCollector(unittest.TestCase):
    def setUp(self):
        self.mock_connection = Mock()
        self.config = QueryMonitoringConfig()
        self.collector = PostgreSQLQueryCollector(self.mock_connection, self.config)
    
    @patch('infrastructure.database.postgres.monitoring.postgres_query_collector.execute_query')
    def test_collect_query_metrics(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = []
        
        metrics = self.collector.collect_query_metrics(limit=10)
        
        self.assertIsInstance(metrics, list)
        mock_execute.assert_called()
    
    def test_get_slow_queries(self):
        with patch.object(self.collector, 'collect_query_metrics') as mock_collect:
            mock_metrics = [
                QueryMetric(
                    query_hash="hash1",
                    query_type="select",
                    database="postgres",
                    collection_table="users",
                    execution_time_ms=1500.0,
                    status=QueryStatus.SUCCESS,
                    performance_level=QueryPerformanceLevel.SLOW,
                    timestamp=datetime.utcnow()
                ),
                QueryMetric(
                    query_hash="hash2",
                    query_type="insert",
                    database="postgres",
                    collection_table="orders",
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
            query_type="select",
            database="postgres",
            collection_table="users",
            execution_time_ms=100.0,
            status=QueryStatus.SUCCESS,
            performance_level=QueryPerformanceLevel.FAST,
            timestamp=datetime.utcnow()
        )
        
        initial_count = len(self.collector._query_metrics_store)
        self.collector.record_query_execution(metric)
        
        self.assertEqual(len(self.collector._query_metrics_store), initial_count + 1)
        self.assertIn(metric, self.collector._query_metrics_store)
    
    @patch('infrastructure.database.postgres.monitoring.postgres_query_collector.execute_query')
    def test_get_database_metrics(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = [{"table_count": 10}]
        
        metrics = self.collector.get_database_metrics()
        
        self.assertIsInstance(metrics, dict)
        mock_execute.assert_called()
    
    @patch('infrastructure.database.postgres.monitoring.postgres_query_collector.execute_query')
    def test_get_table_statistics(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = [{"row_count": 1000}]
        
        stats = self.collector.get_table_statistics("users")
        
        self.assertIsInstance(stats, dict)
        mock_execute.assert_called()
    
    def test_identify_index_gaps(self):
        with patch.object(self.collector, 'get_slow_queries') as mock_slow:
            mock_slow.return_value = [
                QueryMetric(
                    query_hash="hash1",
                    query_type="select",
                    database="postgres",
                    collection_table="users",
                    execution_time_ms=1500.0,
                    status=QueryStatus.SUCCESS,
                    performance_level=QueryPerformanceLevel.SLOW,
                    timestamp=datetime.utcnow()
                )
            ]
            
            gaps = self.collector.identify_index_gaps()
            
            self.assertIsInstance(gaps, list)


class TestPostgreSQLQueryAnalyzer(unittest.TestCase):
    def setUp(self):
        self.mock_connection = Mock()
        self.analyzer = PostgreSQLQueryAnalyzer(self.mock_connection)
    
    def test_analyze_query(self):
        with patch.object(self.analyzer, 'explain_query') as mock_explain:
            mock_explain.return_value = {"plan": {}, "success": True}
            
            result = self.analyzer.analyze_query("SELECT * FROM users", "postgres")
            
            self.assertIsNotNone(result)
            self.assertEqual(result.query_text, "SELECT * FROM users")
            mock_explain.assert_called_once_with("SELECT * FROM users", "postgres")
    
    @patch('infrastructure.database.postgres.monitoring.postgres_query_analyzer.explain_query')
    def test_explain_query(self, mock_explain):
        mock_explain.return_value = {"plan": {"plan_text": "Seq Scan"}, "success": True}
        
        result = self.analyzer.explain_query("SELECT * FROM users", "postgres")
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("success", False))
    
    def test_suggest_indexes(self):
        with patch.object(self.analyzer, 'explain_query') as mock_explain:
            mock_explain.return_value = {"plan": {"plan_text": "Seq Scan on users"}}
            
            suggestions = self.analyzer.suggest_indexes("SELECT * FROM users WHERE id = 1", "postgres")
            
            self.assertIsInstance(suggestions, list)
    
    def test_generate_performance_report(self):
        with patch.object(self.analyzer, '_get_database_name') as mock_db_name:
            mock_db_name.return_value = "postgres"
            
            period_start = datetime.utcnow() - timedelta(hours=24)
            period_end = datetime.utcnow()
            
            report = self.analyzer.generate_performance_report("postgres", period_start, period_end)
            
            self.assertIsNotNone(report)
            self.assertEqual(report.database, "postgres")
    
    @patch('infrastructure.database.postgres.monitoring.postgres_query_analyzer.execute_query')
    def test_get_schema_analysis(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = [{"table_name": "users", "column_name": "id"}]
        
        analysis = self.analyzer.get_schema_analysis("postgres")
        
        self.assertIsInstance(analysis, dict)
        self.assertTrue(analysis.get("success", False))
    
    def test_get_query_plan_analysis(self):
        with patch.object(self.analyzer, 'explain_query') as mock_explain:
            mock_explain.return_value = {"plan": {"plan_text": "Index Scan"}, "success": True}
            
            analysis = self.analyzer.get_query_plan_analysis("SELECT * FROM users", "postgres")
            
            self.assertIsInstance(analysis, dict)
            self.assertIn("query", analysis)
            self.assertIn("analysis", analysis)


class TestPostgreSQLMetricsExporter(unittest.TestCase):
    def setUp(self):
        self.mock_connection = Mock()
        self.exporter = PostgreSQLMetricsExporter(self.mock_connection)
    
    def test_export_query_metrics(self):
        metrics = [
            QueryMetric(
                query_hash="hash1",
                query_type="select",
                database="postgres",
                collection_table="users",
                execution_time_ms=100.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.FAST,
                timestamp=datetime.utcnow()
            )
        ]
        
        result = self.exporter.export_query_metrics(metrics)
        
        self.assertIsInstance(result, str)
        self.assertIn("postgres", result)
    
    def test_export_database_metrics(self):
        metrics = {
            "table_count": 10,
            "index_count": 15,
            "active_connections": 5
        }
        
        result = self.exporter.export_database_metrics("postgres", metrics)
        
        self.assertIsInstance(result, str)
        self.assertIn("postgres", result)
    
    @patch('infrastructure.database.postgres.monitoring.postgres_metrics_exporter.execute_query')
    def test_get_prometheus_metrics(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = [{"total_connections": 10}]
        
        result = self.exporter.get_prometheus_metrics()
        
        self.assertIsInstance(result, str)
    
    @patch('infrastructure.database.postgres.monitoring.postgres_metrics_exporter.execute_query')
    def test_get_health_status(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = [{"test": 1}]
        
        health = self.exporter.get_health_status()
        
        self.assertIsInstance(health, dict)
        self.assertIn("healthy", health)
        self.assertIn("health_score", health)
    
    @patch('infrastructure.database.postgres.monitoring.postgres_metrics_exporter.execute_query')
    def test_export_json_metrics(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = [{"test": "data"}]
        
        metrics = self.exporter.export_json_metrics()
        
        self.assertIsInstance(metrics, dict)
        self.assertIn("database", metrics)
        self.assertIn("timestamp", metrics)


class TestPostgreSQLMonitoringClient(unittest.TestCase):
    def setUp(self):
        self.mock_connection = Mock()
        self.config = QueryMonitoringConfig()
        self.monitoring_client = PostgreSQLMonitoringClient(self.mock_connection, self.config)
    
    @patch('infrastructure.database.postgres.monitoring.postgres_monitoring_client.execute_query')
    def test_execute_with_monitoring(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = [{"data": "test"}]
        mock_execute.return_value.execution_time_ms = 100.0
        mock_execute.return_value.row_count = 1
        
        result = self.monitoring_client.execute_with_monitoring("SELECT * FROM users")
        
        self.assertTrue(result["success"])
        self.assertIn("execution_time_ms", result)
        self.assertIn("performance_level", result)
        self.assertEqual(result["row_count"], 1)
    
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
    
    @patch('infrastructure.database.postgres.monitoring.postgres_monitoring_client.PostgreSQLQueryCollector.get_table_statistics')
    def test_get_table_performance_analysis(self, mock_table_stats):
        mock_table_stats.return_value = {"row_count": 1000, "seq_scan": 50, "idx_scan": 10}
        
        analysis = self.monitoring_client.get_table_performance_analysis("users")
        
        self.assertIsInstance(analysis, dict)
        self.assertIn("table", analysis)
        self.assertIn("statistics", analysis)


class TestPostgreSQLIntegration(unittest.TestCase):
    """Integration tests for PostgreSQL monitoring components"""
    
    def setUp(self):
        self.mock_connection = Mock()
        self.config = QueryMonitoringConfig()
    
    @patch('infrastructure.database.postgres.monitoring.postgres_monitoring_client.execute_query')
    def test_end_to_end_monitoring_flow(self, mock_execute):
        mock_execute.return_value = Mock()
        mock_execute.return_value.success = True
        mock_execute.return_value.records = [{"data": "test"}]
        mock_execute.return_value.execution_time_ms = 1500.0
        mock_execute.return_value.row_count = 1
        
        client = PostgreSQLMonitoringClient(self.mock_connection, self.config)
        result = client.execute_with_monitoring("SELECT * FROM users")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["performance_level"], QueryPerformanceLevel.SLOW)
    
    @patch('infrastructure.database.postgres.monitoring.postgres_monitoring_client.execute_query')
    def test_error_handling(self, mock_execute):
        mock_execute.side_effect = Exception("Database error")
        
        client = PostgreSQLMonitoringClient(self.mock_connection, self.config)
        result = client.execute_with_monitoring("SELECT * FROM users")
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertEqual(result["performance_level"], QueryPerformanceLevel.CRITICAL)


class TestPostgreSQLQueryAnalysis(unittest.TestCase):
    """Specific tests for PostgreSQL query analysis features"""
    
    def setUp(self):
        self.mock_connection = Mock()
        self.analyzer = PostgreSQLQueryAnalyzer(self.mock_connection)
    
    def test_extract_query_type(self):
        self.assertEqual(self.analyzer._extract_query_type("SELECT * FROM users"), "select")
        self.assertEqual(self.analyzer._extract_query_type("INSERT INTO users"), "insert")
        self.assertEqual(self.analyzer._extract_query_type("UPDATE users SET"), "update")
        self.assertEqual(self.analyzer._extract_query_type("DELETE FROM users"), "delete")
        self.assertEqual(self.analyzer._extract_query_type("CREATE TABLE"), "create")
        self.assertEqual(self.analyzer._extract_query_type("UNKNOWN QUERY"), "unknown")
    
    def test_extract_table_from_query(self):
        self.assertEqual(self.analyzer._extract_table_from_query("SELECT * FROM users"), "users")
        self.assertEqual(self.analyzer._extract_table_from_query("INSERT INTO orders"), "orders")
        self.assertEqual(self.analyzer._extract_table_from_query("UPDATE products SET"), "products")
        self.assertEqual(self.analyzer._extract_table_from_query("DELETE FROM customers"), "customers")
        self.assertIsNone(self.analyzer._extract_table_from_query("INVALID QUERY"))
    
    def test_extract_where_columns(self):
        columns = self.analyzer._extract_where_columns("SELECT * FROM users WHERE id = 1 AND name = 'test'")
        self.assertIn("id", columns)
        self.assertIn("name", columns)
    
    def test_extract_join_columns(self):
        joins = self.analyzer._extract_join_columns("SELECT * FROM users u JOIN orders o ON u.id = o.user_id")
        self.assertEqual(len(joins), 1)
        self.assertEqual(joins[0]["table"], "orders")
        self.assertEqual(joins[0]["left_column"], "id")
        self.assertEqual(joins[0]["right_column"], "user_id")
    
    def test_has_aggregate(self):
        self.assertTrue(self.analyzer._has_aggregate("SELECT COUNT(*) FROM users"))
        self.assertTrue(self.analyzer._has_aggregate("SELECT SUM(price) FROM orders"))
        self.assertTrue(self.analyzer._has_aggregate("SELECT AVG(age) FROM users"))
        self.assertFalse(self.analyzer._has_aggregate("SELECT * FROM users"))
    
    def test_has_limit_clause(self):
        self.assertTrue(self.analyzer._has_limit_clause("SELECT * FROM users LIMIT 10"))
        self.assertFalse(self.analyzer._has_limit_clause("SELECT * FROM users"))
    
    def test_has_seq_scan(self):
        plan_with_seq = {"plan_text": "Seq Scan on users"}
        plan_without_seq = {"plan_text": "Index Scan on users"}
        
        self.assertTrue(self.analyzer._has_seq_scan(plan_with_seq))
        self.assertFalse(self.analyzer._has_seq_scan(plan_without_seq))


if __name__ == '__main__':
    unittest.main()

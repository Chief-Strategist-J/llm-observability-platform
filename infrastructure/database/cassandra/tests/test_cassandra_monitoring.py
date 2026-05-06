import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from cassandra.cluster import Session

project_root = Path(__file__).resolve().parents[4)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.database.cassandra.monitoring.cassandra_query_collector import CassandraQueryCollector
from infrastructure.database.cassandra.monitoring.cassandra_query_analyzer import CassandraQueryAnalyzer
from infrastructure.database.cassandra.monitoring.cassandra_metrics_exporter import CassandraMetricsExporter
from infrastructure.database.cassandra.monitoring.cassandra_monitoring_client import CassandraMonitoringClient
from infrastructure.database.shared.query_monitoring_interfaces import (
    QueryMetric, QueryStatus, QueryPerformanceLevel, QueryMonitoringConfig
)


class TestCassandraQueryCollector(unittest.TestCase):
    def setUp(self):
        self.mock_session = Mock(spec=Session)
        self.config = QueryMonitoringConfig()
        self.collector = CassandraQueryCollector(self.mock_session, self.config)

    def test_collect_query_metrics(self):
        self.obs.log_info("test_collect_query_metrics")
        
        with patch.object(self.collector, '_get_system_metrics', return_value=[]):
            with patch.object(self.collector, '_get_table_metrics', return_value=[]):
                with patch.object(self.collector, '_get_slow_query_metrics', return_value=[]):
                    metrics = self.collector.collect_query_metrics(limit=10)
                    
                    self.assertIsInstance(metrics, list)

    def test_get_slow_queries(self):
        with patch.object(self.collector, 'collect_query_metrics') as mock_collect:
            mock_metrics = [
                QueryMetric(
                    query_hash="slow_hash",
                    query_type="select",
                    database="cassandra",
                    collection_table="users",
                    execution_time_ms=1500.0,
                    status=QueryStatus.SUCCESS,
                    performance_level=QueryPerformanceLevel.SLOW,
                    timestamp=datetime.utcnow()
                ),
                QueryMetric(
                    query_hash="fast_hash",
                    query_type="select",
                    database="cassandra",
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
            self.assertEqual(slow_queries[0].query_hash, "slow_hash")

    def test_record_query_execution(self):
        metric = QueryMetric(
            query_hash="test_hash",
            query_type="select",
            database="cassandra",
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

    def test_get_performance_summary(self):
        with patch('infrastructure.database.cassandra.monitoring.cassandra_query_collector.TimeWindowCalculator') as mock_time:
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
                    query_type="select",
                    database="cassandra",
                    collection_table="users",
                    execution_time_ms=1500.0,
                    status=QueryStatus.SUCCESS,
                    performance_level=QueryPerformanceLevel.SLOW,
                    timestamp=datetime.utcnow()
                )
            ]
            
            gaps = self.collector.identify_index_gaps()
            
            self.assertIsInstance(gaps, list)

    def test_get_database_metrics(self):
        with patch('infrastructure.database.cassandra.monitoring.cassandra_query_collector.execute_query') as mock_execute:
            mock_execute.return_value = Mock()
            mock_execute.return_value.success = True
            mock_execute.return_value.records = [{"cluster_name": "test"}]
            
            metrics = self.collector.get_database_metrics()
            
            self.assertIsInstance(metrics, dict)

    def test_get_table_statistics(self):
        with patch('infrastructure.database.cassandra.monitoring.cassandra_query_collector.execute_query') as mock_execute:
            mock_execute.return_value = Mock()
            mock_execute.return_value.success = True
            mock_execute.return_value.records = [{"table_name": "users"}]
            
            stats = self.collector.get_table_statistics("users")
            
            self.assertIsInstance(stats, dict)


class TestCassandraQueryAnalyzer(unittest.TestCase):
    def setUp(self):
        self.mock_session = Mock(spec=Session)
        self.analyzer = CassandraQueryAnalyzer(self.mock_session)

    def test_analyze_query(self):
        with patch.object(self.analyzer, 'explain_query') as mock_explain:
            mock_explain.return_value = {"plan": {}, "success": True}
            
            result = self.analyzer.analyze_query("SELECT * FROM users", "cassandra")
            
            self.assertIsNotNone(result)
            self.assertEqual(result.query_text, "SELECT * FROM users")
            mock_explain.assert_called_once_with("SELECT * FROM users", "cassandra")

    def test_explain_query(self):
        with patch('infrastructure.database.cassandra.monitoring.cassandra_query_analyzer.explain_query') as mock_explain:
            mock_explain.return_value = {"plan": "test_plan", "success": True}
            
            plan = self.analyzer.explain_query("SELECT * FROM users", "cassandra")
            
            self.assertIsInstance(plan, dict)
            self.assertTrue(plan.get("success", False))

    def test_suggest_indexes(self):
        with patch.object(self.analyzer, 'explain_query') as mock_explain:
            mock_explain.return_value = {"plan": {"collectionScan": True}}
            
            suggestions = self.analyzer.suggest_indexes("SELECT * FROM users", "cassandra")
            
            self.assertIsInstance(suggestions, list)

    def test_generate_performance_report(self):
        with patch.object(self.analyzer, '_get_database_name') as mock_db_name:
            mock_db_name.return_value = "cassandra"
            
            period_start = datetime.utcnow() - timedelta(hours=24)
            period_end = datetime.utcnow()
            
            report = self.analyzer.generate_performance_report("cassandra", period_start, period_end)
            
            self.assertIsNotNone(report)
            self.assertEqual(report.database, "cassandra")

    def test_get_query_plan_analysis(self):
        with patch.object(self.analyzer, 'explain_query') as mock_explain:
            mock_explain.return_value = {"plan": {"plan_text": "Seq Scan"}, "success": True}
            
            analysis = self.analyzer.get_query_plan_analysis("SELECT * FROM users", "cassandra")
            
            self.assertIsInstance(analysis, dict)
            self.assertIn("query", analysis)
            self.assertIn("analysis", analysis)

    def test_get_schema_analysis(self):
        with patch('infrastructure.database.cassandra.monitoring.cassandra_query_analyzer.execute_query') as mock_execute:
            mock_execute.return_value = Mock()
            mock_execute.return_value.success = True
            mock_execute.return_value.records = [{"table_name": "users"}]
            
            analysis = self.analyzer.get_schema_analysis("cassandra")
            
            self.assertIsInstance(analysis, dict)
            self.assertTrue(analysis.get("success", False))


class TestCassandraMetricsExporter(unittest.TestCase):
    def setUp(self):
        self.mock_session = Mock(spec=Session)
        self.exporter = CassandraMetricsExporter(self.mock_session)

    def test_export_query_metrics(self):
        metrics = [
            QueryMetric(
                query_hash="hash1",
                query_type="select",
                database="cassandra",
                collection_table="users",
                execution_time_ms=100.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.FAST,
                timestamp=datetime.utcnow()
            )
        ]
        
        result = self.exporter.export_query_metrics(metrics)
        
        self.assertIsInstance(result, str)
        self.assertIn("cassandra", result)

    def test_export_database_metrics(self):
        metrics = {
            "cluster_name": "test_cluster",
            "table_count": 10,
            "node_count": 3
        }
        
        result = self.exporter.export_database_metrics("cassandra", metrics)
        
        self.assertIsInstance(result, str)
        self.assertIn("cassandra", result)

    def test_get_prometheus_metrics(self):
        with patch.object(self.exporter, '_collect_database_query_metrics') as mock_db_metrics:
            with patch.object(self.exporter, '_collect_server_metrics') as mock_server:
                mock_db_metrics.return_value = "db_metrics"
                mock_server.return_value = "server_metrics"
                
                result = self.exporter.get_prometheus_metrics()
                
                self.assertIsInstance(result, str)

    def test_get_health_status(self):
        with patch('infrastructure.database.cassandra.monitoring.cassandra_metrics_exporter.execute_query') as mock_execute:
            mock_execute.return_value = Mock()
            mock_execute.return_value.success = True
            mock_execute.return_value.records = [{"uptime": 1000}]
            
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


class TestCassandraMonitoringClient(unittest.TestCase):
    def setUp(self):
        self.mock_session = Mock(spec=Session)
        self.config = QueryMonitoringConfig()
        self.monitoring_client = CassandraMonitoringClient(self.mock_session, self.config)

    def test_execute_with_monitoring(self):
        with patch('infrastructure.database.cassandra.monitoring.cassandra_monitoring_client.execute_query') as mock_execute:
            mock_execute.return_value = Mock()
            mock_execute.return_value.success = True
            mock_execute.return_value.records = [{"data": "test"}]
            mock_execute.return_value.execution_time_ms = 100.0
            
            result = self.monitoring_client.execute_with_monitoring("SELECT * FROM users")
            
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


class TestCassandraIntegration(unittest.TestCase):
    """Integration tests for Cassandra monitoring components"""
    
    def setUp(self):
        self.mock_session = Mock(spec=Session)
        self.config = QueryMonitoringConfig()

    def test_end_to_end_monitoring_flow(self):
        with patch('infrastructure.database.cassandra.monitoring.cassandra_monitoring_client.execute_query') as mock_execute:
            mock_execute.return_value = Mock()
            mock_execute.return_value.success = True
            mock_execute.return_value.records = [{"data": "test"}]
            mock_execute.return_value.execution_time_ms = 1500.0
            
            client = CassandraMonitoringClient(self.mock_session, self.config)
            result = client.execute_with_monitoring("SELECT * FROM users")
            
            self.assertTrue(result["success"])
            self.assertEqual(result["performance_level"], QueryPerformanceLevel.SLOW)

    def test_error_handling(self):
        with patch('infrastructure.database.cassandra.monitoring.cassandra_monitoring_client.execute_query') as mock_execute:
            mock_execute.side_effect = Exception("Database error")
            
            client = CassandraMonitoringClient(self.mock_session, self.config)
            result = client.execute_with_monitoring("SELECT * FROM users")
            
            self.assertFalse(result["success"])
            self.assertIn("error", result)
            self.assertEqual(result["performance_level"], QueryPerformanceLevel.CRITICAL)


if __name__ == '__main__':
    unittest.main()

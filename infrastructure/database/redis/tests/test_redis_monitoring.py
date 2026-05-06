import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import redis
from redis import Redis

project_root = Path(__file__).resolve().parents[4)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.database.redis.monitoring.redis_query_collector import RedisQueryCollector
from infrastructure.database.redis.monitoring.redis_query_analyzer import RedisQueryAnalyzer
from infrastructure.database.redis.monitoring.redis_metrics_exporter import RedisMetricsExporter
from infrastructure.database.redis.monitoring.redis_monitoring_client import RedisMonitoringClient
from infrastructure.database.shared.query_monitoring_interfaces import (
    QueryMetric, QueryStatus, QueryPerformanceLevel, QueryMonitoringConfig
)


class TestRedisQueryCollector(unittest.TestCase):
    def setUp(self):
        self.mock_client = Mock(spec=Redis)
        self.config = QueryMonitoringConfig()
        self.collector = RedisQueryCollector(self.mock_client, self.config)

    def test_collect_query_metrics(self):
        self.obs.log_info("test_collect_query_metrics")
        
        with patch.object(self.collector, '_get_slow_log_metrics', return_value=[]):
            with patch.object(self.collector, '_get_command_metrics', return_value=[]):
                with patch.object(self.collector, '_get_key_operation_metrics', return_value=[]):
                    metrics = self.collector.collect_query_metrics(limit=10)
                    
                    self.assertIsInstance(metrics, list)

    def test_get_slow_queries(self):
        with patch.object(self.collector, 'collect_query_metrics') as mock_collect:
            mock_metrics = [
                QueryMetric(
                    query_hash="slow_hash",
                    query_type="get",
                    database="redis",
                    execution_time_ms=1500.0,
                    status=QueryStatus.SUCCESS,
                    performance_level=QueryPerformanceLevel.SLOW,
                    timestamp=datetime.utcnow()
                ),
                QueryMetric(
                    query_hash="fast_hash",
                    query_type="set",
                    database="redis",
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
            query_type="get",
            database="redis",
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
        with patch('infrastructure.database.redis.monitoring.redis_query_collector.TimeWindowCalculator') as mock_time:
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
                    query_type="keys",
                    database="redis",
                    execution_time_ms=1500.0,
                    status=QueryStatus.SUCCESS,
                    performance_level=QueryPerformanceLevel.SLOW,
                    timestamp=datetime.utcnow()
                )
            ]
            
            gaps = self.collector.identify_index_gaps()
            
            self.assertIsInstance(gaps, list)

    def test_get_database_metrics(self):
        with patch.object(self.mock_client, 'info') as mock_info:
            mock_info.return_value = {"redis_version": "6.0.0", "connected_clients": 10}
            
            metrics = self.collector.get_database_metrics()
            
            self.assertIsInstance(metrics, dict)

    def test_get_key_statistics(self):
        with patch.object(self.mock_client, 'keys') as mock_keys:
            with patch.object(self.mock_client, 'type') as mock_type:
                mock_keys.return_value = ["key1", "key2", "key3"]
                mock_type.return_value = "string"
                
                stats = self.collector.get_key_statistics()
                
                self.assertIsInstance(stats, dict)
                self.assertEqual(stats["total_keys"], 3)

    def test_get_connection_metrics(self):
        with patch.object(self.mock_client, 'info') as mock_info:
            mock_info.side_effect = [
                {"connected_clients": 10, "total_connections_received": 100},
                {"total_commands_processed": 1000, "instantaneous_ops_per_sec": 50}
            ]
            
            metrics = self.collector.get_connection_metrics()
            
            self.assertIsInstance(metrics, dict)

    def test_get_slow_log_analysis(self):
        with patch('infrastructure.database.redis.monitoring.redis_query_collector.get_slow_log') as mock_slow_log:
            mock_slow_log.return_value = [
                {
                    "id": 1,
                    "timestamp": datetime.utcnow().isoformat(),
                    "execution_time_micros": 1500000,
                    "command": ["GET", "key1"],
                    "client_info": "127.0.0.1:12345"
                }
            ]
            
            analysis = self.collector.get_slow_log_analysis(limit=10)
            
            self.assertIsInstance(analysis, dict)
            self.assertIn("total_slow_queries", analysis)


class TestRedisQueryAnalyzer(unittest.TestCase):
    def setUp(self):
        self.mock_client = Mock(spec=Redis)
        self.analyzer = RedisQueryAnalyzer(self.mock_client)

    def test_analyze_query(self):
        with patch.object(self.analyzer, 'explain_query') as mock_explain:
            mock_explain.return_value = {"command": "GET", "success": True}
            
            result = self.analyzer.analyze_query("GET key1", "redis")
            
            self.assertIsNotNone(result)
            self.assertEqual(result.query_text, "GET key1")
            mock_explain.assert_called_once_with("GET key1", "redis")

    def test_explain_query(self):
        parts = ["GET", "key1"]
        
        analysis = self.analyzer.explain_query("GET key1", "redis")
        
        self.assertIsInstance(analysis, dict)
        self.assertTrue(analysis.get("success", False))
        self.assertEqual(analysis["command"], "GET")

    def test_suggest_indexes(self):
        suggestions = self.analyzer.suggest_indexes("GET key1", "redis")
        
        self.assertIsInstance(suggestions, list)
        
        # Check for Redis-specific suggestions
        suggestion_types = [s.get("type") for s in suggestions]
        self.assertIn("data_structure", suggestion_types)

    def test_generate_performance_report(self):
        with patch.object(self.analyzer, '_get_database_name') as mock_db_name:
            mock_db_name.return_value = "redis"
            
            period_start = datetime.utcnow() - timedelta(hours=24)
            period_end = datetime.utcnow()
            
            report = self.analyzer.generate_performance_report("redis", period_start, period_end)
            
            self.assertIsNotNone(report)
            self.assertEqual(report.database, "redis")

    def test_get_query_plan_analysis(self):
        analysis = self.analyzer.get_query_plan_analysis("GET key1", "redis")
        
        self.assertIsInstance(analysis, dict)
        self.assertIn("query", analysis)
        self.assertIn("analysis", analysis)

    def test_get_schema_analysis(self):
        with patch.object(self.analyzer, '_get_database_name') as mock_db_name:
            mock_db_name.return_value = "redis"
            
            analysis = self.analyzer.get_schema_analysis("redis")
            
            self.assertIsInstance(analysis, dict)
            self.assertTrue(analysis.get("success", False))

    def test_extract_query_type(self):
        self.assertEqual(self.analyzer._extract_query_type("GET key1"), "get")
        self.assertEqual(self.analyzer._extract_query_type("SET key value"), "set")
        self.assertEqual(self.analyzer._extract_query_type("HGET hash field"), "hget")
        self.assertEqual(self.analyzer._extract_query_type("UNKNOWN"), "unknown")

    def test_suggest_data_structures_for_key(self):
        suggestions = self.analyzer._suggest_data_structures_for_key("user:123")
        
        self.assertIsInstance(suggestions, list)
        self.assertTrue(len(suggestions) > 0)

    def test_is_potentially_large_key(self):
        with patch.object(self.mock_client, 'strlen') as mock_strlen:
            mock_strlen.return_value = 2048  # > 1KB
            
            is_large = self.analyzer._is_potentially_large_key("large_key")
            
            self.assertTrue(is_large)


class TestRedisMetricsExporter(unittest.TestCase):
    def setUp(self):
        self.mock_client = Mock(spec=Redis)
        self.exporter = RedisMetricsExporter(self.mock_client)

    def test_export_query_metrics(self):
        metrics = [
            QueryMetric(
                query_hash="hash1",
                query_type="get",
                database="redis",
                execution_time_ms=100.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.FAST,
                timestamp=datetime.utcnow()
            )
        ]
        
        result = self.exporter.export_query_metrics(metrics)
        
        self.assertIsInstance(result, str)
        self.assertIn("redis", result)

    def test_export_database_metrics(self):
        metrics = {
            "redis_version": "6.0.0",
            "database_size": 1000,
            "used_memory": 1024000
        }
        
        result = self.exporter.export_database_metrics("redis", metrics)
        
        self.assertIsInstance(result, str)
        self.assertIn("redis", result)

    def test_get_prometheus_metrics(self):
        with patch.object(self.exporter, '_collect_database_query_metrics') as mock_db_metrics:
            with patch.object(self.exporter, '_collect_server_metrics') as mock_server:
                mock_db_metrics.return_value = "db_metrics"
                mock_server.return_value = "server_metrics"
                
                result = self.exporter.get_prometheus_metrics()
                
                self.assertIsInstance(result, str)

    def test_get_health_status(self):
        with patch.object(self.mock_client, 'ping') as mock_ping:
            mock_ping.return_value = True
            
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

    def test_get_memory_metrics(self):
        info_data = {
            "used_memory": 1024000,
            "used_memory_rss": 2048000,
            "used_memory_peak": 3072000,
            "maxmemory": 8192000,
            "mem_fragmentation_ratio": 1.5
        }
        
        lines = self.exporter._get_memory_metrics(info_data)
        
        self.assertIsInstance(lines, list)
        self.assertTrue(len(lines) > 0)

    def test_get_client_metrics(self):
        info_data = {
            "connected_clients": 10,
            "client_recent_max_input_buffer": 1024,
            "client_recent_max_output_buffer": 2048,
            "blocked_clients": 2
        }
        
        lines = self.exporter._get_client_metrics(info_data)
        
        self.assertIsInstance(lines, list)
        self.assertTrue(len(lines) > 0)

    def test_get_stats_metrics(self):
        info_data = {
            "total_connections_received": 1000,
            "total_commands_processed": 5000,
            "instantaneous_ops_per_sec": 100,
            "keyspace_hits": 800,
            "keyspace_misses": 200
        }
        
        lines = self.exporter._get_stats_metrics(info_data)
        
        self.assertIsInstance(lines, list)
        self.assertTrue(len(lines) > 0)


class TestRedisMonitoringClient(unittest.TestCase):
    def setUp(self):
        self.mock_client = Mock(spec=Redis)
        self.config = QueryMonitoringConfig()
        self.monitoring_client = RedisMonitoringClient(self.mock_client, self.config)

    def test_execute_with_monitoring(self):
        with patch('infrastructure.database.redis.monitoring.redis_monitoring_client.execute_query_with_timing') as mock_execute:
            mock_execute.return_value = Mock()
            mock_execute.return_value.success = True
            mock_execute.return_value.result = "test_value"
            mock_execute.return_value.execution_time_ms = 100.0
            
            result = self.monitoring_client.execute_with_monitoring("GET key1")
            
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
        with patch.object(self.monitoring_client.collector, 'get_slow_log_analysis') as mock_slow_log:
            mock_slow_log.return_value = {
                "total_slow_queries": 5,
                "analysis": {},
                "slow_queries": []
            }
            
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

    def test_get_key_performance_analysis(self):
        with patch.object(self.monitoring_client.collector, 'get_key_statistics') as mock_key_stats:
            mock_key_stats.return_value = {
                "total_keys": 1000,
                "key_types": {"string": 800, "hash": 200},
                "sample_memory_usage": {"key1": 512, "key2": 256}
            }
            
            analysis = self.monitoring_client.get_key_performance_analysis("user:*")
            
            self.assertIsInstance(analysis, dict)
            self.assertIn("statistics", analysis)


class TestRedisIntegration(unittest.TestCase):
    """Integration tests for Redis monitoring components"""
    
    def setUp(self):
        self.mock_client = Mock(spec=Redis)
        self.config = QueryMonitoringConfig()

    def test_end_to_end_monitoring_flow(self):
        with patch('infrastructure.database.redis.monitoring.redis_monitoring_client.execute_query_with_timing') as mock_execute:
            mock_execute.return_value = Mock()
            mock_execute.return_value.success = True
            mock_execute.return_value.result = "test_value"
            mock_execute.return_value.execution_time_ms = 1500.0
            
            client = RedisMonitoringClient(self.mock_client, self.config)
            result = client.execute_with_monitoring("GET key1")
            
            self.assertTrue(result["success"])
            self.assertEqual(result["performance_level"], QueryPerformanceLevel.SLOW)

    def test_error_handling(self):
        with patch('infrastructure.database.redis.monitoring.redis_monitoring_client.execute_query_with_timing') as mock_execute:
            mock_execute.side_effect = Exception("Database error")
            
            client = RedisMonitoringClient(self.mock_client, self.config)
            result = client.execute_with_monitoring("GET key1")
            
            self.assertFalse(result["success"])
            self.assertIn("error", result)
            self.assertEqual(result["performance_level"], QueryPerformanceLevel.CRITICAL)

    def test_slow_log_integration(self):
        with patch.object(self.mock_client, 'slowlog_get') as mock_slowlog:
            mock_slowlog.return_value = [
                [1, int(datetime.utcnow().timestamp()), 1500000, ["GET", "slow_key"], "127.0.0.1:12345"]
            ]
            
            client = RedisMonitoringClient(self.mock_client, self.config)
            slow_log_analysis = client.collector.get_slow_log_analysis(limit=10)
            
            self.assertIsInstance(slow_log_analysis, dict)
            self.assertIn("total_slow_queries", slow_log_analysis)


if __name__ == '__main__':
    unittest.main()

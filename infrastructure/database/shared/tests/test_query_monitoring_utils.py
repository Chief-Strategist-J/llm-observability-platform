import unittest
from datetime import datetime, timedelta
from infrastructure.database.shared.query_monitoring_utils import (
    QueryHashGenerator, PerformanceClassifier, QueryMetricsAggregator,
    QueryRecommendationEngine, TimeWindowCalculator, MetricsFormatter,
    QueryPlanAnalyzer
)
from infrastructure.database.shared.query_monitoring_interfaces import (
    QueryMetric, QueryStatus, QueryPerformanceLevel
)


class TestQueryHashGenerator(unittest.TestCase):
    def test_generate_hash_consistency(self):
        query = "SELECT * FROM users WHERE id = 1"
        hash1 = QueryHashGenerator.generate_hash(query)
        hash2 = QueryHashGenerator.generate_hash(query)
        self.assertEqual(hash1, hash2)
    
    def test_generate_hash_with_params(self):
        query = "SELECT * FROM users WHERE id = $1"
        params = {"id": 1}
        hash1 = QueryHashGenerator.generate_hash(query, params)
        hash2 = QueryHashGenerator.generate_hash(query, params)
        self.assertEqual(hash1, hash2)
    
    def test_generate_hash_different_queries(self):
        query1 = "SELECT * FROM users WHERE id = 1"
        query2 = "SELECT * FROM users WHERE id = 2"
        hash1 = QueryHashGenerator.generate_hash(query1)
        hash2 = QueryHashGenerator.generate_hash(query2)
        self.assertEqual(hash1, hash2)  # Should be same after normalization
    
    def test_normalize_query(self):
        query = "SELECT   *   FROM   users   WHERE   id   =   1"
        normalized = QueryHashGenerator._normalize_query(query)
        self.assertEqual(normalized, "select * from users where id = ?")


class TestPerformanceClassifier(unittest.TestCase):
    def test_classify_performance_fast(self):
        level = PerformanceClassifier.classify_performance(50.0, PerformanceClassifier.get_default_thresholds())
        self.assertEqual(level, QueryPerformanceLevel.FAST)
    
    def test_classify_performance_normal(self):
        level = PerformanceClassifier.classify_performance(500.0, PerformanceClassifier.get_default_thresholds())
        self.assertEqual(level, QueryPerformanceLevel.NORMAL)
    
    def test_classify_performance_slow(self):
        level = PerformanceClassifier.classify_performance(2000.0, PerformanceClassifier.get_default_thresholds())
        self.assertEqual(level, QueryPerformanceLevel.SLOW)
    
    def test_classify_performance_critical(self):
        level = PerformanceClassifier.classify_performance(6000.0, PerformanceClassifier.get_default_thresholds())
        self.assertEqual(level, QueryPerformanceLevel.CRITICAL)
    
    def test_get_default_thresholds(self):
        thresholds = PerformanceClassifier.get_default_thresholds()
        self.assertIn('fast', thresholds)
        self.assertIn('normal', thresholds)
        self.assertIn('slow', thresholds)
        self.assertIn('critical', thresholds)
        self.assertEqual(thresholds['fast'], 100.0)


class TestQueryMetricsAggregator(unittest.TestCase):
    def setUp(self):
        self.sample_metrics = [
            QueryMetric(
                query_hash="hash1",
                query_type="select",
                database="test",
                execution_time_ms=100.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.FAST,
                timestamp=datetime.utcnow()
            ),
            QueryMetric(
                query_hash="hash2",
                query_type="insert",
                database="test",
                execution_time_ms=1500.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.SLOW,
                timestamp=datetime.utcnow()
            )
        ]
    
    def test_aggregate_metrics(self):
        result = QueryMetricsAggregator.aggregate_metrics(self.sample_metrics)
        
        self.assertEqual(result['total_queries'], 2)
        self.assertEqual(result['avg_execution_time_ms'], 800.0)  # (100 + 1500) / 2
        self.assertEqual(result['slow_query_count'], 1)
        self.assertEqual(result['slow_query_percentage'], 50.0)
    
    def test_aggregate_empty_metrics(self):
        result = QueryMetricsAggregator.aggregate_metrics([])
        self.assertEqual(result, {})
    
    def test_get_top_slow_queries(self):
        slow_queries = QueryMetricsAggregator.get_top_slow_queries(self.sample_metrics, limit=5)
        self.assertEqual(len(slow_queries), 1)
        self.assertEqual(slow_queries[0].query_hash, "hash2")


class TestQueryRecommendationEngine(unittest.TestCase):
    def setUp(self):
        self.sample_metrics = [
            QueryMetric(
                query_hash="hash1",
                query_type="select",
                database="test",
                execution_time_ms=100.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.FAST,
                timestamp=datetime.utcnow()
            ),
            QueryMetric(
                query_hash="hash2",
                query_type="select",
                database="test",
                execution_time_ms=2000.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.SLOW,
                timestamp=datetime.utcnow(),
                collection_table="users"
            )
        ]
    
    def test_generate_recommendations(self):
        recommendations = QueryRecommendationEngine.generate_recommendations(self.sample_metrics)
        self.assertIsInstance(recommendations, list)
    
    def test_generate_recommendations_empty(self):
        recommendations = QueryRecommendationEngine.generate_recommendations([])
        self.assertEqual(recommendations, [])


class TestTimeWindowCalculator(unittest.TestCase):
    def test_get_time_windows(self):
        period_minutes = 60
        windows = TimeWindowCalculator.get_time_windows(period_minutes)
        
        self.assertIn('now', windows)
        self.assertIn('period_start', windows)
        self.assertIn('period_end', windows)
        
        expected_start = windows['now'] - timedelta(minutes=period_minutes)
        self.assertEqual(windows['period_start'], expected_start)
        self.assertEqual(windows['period_end'], windows['now'])
    
    def test_filter_metrics_by_time(self):
        now = datetime.utcnow()
        period_start = now - timedelta(hours=1)
        period_end = now
        
        metrics = [
            QueryMetric(
                query_hash="hash1",
                query_type="select",
                database="test",
                execution_time_ms=100.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.FAST,
                timestamp=now - timedelta(minutes=30)  # Within period
            ),
            QueryMetric(
                query_hash="hash2",
                query_type="insert",
                database="test",
                execution_time_ms=200.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.FAST,
                timestamp=now - timedelta(hours=2)  # Outside period
            )
        ]
        
        filtered = TimeWindowCalculator.filter_metrics_by_time(metrics, period_start, period_end)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].query_hash, "hash1")


class TestMetricsFormatter(unittest.TestCase):
    def setUp(self):
        self.sample_metrics = [
            QueryMetric(
                query_hash="hash1",
                query_type="select",
                database="test",
                execution_time_ms=100.0,
                status=QueryStatus.SUCCESS,
                performance_level=QueryPerformanceLevel.FAST,
                timestamp=datetime.utcnow()
            )
        ]
    
    def test_format_for_prometheus(self):
        prometheus_output = MetricsFormatter.format_for_prometheus(self.sample_metrics, "test_db")
        
        self.assertIsInstance(prometheus_output, str)
        self.assertIn("db_query_total", prometheus_output)
        self.assertIn("test_db", prometheus_output)
    
    def test_format_for_prometheus_empty(self):
        prometheus_output = MetricsFormatter.format_for_prometheus([], "test_db")
        self.assertEqual(prometheus_output, "")
    
    def test_format_for_json_export(self):
        json_output = MetricsFormatter.format_for_json_export(self.sample_metrics, "test_db")
        
        self.assertIsInstance(json_output, dict)
        self.assertIn("database", json_output)
        self.assertIn("metrics", json_output)
        self.assertIn("summary", json_output)
        self.assertEqual(json_output["database"], "test_db")


class TestQueryPlanAnalyzer(unittest.TestCase):
    def test_extract_indexes_from_plan(self):
        plan = {
            "indexName": "test_index",
            "fields": ["id", "name"]
        }
        
        indexes = QueryPlanAnalyzer.extract_indexes_from_plan(plan)
        self.assertIn("test_index", indexes)
    
    def test_extract_indexes_from_nested_plan(self):
        plan = {
            "nodes": [
                {
                    "indexName": "index1",
                    "children": [
                        {
                            "indexName": "index2"
                        }
                    ]
                }
            ]
        }
        
        indexes = QueryPlanAnalyzer.extract_indexes_from_plan(plan)
        self.assertIn("index1", indexes)
        self.assertIn("index2", indexes)
    
    def test_analyze_plan_efficiency(self):
        plan = {
            "collectionScan": True
        }
        
        analysis = QueryPlanAnalyzer.analyze_plan_efficiency(plan)
        
        self.assertIn("efficiency_score", analysis)
        self.assertIn("issues", analysis)
        self.assertIn("indexes_used", analysis)
        self.assertLess(analysis["efficiency_score"], 100)
        self.assertTrue(any("collection scan" in issue.lower() for issue in analysis["issues"]))
    
    def test_analyze_plan_efficiency_no_issues(self):
        plan = {
            "indexScan": True,
            "indexName": "test_index"
        }
        
        analysis = QueryPlanAnalyzer.analyze_plan_efficiency(plan)
        
        self.assertEqual(analysis["efficiency_score"], 100)
        self.assertEqual(len(analysis["issues"]), 0)


if __name__ == '__main__':
    unittest.main()

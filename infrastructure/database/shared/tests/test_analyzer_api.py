import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from infrastructure.database.shared.analyzer_api import (
    cross_database_analysis, performance_comparison, optimization_report,
    health_overview, aggregated_metrics
)


class TestAnalyzerAPI(unittest.TestCase):
    """Test the shared analyzer API endpoints"""
    
    @patch('infrastructure.database.shared.analyzer_api._analyze_mongodb_query')
    @patch('infrastructure.database.shared.analyzer_api._analyze_neo4j_query')
    @patch('infrastructure.database.shared.analyzer_api._analyze_postgres_query')
    async def test_cross_database_analysis(self, mock_postgres, mock_neo4j, mock_mongodb):
        # Mock the individual database analysis functions
        mock_mongodb.return_value = {"performance_score": 80, "recommendations": ["Add index"]}
        mock_neo4j.return_value = {"performance_score": 75, "recommendations": ["Optimize query"]}
        mock_postgres.return_value = {"performance_score": 85, "recommendations": ["Create index"]}
        
        # Create a mock request
        request = Mock()
        request.query = "SELECT * FROM users WHERE id = 1"
        request.databases = ["mongodb", "neo4j", "postgres"]
        
        result = await cross_database_analysis(request)
        
        self.assertTrue(result["success"])
        self.assertIn("database_results", result["data"])
        self.assertIn("comparison", result["data"])
        self.assertEqual(len(result["data"]["database_results"]), 3)
        
        # Verify comparison data
        comparison = result["data"]["comparison"]
        self.assertIn("performance_scores", comparison)
        self.assertEqual(comparison["performance_scores"]["mongodb"], 80)
        self.assertEqual(comparison["performance_scores"]["neo4j"], 75)
        self.assertEqual(comparison["performance_scores"]["postgres"], 85)
    
    @patch('infrastructure.database.shared.analyzer_api._get_mongodb_performance_summary')
    @patch('infrastructure.database.shared.analyzer_api._get_neo4j_performance_summary')
    @patch('infrastructure.database.shared.analyzer_api._get_postgres_performance_summary')
    async def test_performance_comparison(self, mock_postgres, mock_neo4j, mock_mongodb):
        # Mock performance summaries
        mock_mongodb.return_value = {"summary": {"total_queries": 1000, "avg_execution_time_ms": 150}}
        mock_neo4j.return_value = {"summary": {"total_queries": 800, "avg_execution_time_ms": 200}}
        mock_postgres.return_value = {"summary": {"total_queries": 1200, "avg_execution_time_ms": 120}}
        
        request = Mock()
        request.period_hours = 24
        request.databases = ["mongodb", "neo4j", "postgres"]
        
        result = await performance_comparison(request)
        
        self.assertTrue(result["success"])
        self.assertIn("database_performance", result["data"])
        self.assertIn("comparison", result["data"])
        
        # Verify comparison metrics
        comparison = result["data"]["comparison"]
        self.assertIn("total_queries", comparison)
        self.assertEqual(comparison["total_queries"]["mongodb"], 1000)
        self.assertEqual(comparison["total_queries"]["neo4j"], 800)
        self.assertEqual(comparison["total_queries"]["postgres"], 1200)
    
    @patch('infrastructure.database.shared.analyzer_api._get_mongodb_optimization_report')
    @patch('infrastructure.database.shared.analyzer_api._get_neo4j_optimization_report')
    @patch('infrastructure.database.shared.analyzer_api._get_postgres_optimization_report')
    async def test_optimization_report(self, mock_postgres, mock_neo4j, mock_mongodb):
        # Mock optimization reports
        mock_mongodb.return_value = {"issues": [{"severity": "high", "description": "Slow query"}]}
        mock_neo4j.return_value = {"issues": [{"severity": "medium", "description": "Index gap"}]}
        mock_postgres.return_value = {"issues": [{"severity": "low", "description": "Minor issue"}]}
        
        request = Mock()
        request.databases = ["mongodb", "neo4j", "postgres"]
        request.include_recommendations = True
        
        result = await optimization_report(request)
        
        self.assertTrue(result["success"])
        self.assertIn("database_reports", result["data"])
        self.assertIn("overall_recommendations", result["data"])
        self.assertIn("summary", result["data"])
        
        # Verify summary
        summary = result["data"]["summary"]
        self.assertEqual(summary["total_issues"], 3)
        self.assertEqual(summary["critical_issues"], 0)
        self.assertEqual(summary["high_issues"], 1)
    
    @patch('infrastructure.database.shared.analyzer_api._get_mongodb_health')
    @patch('infrastructure.database.shared.analyzer_api._get_neo4j_health')
    @patch('infrastructure.database.shared.analyzer_api._get_postgres_health')
    async def test_health_overview(self, mock_postgres, mock_neo4j, mock_mongodb):
        # Mock health status
        mock_mongodb.return_value = {"healthy": True, "health_score": 85}
        mock_neo4j.return_value = {"healthy": True, "health_score": 90}
        mock_postgres.return_value = {"healthy": False, "health_score": 60}
        
        result = await health_overview()
        
        self.assertTrue(result["success"])
        self.assertIn("individual_health", result["data"])
        self.assertIn("overall_health", result["data"])
        
        # Verify overall health calculation
        overall_health = result["data"]["overall_health"]
        self.assertEqual(overall_health["healthy_databases"], 2)
        self.assertEqual(overall_health["total_databases"], 3)
        self.assertEqual(overall_health["status"], "degraded")
    
    @patch('infrastructure.database.shared.analyzer_api._get_mongodb_metrics')
    @patch('infrastructure.database.shared.analyzer_api._get_neo4j_metrics')
    @patch('infrastructure.database.shared.analyzer_api._get_postgres_metrics')
    async def test_aggregated_metrics(self, mock_postgres, mock_neo4j, mock_mongodb):
        # Mock metrics
        mock_mongodb.return_value = {
            "query_metrics": {"summary": {"total_queries": 1000, "avg_execution_time_ms": 150}}
        }
        mock_neo4j.return_value = {
            "query_metrics": {"summary": {"total_queries": 800, "avg_execution_time_ms": 200}}
        }
        mock_postgres.return_value = {
            "query_metrics": {"summary": {"total_queries": 1200, "avg_execution_time_ms": 120}}
        }
        
        result = await aggregated_metrics(period_minutes=60)
        
        self.assertTrue(result["success"])
        self.assertIn("individual_metrics", result["data"])
        self.assertIn("aggregated_metrics", result["data"])
        
        # Verify aggregation
        aggregated = result["data"]["aggregated_metrics"]
        self.assertEqual(aggregated["total_queries"], 3000)  # 1000 + 800 + 1200
        self.assertAlmostEqual(aggregated["avg_execution_time"], 156.67, places=2)  # (150+200+120)/3


class TestAnalyzerAPIHelpers(unittest.TestCase):
    """Test the helper functions used by the analyzer API"""
    
    def test_compare_database_results(self):
        results = {
            "mongodb": {"performance_score": 80, "recommendations": ["Add index"]},
            "neo4j": {"performance_score": 75, "recommendations": ["Optimize query"]},
            "postgres": {"performance_score": 85, "recommendations": ["Create index"]}
        }
        
        from infrastructure.database.shared.analyzer_api import _compare_database_results
        comparison = _compare_database_results(results)
        
        self.assertIn("performance_scores", comparison)
        self.assertIn("recommendations", comparison)
        self.assertEqual(comparison["performance_scores"]["mongodb"], 80)
    
    def test_compare_performance_metrics(self):
        results = {
            "mongodb": {"summary": {"total_queries": 1000, "avg_execution_time_ms": 150}},
            "postgres": {"summary": {"total_queries": 1200, "avg_execution_time_ms": 120}}
        }
        
        from infrastructure.database.shared.analyzer_api import _compare_performance_metrics
        comparison = _compare_performance_metrics(results)
        
        self.assertIn("total_queries", comparison)
        self.assertEqual(comparison["total_queries"]["mongodb"], 1000)
        self.assertEqual(comparison["total_queries"]["postgres"], 1200)
    
    def test_generate_overall_recommendations(self):
        results = {
            "mongodb": {"issues": [{"severity": "high", "description": "Slow query"}]},
            "postgres": {"issues": [{"severity": "critical", "description": "Connection issue"}]}
        }
        
        from infrastructure.database.shared.analyzer_api import _generate_overall_recommendations
        recommendations = _generate_overall_recommendations(results)
        
        self.assertIsInstance(recommendations, list)
        self.assertTrue(any("critical" in rec.lower() for rec in recommendations))
    
    def test_generate_optimization_summary(self):
        results = {
            "mongodb": {"issues": [{"severity": "high"}, {"severity": "medium"}], "health": {"healthy": True}},
            "postgres": {"issues": [{"severity": "low"}], "health": {"healthy": False}}
        }
        
        from infrastructure.database.shared.analyzer_api import _generate_optimization_summary
        summary = _generate_optimization_summary(results)
        
        self.assertEqual(summary["total_issues"], 3)
        self.assertEqual(summary["critical_issues"], 0)
        self.assertEqual(summary["high_issues"], 1)
        self.assertEqual(summary["healthy_databases"], 1)
        self.assertEqual(summary["databases_analyzed"], 2)
    
    def test_calculate_overall_health(self):
        health_status = {
            "mongodb": {"healthy": True},
            "neo4j": {"healthy": True},
            "postgres": {"healthy": False}
        }
        
        from infrastructure.database.shared.analyzer_api import _calculate_overall_health
        overall = _calculate_overall_health(health_status)
        
        self.assertEqual(overall["healthy_databases"], 2)
        self.assertEqual(overall["total_databases"], 3)
        self.assertEqual(overall["status"], "degraded")
        self.assertEqual(overall["score"], 60)
    
    def test_aggregate_metrics(self):
        metrics = {
            "mongodb": {
                "query_metrics": {
                    "summary": {"total_queries": 1000, "avg_execution_time_ms": 150, "error_rate": 5}
                }
            },
            "postgres": {
                "query_metrics": {
                    "summary": {"total_queries": 1200, "avg_execution_time_ms": 120, "error_rate": 2}
                }
            }
        }
        
        from infrastructure.database.shared.analyzer_api import _aggregate_metrics
        aggregated = _aggregate_metrics(metrics)
        
        self.assertEqual(aggregated["total_queries"], 2200)
        self.assertAlmostEqual(aggregated["avg_execution_time"], 135, places=2)
        self.assertEqual(aggregated["total_errors"], 74)  # (1000*0.05) + (1200*0.02)


class TestAnalyzerAPIErrorHandling(unittest.TestCase):
    """Test error handling in analyzer API"""
    
    async def test_cross_database_analysis_with_errors(self):
        with patch('infrastructure.database.shared.analyzer_api._analyze_mongodb_query') as mock_mongodb:
            with patch('infrastructure.database.shared.analyzer_api._analyze_neo4j_query') as mock_neo4j:
                with patch('infrastructure.database.shared.analyzer_api._analyze_postgres_query') as mock_postgres:
                    # Mock one database to fail
                    mock_mongodb.return_value = {"performance_score": 80}
                    mock_neo4j.return_value = {"error": "Neo4j not available"}
                    mock_postgres.return_value = {"performance_score": 85}
                    
                    request = Mock()
                    request.query = "SELECT * FROM users"
                    request.databases = ["mongodb", "neo4j", "postgres"]
                    
                    result = await cross_database_analysis(request)
                    
                    self.assertTrue(result["success"])
                    self.assertIn("error", result["data"]["database_results"]["neo4j"])
                    self.assertEqual(result["data"]["database_results"]["mongodb"]["performance_score"], 80)
    
    async def test_health_overview_all_unhealthy(self):
        with patch('infrastructure.database.shared.analyzer_api._get_mongodb_health') as mock_mongodb:
            with patch('infrastructure.database.shared.analyzer_api._get_neo4j_health') as mock_neo4j:
                with patch('infrastructure.database.shared.analyzer_api._get_postgres_health') as mock_postgres:
                    # Mock all databases as unhealthy
                    mock_mongodb.return_value = {"healthy": False}
                    mock_neo4j.return_value = {"healthy": False}
                    mock_postgres.return_value = {"healthy": False}
                    
                    result = await health_overview()
                    
                    self.assertTrue(result["success"])
                    overall_health = result["data"]["overall_health"]
                    self.assertEqual(overall_health["healthy_databases"], 0)
                    self.assertEqual(overall_health["status"], "critical")
                    self.assertEqual(overall_health["score"], 30)


if __name__ == '__main__':
    unittest.main()

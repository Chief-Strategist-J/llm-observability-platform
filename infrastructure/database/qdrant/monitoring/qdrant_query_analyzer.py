import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests
from requests import Session

project_root = Path(__file__).resolve().parents[4)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.database.shared.query_monitoring_interfaces import (
    IQueryAnalyzer, QueryAnalysisResult, PerformanceReport, QueryMetric,
    QueryPerformanceLevel, QueryStatus
)
from infrastructure.database.shared.query_monitoring_utils import (
    QueryHashGenerator, QueryMetricsAggregator, QueryRecommendationEngine,
    QueryPlanAnalyzer, PerformanceClassifier
)
from infrastructure.observability.scripts.observability_client import ObservabilityClient
from ..client.qdrant_client import (
    execute_request, get_http_client, QdrantConnectionConfig,
    list_collections, get_collection_info, search_points, scroll_points,
    count_points, get_cluster_info, get_metrics
)


class QdrantQueryAnalyzer(IQueryAnalyzer):
    def __init__(self, session: Session):
        self.session = session
        self.obs = ObservabilityClient(service_name="qdrant-query-analyzer")

    def analyze_query(self, query_text: str, database: str) -> QueryAnalysisResult:
        self.obs.log_info(f"analyze_query database={database}")
        
        try:
            query_hash = QueryHashGenerator.generate_hash(query_text)
            
            plan_details = self.explain_query(query_text, database)
            plan_analysis = QueryPlanAnalyzer.analyze_plan_efficiency(plan_details)
            
            performance_score = self._calculate_performance_score(query_text, database, plan_analysis)
            
            recommendations = self._generate_query_recommendations(query_text, database, plan_analysis)
            
            suggested_indexes = self.suggest_indexes(query_text, database)
            
            optimization_potential = self._assess_optimization_potential(performance_score, plan_analysis)
            
            estimated_improvement = self._estimate_improvement(suggested_indexes, plan_analysis)
            
            return QueryAnalysisResult(
                query_hash=query_hash,
                query_text=query_text,
                performance_score=performance_score,
                recommendations=recommendations,
                suggested_indexes=suggested_indexes,
                optimization_potential=optimization_potential,
                estimated_improvement_percent=estimated_improvement
            )
        
        except Exception as e:
            self.obs.log_error(f"Failed to analyze query: {e}")
            return QueryAnalysisResult(
                query_hash=QueryHashGenerator.generate_hash(query_text),
                query_text=query_text,
                performance_score=0,
                recommendations=["Query analysis failed due to error"],
                suggested_indexes=[],
                optimization_potential="unknown",
                estimated_improvement_percent=None
            )

    def explain_query(self, query_text: str, database: str) -> Dict[str, Any]:
        self.obs.log_info(f"explain_query database={database}")
        
        try:
            # Parse the query to extract operation type and parameters
            query_parts = query_text.split()
            if not query_parts:
                return {
                    "success": False,
                    "error": "Empty query"
                }
            
            operation = query_parts[0].lower()
            
            # Get operation-specific analysis
            analysis = {
                "operation": operation,
                "query_text": query_text,
                "success": True,
                "operation_info": self._get_operation_info(operation, query_parts[1:]),
                "performance_implications": self._get_performance_implications(operation, query_parts[1:]),
                "optimization_suggestions": self._get_operation_optimizations(operation, query_parts[1:])
            }
            
            return analysis
        
        except Exception as e:
            self.obs.log_error(f"Failed to explain query: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def suggest_indexes(self, query_text: str, database: str) -> List[Dict[str, Any]]:
        self.obs.log_info(f"suggest_indexes database={database}")
        
        suggestions = []
        
        try:
            query_parts = query_text.split()
            if not query_parts:
                return suggestions
            
            operation = query_parts[0].lower()
            args = query_parts[1:]
            
            # Qdrant doesn't have traditional indexes, but we can suggest HNSW optimizations
            if operation == "search" and args:
                suggestions.append({
                    'type': 'hnsw_optimization',
                    'recommendation': 'Optimize HNSW parameters for better search performance',
                    'reason': 'Vector search performance depends heavily on HNSW configuration',
                    'parameters': {
                        'm': 'Consider adjusting M parameter (16-64)',
                        'ef_construct': 'Consider adjusting ef_construct (100-400)',
                        'ef_search': 'Consider adjusting ef_search (32-128)'
                    }
                })
            
            if operation in ["search", "scroll"] and args:
                collection_name = self._extract_collection_name(query_text)
                if collection_name:
                    suggestions.append({
                        'type': 'collection_optimization',
                        'collection': collection_name,
                        'recommendation': f'Consider optimizing collection {collection_name}',
                        'reason': 'Collection configuration affects query performance',
                        'optimizations': [
                            'Adjust HNSW parameters',
                            'Consider quantization for memory efficiency',
                            'Use on_disk storage for large collections'
                        ]
                    })
            
            if operation == "search":
                suggestions.append({
                    'type': 'search_optimization',
                    'recommendation': 'Optimize search parameters for better performance',
                    'reason': 'Search parameters directly impact performance',
                    'parameters': {
                        'limit': 'Use appropriate limit to reduce computation',
                        'with_payload': 'Disable payload retrieval if not needed',
                        'with_vector': 'Disable vector retrieval if not needed'
                    }
                })
        
        except Exception as e:
            self.obs.log_error(f"Failed to suggest indexes: {e}")
        
        return suggestions

    def generate_performance_report(self, database: str, period_start: datetime, period_end: datetime) -> PerformanceReport:
        self.obs.log_info(f"generate_performance_report database={database}")
        
        try:
            from .qdrant_query_collector import QdrantQueryCollector
            collector = QdrantQueryCollector(self.session)
            
            all_metrics = collector.collect_query_metrics(limit=10000)
            
            period_metrics = [
                m for m in all_metrics
                if period_start <= m.timestamp <= period_end
            ]
            
            if not period_metrics:
                return PerformanceReport(
                    database=database,
                    period_start=period_start,
                    period_end=period_end,
                    total_queries=0,
                    slow_queries=0,
                    avg_execution_time_ms=0.0,
                    performance_distribution={level: 0 for level in QueryPerformanceLevel},
                    top_slow_queries=[],
                    recommendations=["No query data available for the specified period"]
                )
            
            summary = QueryMetricsAggregator.aggregate_metrics(period_metrics)
            top_slow = QueryMetricsAggregator.get_top_slow_queries(period_metrics, limit=10)
            recommendations = QueryRecommendationEngine.generate_recommendations(period_metrics)
            
            # Add Qdrant-specific recommendations
            qdrant_recommendations = self._generate_qdrant_specific_recommendations(period_metrics)
            recommendations.extend(qdrant_recommendations)
            
            return PerformanceReport(
                database=database,
                period_start=period_start,
                period_end=period_end,
                total_queries=summary['total_queries'],
                slow_queries=summary['slow_query_count'],
                avg_execution_time_ms=summary['avg_execution_time_ms'],
                performance_distribution=summary['performance_distribution'],
                top_slow_queries=top_slow,
                recommendations=recommendations
            )
        
        except Exception as e:
            self.obs.log_error(f"Failed to generate performance report: {e}")
            return PerformanceReport(
                database=database,
                period_start=period_start,
                period_end=period_end,
                total_queries=0,
                slow_queries=0,
                avg_execution_time_ms=0.0,
                performance_distribution={level: 0 for level in QueryPerformanceLevel},
                top_slow_queries=[],
                recommendations=[f"Report generation failed: {str(e)}"]
            )

    def _calculate_performance_score(self, query_text: str, database: str, plan_analysis: Dict[str, Any]) -> float:
        score = 100.0
        
        if plan_analysis.get('efficiency_score', 100) < 100:
            score = plan_analysis['efficiency_score']
        
        # Qdrant-specific performance factors
        query_parts = query_text.split()
        if query_parts:
            operation = query_parts[0].lower()
            
            if operation == "search":
                # Check for expensive search parameters
                if "limit=1000" in query_text or "limit=500" in query_text:
                    score -= 20  # Large limits are expensive
                
                if "with_payload=true" in query_text.lower():
                    score -= 10  # Payload retrieval adds overhead
                
                if "with_vector=true" in query_text.lower():
                    score -= 10  # Vector retrieval adds overhead
            
            elif operation == "scroll":
                if "limit=1000" in query_text or "limit=500" in query_text:
                    score -= 25  # Large scroll operations are expensive
            
            elif operation == "count":
                score -= 5  # Count operations can be expensive for large collections
        
        return max(0, score)

    def _generate_query_recommendations(self, query_text: str, database: str, plan_analysis: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        if plan_analysis.get('issues'):
            recommendations.extend(plan_analysis['issues'])
        
        query_parts = query_text.split()
        if query_parts:
            operation = query_parts[0].lower()
            
            if operation == "search":
                if "limit=1000" in query_text or "limit=500" in query_text:
                    recommendations.append("Consider reducing search limit for better performance")
                
                if "with_payload=true" in query_text.lower():
                    recommendations.append("Consider disabling payload retrieval if not needed")
                
                if "with_vector=true" in query_text.lower():
                    recommendations.append("Consider disabling vector retrieval if not needed")
            
            if operation == "scroll":
                recommendations.append("Consider using pagination instead of large scroll operations")
            
            if operation in ["search", "scroll"]:
                collection_name = self._extract_collection_name(query_text)
                if collection_name:
                    recommendations.append(f"Consider optimizing HNSW parameters for collection: {collection_name}")
        
        return recommendations

    def _assess_optimization_potential(self, performance_score: float, plan_analysis: Dict[str, Any]) -> str:
        if performance_score >= 80:
            return "low"
        elif performance_score >= 60:
            return "medium"
        elif performance_score >= 40:
            return "high"
        else:
            return "critical"

    def _estimate_improvement(self, suggested_indexes: List[Dict[str, Any]], plan_analysis: Dict[str, Any]) -> Optional[float]:
        if not suggested_indexes and not plan_analysis.get('issues'):
            return None
        
        improvement = 0.0
        
        if suggested_indexes:
            improvement += len(suggested_indexes) * 25.0
        
        if plan_analysis.get('efficiency_score', 100) < 80:
            improvement += (80 - plan_analysis['efficiency_score']) * 0.7
        
        return min(85.0, improvement)

    def _get_operation_info(self, operation: str, args: List[str]) -> Dict[str, Any]:
        operation_info = {
            "complexity": "O(log n)",
            "memory_impact": "medium",
            "blocking": False,
            "thread_safe": True
        }
        
        # Qdrant operation-specific information
        if operation == "search":
            operation_info.update({
                "complexity": "O(log n)",
                "memory_impact": "medium",
                "blocking": False,
                "description": "Vector similarity search using HNSW index"
            })
        elif operation == "scroll":
            operation_info.update({
                "complexity": "O(n)",
                "memory_impact": "high",
                "blocking": False,
                "description": "Iterate through all points in collection"
            })
        elif operation == "count":
            operation_info.update({
                "complexity": "O(1)",
                "memory_impact": "low",
                "blocking": False,
                "description": "Count points in collection"
            })
        elif operation == "info":
            operation_info.update({
                "complexity": "O(1)",
                "memory_impact": "low",
                "blocking": False,
                "description": "Get collection information"
            })
        
        return operation_info

    def _get_performance_implications(self, operation: str, args: List[str]) -> List[str]:
        implications = []
        
        if operation == "search":
            implications.append("Performance depends on HNSW parameters")
            implications.append("Memory usage increases with result size")
            
            if args:
                for arg in args:
                    if "limit=" in arg and ("1000" in arg or "500" in arg):
                        implications.append("Large limits may impact performance")
                    if "with_payload=true" in arg.lower():
                        implications.append("Payload retrieval increases memory usage")
                    if "with_vector=true" in arg.lower():
                        implications.append("Vector retrieval increases memory usage")
        
        if operation == "scroll":
            implications.append("May be expensive for large collections")
            implications.append("Memory usage depends on limit and payload size")
        
        if operation == "count":
            implications.append("Generally fast, but may be affected by filters")
        
        return implications

    def _get_operation_optimizations(self, operation: str, args: List[str]) -> List[str]:
        optimizations = []
        
        if operation == "search":
            optimizations.append("Use appropriate limit to reduce computation")
            optimizations.append("Disable payload and vector retrieval if not needed")
            optimizations.append("Consider using filters to reduce search space")
            optimizations.append("Optimize HNSW parameters for your use case")
        
        if operation == "scroll":
            optimizations.append("Use pagination with small limits")
            optimizations.append("Consider using search instead when possible")
            optimizations.append("Disable unnecessary payload/vector retrieval")
        
        if operation == "count":
            optimizations.append("Use specific filters when counting subsets")
        
        return optimizations

    def _extract_collection_name(self, query_text: str) -> Optional[str]:
        try:
            # Try to extract collection name from query
            parts = query_text.split()
            if len(parts) >= 2:
                # Look for collection name in different positions
                for i, part in enumerate(parts):
                    if part.lower() == "collection" and i + 1 < len(parts):
                        return parts[i + 1]
                    if part.startswith("collection="):
                        return part.split("=")[1]
                    if part.startswith("/collections/"):
                        return part.split("/")[-1]
        except:
            pass
        return None

    def _generate_qdrant_specific_recommendations(self, metrics: List[QueryMetric]) -> List[str]:
        recommendations = []
        
        # Analyze operation distribution
        operation_counts = {}
        for metric in metrics:
            operation = metric.query_type
            if operation not in operation_counts:
                operation_counts[operation] = 0
            operation_counts[operation] += 1
        
        # Check for expensive operations
        if operation_counts.get('scroll', 0) > operation_counts.get('search', 0):
            recommendations.append("High scroll operation count - consider using search instead")
        
        # Check for large result sets
        large_result_operations = [m for m in metrics if m.affected_rows and m.affected_rows > 100]
        if len(large_result_operations) > len(metrics) * 0.2:  # > 20% of operations
            recommendations.append("Many operations return large result sets - consider pagination")
        
        # Check for performance issues
        slow_operations = [m for m in metrics if m.performance_level in ["slow", "critical"]]
        if len(slow_operations) > len(metrics) * 0.1:  # > 10% of operations
            recommendations.append("High percentage of slow operations - review HNSW configuration")
        
        return recommendations

    def get_query_plan_analysis(self, query_text: str, database: str) -> Dict[str, Any]:
        self.obs.log_info(f"get_query_plan_analysis database={database}")
        
        try:
            explain_result = self.explain_query(query_text, database)
            
            analysis = {
                "query": query_text,
                "database": database,
                "explain": explain_result,
                "analysis": {}
            }
            
            if explain_result.get("success"):
                analysis["analysis"]["operation_info"] = explain_result.get("operation_info", {})
                analysis["analysis"]["performance_implications"] = explain_result.get("performance_implications", [])
                analysis["analysis"]["optimization_suggestions"] = explain_result.get("optimization_suggestions", [])
                
                # Add Qdrant-specific analysis
                query_parts = query_text.split()
                if query_parts:
                    operation = query_parts[0].lower()
                    analysis["analysis"]["qdrant_specific"] = self._get_qdrant_specific_analysis(operation, query_parts[1:])
            
            return analysis
        
        except Exception as e:
            self.obs.log_error(f"Failed to get query plan analysis: {e}")
            return {
                "query": query_text,
                "database": database,
                "error": str(e)
            }

    def _get_qdrant_specific_analysis(self, operation: str, args: List[str]) -> Dict[str, Any]:
        analysis = {
            "hnsw_performance": "good",
            "memory_efficiency": "medium",
            "best_practices": []
        }
        
        if operation == "search":
            analysis["best_practices"] = [
                "Use appropriate limit values",
                "Disable unnecessary payload/vector retrieval",
                "Consider using filters to reduce search space"
            ]
            
            # Check for performance issues in arguments
            query_text = " ".join([operation] + args)
            if "limit=1000" in query_text or "limit=500" in query_text:
                analysis["hnsw_performance"] = "poor"
                analysis["best_practices"].append("Reduce limit for better performance")
        
        if operation == "scroll":
            analysis["memory_efficiency"] = "low"
            analysis["best_practices"] = [
                "Use pagination with small limits",
                "Consider search instead of scroll when possible"
            ]
        
        return analysis

    def get_schema_analysis(self, database: str) -> Dict[str, Any]:
        self.obs.log_info(f"get_schema_analysis database={database}")
        
        try:
            from .qdrant_query_collector import QdrantQueryCollector
            collector = QdrantQueryCollector(self.session)
            
            # Get cluster and collection information
            cluster_info = get_cluster_info(self.session)
            collections_info = list_collections(self.session)
            
            analysis = {
                "database_type": "qdrant",
                "cluster_info": cluster_info.result.get("result", {}) if cluster_info.success else {},
                "collections_info": collections_info.result.get("collections", []) if collections_info.success else [],
                "collection_analysis": {},
                "recommendations": []
            }
            
            # Analyze each collection
            if collections_info.success:
                collections = collections_info.result.get("collections", [])
                for collection in collections[:10]:  # Limit to first 10 collections
                    collection_name = collection.get("name", "unknown")
                    collection_stats = collector.get_collection_statistics(collection_name)
                    collection_hnsw = collector.get_hnsw_performance_analysis(collection_name)
                    
                    analysis["collection_analysis"][collection_name] = {
                        "statistics": collection_stats,
                        "hnsw_analysis": collection_hnsw
                    }
            
            # Generate recommendations
            total_collections = len(collections) if collections_info.success else 0
            if total_collections > 50:
                analysis["recommendations"].append("High number of collections - consider consolidation")
            
            # Check for performance issues in collections
            performance_issues = 0
            for collection_name, collection_data in analysis["collection_analysis"].items():
                hnsw_data = collection_data.get("hnsw_analysis", {})
                averages = hnsw_data.get("averages", {})
                
                if averages.get("avg_search_time_ms", 0) > 100:
                    performance_issues += 1
            
            if performance_issues > total_collections * 0.3:  # > 30% of collections have issues
                analysis["recommendations"].append("Multiple collections have performance issues - review HNSW configuration")
            
            return {
                "success": True,
                "database": database,
                "schema": analysis,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            self.obs.log_error(f"Failed to get schema analysis: {e}")
            return {
                "success": False,
                "database": database,
                "error": str(e)
            }

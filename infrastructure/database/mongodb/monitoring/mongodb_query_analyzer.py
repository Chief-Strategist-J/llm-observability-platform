import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.database import Database

project_root = Path(__file__).resolve().parents[4]
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


class MongoDBQueryAnalyzer(IQueryAnalyzer):
    def __init__(self, client: MongoClient):
        self.client = client
        self.obs = ObservabilityClient(service_name="mongodb-query-analyzer")

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
            db = self.client[database]
            
            if query_text.strip().startswith("find"):
                return self._explain_find_query(query_text, db)
            elif query_text.strip().startswith("aggregate"):
                return self._explain_aggregate_query(query_text, db)
            else:
                return self._explain_generic_query(query_text, db)
        
        except Exception as e:
            self.obs.log_error(f"Failed to explain query: {e}")
            return {}

    def suggest_indexes(self, query_text: str, database: str) -> List[Dict[str, Any]]:
        self.obs.log_info(f"suggest_indexes database={database}")
        
        suggestions = []
        
        try:
            plan = self.explain_query(query_text, database)
            
            if self._has_collection_scan(plan):
                collection_name = self._extract_collection_name(query_text)
                if collection_name:
                    filter_fields = self._extract_filter_fields(query_text)
                    if filter_fields:
                        suggestions.append({
                            'collection': collection_name,
                            'fields': filter_fields,
                            'type': 'compound',
                            'reason': 'Query performs collection scan, index would improve performance'
                        })
            
            sort_fields = self._extract_sort_fields(query_text)
            if sort_fields:
                collection_name = self._extract_collection_name(query_text)
                if collection_name:
                    suggestions.append({
                        'collection': collection_name,
                        'fields': sort_fields,
                        'type': 'sort',
                        'reason': 'Query includes sort operation, index would improve sorting performance'
                    })
            
            join_fields = self._extract_join_fields(query_text)
            if join_fields:
                collection_name = self._extract_collection_name(query_text)
                if collection_name:
                    suggestions.append({
                        'collection': collection_name,
                        'fields': join_fields,
                        'type': 'join',
                        'reason': 'Query includes lookup operations, index would improve join performance'
                    })
        
        except Exception as e:
            self.obs.log_error(f"Failed to suggest indexes: {e}")
        
        return suggestions

    def generate_performance_report(self, database: str, period_start: datetime, period_end: datetime) -> PerformanceReport:
        self.obs.log_info(f"generate_performance_report database={database}")
        
        try:
            from .mongodb_query_collector import MongoDBQueryCollector
            collector = MongoDBQueryCollector(self.client)
            
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
        
        if self._has_complex_aggregation(query_text):
            score -= 10
        
        if self._has_large_result_set(query_text, database):
            score -= 15
        
        if self._has_regex_query(query_text):
            score -= 20
        
        return max(0, score)

    def _generate_query_recommendations(self, query_text: str, database: str, plan_analysis: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        if plan_analysis.get('issues'):
            recommendations.extend(plan_analysis['issues'])
        
        if self._has_collection_scan(plan_analysis):
            recommendations.append("Query performs collection scan - consider adding appropriate indexes")
        
        if self._has_complex_aggregation(query_text):
            recommendations.append("Complex aggregation detected - consider breaking into simpler stages")
        
        if self._has_regex_query(query_text):
            recommendations.append("Regex query detected - ensure regex is optimized and anchored")
        
        if self._has_large_limit(query_text):
            recommendations.append("Large limit detected - consider implementing pagination")
        
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
            improvement += len(suggested_indexes) * 15.0
        
        if plan_analysis.get('efficiency_score', 100) < 80:
            improvement += (80 - plan_analysis['efficiency_score']) * 0.5
        
        return min(90.0, improvement)

    def _explain_find_query(self, query_text: str, db: Database) -> Dict[str, Any]:
        try:
            collection_name, filter_dict = self._parse_find_query(query_text)
            if collection_name and filter_dict:
                collection = db[collection_name]
                return collection.find(filter_dict).explain()
        except Exception as e:
            self.obs.log_error(f"Failed to explain find query: {e}")
        return {}

    def _explain_aggregate_query(self, query_text: str, db: Database) -> Dict[str, Any]:
        try:
            collection_name, pipeline = self._parse_aggregate_query(query_text)
            if collection_name and pipeline:
                collection = db[collection_name]
                return collection.aggregate(pipeline).explain()
        except Exception as e:
            self.obs.log_error(f"Failed to explain aggregate query: {e}")
        return {}

    def _explain_generic_query(self, query_text: str, db: Database) -> Dict[str, Any]:
        return {}

    def _parse_find_query(self, query_text: str) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
        try:
            import ast
            if "find(" in query_text and "{" in query_text:
                parts = query_text.split("find(")
                if len(parts) > 1:
                    collection_part = parts[0].strip().split()[-1]
                    filter_part = parts[1].split(")")[0]
                    
                    try:
                        filter_dict = ast.literal_eval(filter_part)
                        return collection_part, filter_dict
                    except:
                        pass
        except:
            pass
        return None, None

    def _parse_aggregate_query(self, query_text: str) -> tuple[Optional[str], Optional[List[Dict[str, Any]]]]:
        try:
            import ast
            if "aggregate(" in query_text and "[" in query_text:
                parts = query_text.split("aggregate(")
                if len(parts) > 1:
                    collection_part = parts[0].strip().split()[-1]
                    pipeline_part = parts[1].split(")")[0]
                    
                    try:
                        pipeline = ast.literal_eval(pipeline_part)
                        return collection_part, pipeline
                    except:
                        pass
        except:
            pass
        return None, None

    def _has_collection_scan(self, plan: Dict[str, Any]) -> bool:
        return "COLLSCAN" in str(plan).upper()

    def _extract_collection_name(self, query_text: str) -> Optional[str]:
        if "find(" in query_text:
            parts = query_text.split("find(")
            if len(parts) > 1:
                return parts[0].strip().split()[-1]
        elif "aggregate(" in query_text:
            parts = query_text.split("aggregate(")
            if len(parts) > 1:
                return parts[0].strip().split()[-1]
        return None

    def _extract_filter_fields(self, query_text: str) -> List[str]:
        fields = []
        try:
            import ast
            if "{" in query_text and "}" in query_text:
                start = query_text.find("{")
                end = query_text.rfind("}") + 1
                filter_str = query_text[start:end]
                
                try:
                    filter_dict = ast.literal_eval(filter_str)
                    if isinstance(filter_dict, dict):
                        fields.extend(filter_dict.keys())
                except:
                    pass
        except:
            pass
        return fields

    def _extract_sort_fields(self, query_text: str) -> List[str]:
        fields = []
        if "sort(" in query_text:
            try:
                import ast
                parts = query_text.split("sort(")
                if len(parts) > 1:
                    sort_part = parts[1].split(")")[0]
                    try:
                        sort_dict = ast.literal_eval(sort_part)
                        if isinstance(sort_dict, dict):
                            fields.extend(sort_dict.keys())
                    except:
                        pass
            except:
                pass
        return fields

    def _extract_join_fields(self, query_text: str) -> List[str]:
        fields = []
        if "$lookup" in query_text:
            try:
                import ast
                if "{" in query_text and "}" in query_text:
                    start = query_text.find("{")
                    end = query_text.rfind("}") + 1
                    lookup_str = query_text[start:end]
                    
                    if "localField" in lookup_str:
                        fields.append("localField")
                    if "foreignField" in lookup_str:
                        fields.append("foreignField")
            except:
                pass
        return fields

    def _has_complex_aggregation(self, query_text: str) -> bool:
        return query_text.count("$") > 5 or "$graphLookup" in query_text

    def _has_large_result_set(self, query_text: str, database: str) -> bool:
        if "limit(" in query_text:
            try:
                parts = query_text.split("limit(")
                if len(parts) > 1:
                    limit_part = parts[1].split(")")[0]
                    try:
                        limit = int(limit_part)
                        return limit > 1000
                    except:
                        pass
        return False

    def _has_regex_query(self, query_text: str) -> bool:
        return "$regex" in query_text or "/.*" in query_text

    def _has_large_limit(self, query_text: str) -> bool:
        if "limit(" in query_text:
            try:
                parts = query_text.split("limit(")
                if len(parts) > 1:
                    limit_part = parts[1].split(")")[0]
                    try:
                        limit = int(limit_part)
                        return limit > 500
                    except:
                        pass
        return False

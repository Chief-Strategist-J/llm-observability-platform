import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from neo4j import GraphDatabase, Driver

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
from ..client.neo4j_client import execute_query


class Neo4jQueryAnalyzer(IQueryAnalyzer):
    def __init__(self, driver: Driver):
        self.driver = driver
        self.obs = ObservabilityClient(service_name="neo4j-query-analyzer")

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
            explain_query = f"EXPLAIN {query_text}"
            result = execute_query(self.driver, explain_query, {}, database)
            
            if result.success and result.records:
                plan = result.records[0].get("plan", {})
                return {
                    "plan": plan,
                    "execution_time_ms": result.execution_time_ms,
                    "success": True
                }
            else:
                return {
                    "success": False,
                    "error": result.error_message,
                    "execution_time_ms": result.execution_time_ms
                }
        
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
            plan = self.explain_query(query_text, database)
            
            if self._has_node_by_id_scan(plan):
                labels = self._extract_labels_from_query(query_text)
                for label in labels:
                    suggestions.append({
                        'type': 'node_label',
                        'label': label,
                        'properties': [],
                        'reason': f'Query scans nodes with label {label}, consider adding indexes'
                    })
            
            properties = self._extract_properties_from_query(query_text)
            labels = self._extract_labels_from_query(query_text)
            
            for label in labels:
                for prop in properties:
                    suggestions.append({
                        'type': 'node_property',
                        'label': label,
                        'properties': [prop],
                        'reason': f'Query filters on {label}.{prop}, consider adding index'
                    })
            
            if self._has_relationship_scan(query_text):
                rel_types = self._extract_relationship_types(query_text)
                for rel_type in rel_types:
                    suggestions.append({
                        'type': 'relationship',
                        'relationship_type': rel_type,
                        'reason': f'Query uses relationship type {rel_type}, consider relationship index'
                    })
        
        except Exception as e:
            self.obs.log_error(f"Failed to suggest indexes: {e}")
        
        return suggestions

    def generate_performance_report(self, database: str, period_start: datetime, period_end: datetime) -> PerformanceReport:
        self.obs.log_info(f"generate_performance_report database={database}")
        
        try:
            from .neo4j_query_collector import Neo4jQueryCollector
            collector = Neo4jQueryCollector(self.driver)
            
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
        
        if self._has_cartesian_product(query_text):
            score -= 30
        
        if self._has_deep_path(query_text):
            score -= 20
        
        if self._has_large_result_set(query_text):
            score -= 15
        
        if self._has_multiple_match_clauses(query_text):
            score -= 10
        
        return max(0, score)

    def _generate_query_recommendations(self, query_text: str, database: str, plan_analysis: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        if plan_analysis.get('issues'):
            recommendations.extend(plan_analysis['issues'])
        
        if self._has_cartesian_product(query_text):
            recommendations.append("Query may create Cartesian product - consider adding relationship constraints")
        
        if self._has_deep_path(query_text):
            recommendations.append("Deep path traversal detected - consider query optimization or path limits")
        
        if self._has_multiple_match_clauses(query_text):
            recommendations.append("Multiple MATCH clauses detected - consider combining or optimizing")
        
        if not self._has_limit_clause(query_text):
            recommendations.append("No LIMIT clause detected - consider adding to prevent large result sets")
        
        labels = self._extract_labels_from_query(query_text)
        if len(labels) > 3:
            recommendations.append("Query involves many labels - consider schema optimization")
        
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
            improvement += len(suggested_indexes) * 20.0
        
        if plan_analysis.get('efficiency_score', 100) < 80:
            improvement += (80 - plan_analysis['efficiency_score']) * 0.6
        
        return min(85.0, improvement)

    def _has_node_by_id_scan(self, plan: Dict[str, Any]) -> bool:
        plan_str = str(plan).lower()
        return "nodebyidscan" in plan_str or "allnodes" in plan_str

    def _extract_labels_from_query(self, query_text: str) -> List[str]:
        labels = []
        try:
            import re
            pattern = r'\(([^:]+):([^)]+)\)'
            matches = re.findall(pattern, query_text)
            for match in matches:
                labels.append(match[1])
        except:
            pass
        return list(set(labels))

    def _extract_properties_from_query(self, query_text: str) -> List[str]:
        properties = []
        try:
            import re
            pattern = r'\.(\w+)\s*='
            matches = re.findall(pattern, query_text)
            properties.extend(matches)
        except:
            pass
        return list(set(properties))

    def _extract_relationship_types(self, query_text: str) -> List[str]:
        rel_types = []
        try:
            import re
            pattern = r'\[([^:]+):([^]]+)\]'
            matches = re.findall(pattern, query_text)
            for match in matches:
                rel_types.append(match[1])
        except:
            pass
        return list(set(rel_types))

    def _has_relationship_scan(self, query_text: str) -> bool:
        return "-[" in query_text or "]-[" in query_text

    def _has_cartesian_product(self, query_text: str) -> bool:
        match_count = query_text.upper().count("MATCH")
        return match_count > 1 and "WHERE" not in query_text.upper()

    def _has_deep_path(self, query_text: str) -> bool:
        return query_text.count("-[") > 4

    def _has_large_result_set(self, query_text: str) -> bool:
        return "LIMIT" not in query_text.upper() and "COUNT(" not in query_text.upper()

    def _has_multiple_match_clauses(self, query_text: str) -> bool:
        return query_text.upper().count("MATCH") > 1

    def _has_limit_clause(self, query_text: str) -> bool:
        return "LIMIT" in query_text.upper()

    def get_query_plan_analysis(self, query_text: str, database: str) -> Dict[str, Any]:
        self.obs.log_info(f"get_query_plan_analysis database={database}")
        
        try:
            explain_result = self.explain_query(query_text, database)
            profile_result = self._profile_query(query_text, database)
            
            analysis = {
                "query": query_text,
                "database": database,
                "explain": explain_result,
                "profile": profile_result,
                "analysis": {}
            }
            
            if explain_result.get("success"):
                plan = explain_result.get("plan", {})
                plan_analysis = QueryPlanAnalyzer.analyze_plan_efficiency(plan)
                analysis["analysis"]["plan_efficiency"] = plan_analysis
            
            if profile_result.get("success"):
                profile = profile_result.get("profile", {})
                analysis["analysis"]["execution_stats"] = {
                    "db_hits": profile.get("dbHits", 0),
                    "rows": profile.get("rows", 0),
                    "memory_usage": profile.get("memory", 0)
                }
            
            return analysis
        
        except Exception as e:
            self.obs.log_error(f"Failed to get query plan analysis: {e}")
            return {
                "query": query_text,
                "database": database,
                "error": str(e)
            }

    def _profile_query(self, query_text: str, database: str) -> Dict[str, Any]:
        try:
            profile_query = f"PROFILE {query_text}"
            result = execute_query(self.driver, profile_query, {}, database)
            
            if result.success and result.records:
                profile = result.records[0].get("profile", {})
                return {
                    "profile": profile,
                    "execution_time_ms": result.execution_time_ms,
                    "success": True
                }
            else:
                return {
                    "success": False,
                    "error": result.error_message,
                    "execution_time_ms": result.execution_time_ms
                }
        
        except Exception as e:
            self.obs.log_error(f"Failed to profile query: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_schema_analysis(self, database: str) -> Dict[str, Any]:
        self.obs.log_info(f"get_schema_analysis database={database}")
        
        try:
            analysis = {}
            
            label_query = "CALL db.labels() YIELD label RETURN label"
            result = execute_query(self.driver, label_query, {}, database)
            if result.success:
                analysis["labels"] = [record["label"] for record in result.records]
            
            rel_type_query = "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
            result = execute_query(self.driver, rel_type_query, {}, database)
            if result.success:
                analysis["relationship_types"] = [record["relationshipType"] for record in result.records]
            
            index_query = "CALL db.indexes() YIELD name, type, entityType, properties RETURN name, type, entityType, properties"
            result = execute_query(self.driver, index_query, {}, database)
            if result.success:
                analysis["indexes"] = [
                    {
                        "name": record["name"],
                        "type": record["type"],
                        "entity_type": record["entityType"],
                        "properties": record["properties"]
                    }
                    for record in result.records
                ]
            
            constraint_query = "CALL db.constraints() YIELD name, description RETURN name, description"
            result = execute_query(self.driver, constraint_query, {}, database)
            if result.success:
                analysis["constraints"] = [
                    {
                        "name": record["name"],
                        "description": record["description"]
                    }
                    for record in result.records
                ]
            
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

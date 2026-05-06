import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extensions import connection as Connection

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
from ..client.postgres_client import execute_query, explain_query


class PostgreSQLQueryAnalyzer(IQueryAnalyzer):
    def __init__(self, connection: Connection):
        self.connection = connection
        self.obs = ObservabilityClient(service_name="postgres-query-analyzer")

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
            result = explain_query(self.connection, query_text, None, analyze=True)
            
            if result.get("success"):
                return {
                    "plan": result.get("plan", {}),
                    "execution_time_ms": result.get("execution_time_ms", 0),
                    "success": True
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error"),
                    "execution_time_ms": result.get("execution_time_ms", 0)
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
            
            if self._has_seq_scan(plan):
                table_name = self._extract_table_from_query(query_text)
                where_columns = self._extract_where_columns(query_text)
                
                if table_name and where_columns:
                    suggestions.append({
                        'type': 'btree',
                        'table': table_name,
                        'columns': where_columns,
                        'reason': f'Query performs sequential scan on {table_name}, index on {", ".join(where_columns)} would improve performance'
                    })
            
            join_columns = self._extract_join_columns(query_text)
            if join_columns:
                for join_info in join_columns:
                    suggestions.append({
                        'type': 'btree',
                        'table': join_info['table'],
                        'columns': [join_info['column']],
                        'reason': f'Query joins on {join_info["table"]}.{join_info["column"]}, index would improve join performance'
                    })
            
            order_columns = self._extract_order_columns(query_text)
            if order_columns:
                table_name = self._extract_table_from_query(query_text)
                if table_name:
                    suggestions.append({
                        'type': 'btree',
                        'table': table_name,
                        'columns': order_columns,
                        'reason': f'Query orders by {", ".join(order_columns)}, index would improve sorting performance'
                    })
        
        except Exception as e:
            self.obs.log_error(f"Failed to suggest indexes: {e}")
        
        return suggestions

    def generate_performance_report(self, database: str, period_start: datetime, period_end: datetime) -> PerformanceReport:
        self.obs.log_info(f"generate_performance_report database={database}")
        
        try:
            from .postgres_query_collector import PostgreSQLQueryCollector
            collector = PostgreSQLQueryCollector(self.connection)
            
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
        
        if self._has_seq_scan(plan_analysis):
            score -= 25
        
        if self._has_nested_loops(plan_analysis):
            score -= 20
        
        if self._has_hash_join(plan_analysis):
            score -= 15
        
        if self._has_sort_operation(plan_analysis):
            score -= 10
        
        if self._has_aggregate(query_text):
            score -= 5
        
        return max(0, score)

    def _generate_query_recommendations(self, query_text: str, database: str, plan_analysis: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        if plan_analysis.get('issues'):
            recommendations.extend(plan_analysis['issues'])
        
        if self._has_seq_scan(plan_analysis):
            recommendations.append("Query performs sequential scan - consider adding appropriate indexes")
        
        if self._has_nested_loops(plan_analysis):
            recommendations.append("Query uses nested loops - consider optimizing joins or adding indexes")
        
        if self._has_sort_operation(plan_analysis):
            recommendations.append("Query requires sorting - consider adding indexes or reducing result set")
        
        if self._has_aggregate(query_text) and not self._has_group_by_index(query_text):
            recommendations.append("Aggregation without index - consider adding index on GROUP BY columns")
        
        if not self._has_limit_clause(query_text):
            recommendations.append("No LIMIT clause detected - consider adding to prevent large result sets")
        
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

    def _has_seq_scan(self, plan: Dict[str, Any]) -> bool:
        plan_text = str(plan.get("plan", {})).lower()
        return "seq scan" in plan_text

    def _has_nested_loops(self, plan: Dict[str, Any]) -> bool:
        plan_text = str(plan.get("plan", {})).lower()
        return "nested loop" in plan_text

    def _has_hash_join(self, plan: Dict[str, Any]) -> bool:
        plan_text = str(plan.get("plan", {})).lower()
        return "hash join" in plan_text

    def _has_sort_operation(self, plan: Dict[str, Any]) -> bool:
        plan_text = str(plan.get("plan", {})).lower()
        return "sort" in plan_text

    def _extract_table_from_query(self, query_text: str) -> Optional[str]:
        try:
            import re
            match = re.search(r'FROM\s+(\w+)', query_text, re.IGNORECASE)
            if match:
                return match.group(1)
        except:
            pass
        return None

    def _extract_where_columns(self, query_text: str) -> List[str]:
        columns = []
        try:
            import re
            where_match = re.search(r'WHERE\s+(.+?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|\s+LIMIT|$)', query_text, re.IGNORECASE)
            if where_match:
                where_clause = where_match.group(1)
                column_matches = re.findall(r'(\w+)\s*=', where_clause)
                columns.extend(column_matches)
        except:
            pass
        return list(set(columns))

    def _extract_join_columns(self, query_text: str) -> List[Dict[str, Any]]:
        joins = []
        try:
            import re
            join_pattern = r'JOIN\s+(\w+)\s+ON\s+(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)'
            matches = re.findall(join_pattern, query_text, re.IGNORECASE)
            
            for match in matches:
                joins.append({
                    'table': match[0],
                    'left_table': match[1],
                    'left_column': match[2],
                    'right_table': match[3],
                    'right_column': match[4]
                })
        except:
            pass
        return joins

    def _extract_order_columns(self, query_text: str) -> List[str]:
        columns = []
        try:
            import re
            order_match = re.search(r'ORDER\s+BY\s+(.+?)(?:\s+LIMIT|$)', query_text, re.IGNORECASE)
            if order_match:
                order_clause = order_match.group(1)
                column_matches = re.findall(r'(\w+)', order_clause)
                columns.extend(column_matches)
        except:
            pass
        return list(set(columns))

    def _has_aggregate(self, query_text: str) -> bool:
        aggregate_functions = ['COUNT(', 'SUM(', 'AVG(', 'MIN(', 'MAX(', 'STDDEV(']
        return any(func in query_text.upper() for func in aggregate_functions)

    def _has_group_by_index(self, query_text: str) -> bool:
        try:
            import re
            group_match = re.search(r'GROUP\s+BY\s+(.+?)(?:\s+ORDER\s+BY|\s+LIMIT|$)', query_text, re.IGNORECASE)
            if group_match:
                return True
        except:
            pass
        return False

    def _has_limit_clause(self, query_text: str) -> bool:
        return "LIMIT" in query_text.upper()

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
                plan = explain_result.get("plan", {})
                plan_analysis = QueryPlanAnalyzer.analyze_plan_efficiency(plan)
                analysis["analysis"]["plan_efficiency"] = plan_analysis
                
                analysis["analysis"]["operations"] = self._analyze_plan_operations(plan)
                analysis["analysis"]["cost_analysis"] = self._analyze_plan_cost(plan)
            
            return analysis
        
        except Exception as e:
            self.obs.log_error(f"Failed to get query plan analysis: {e}")
            return {
                "query": query_text,
                "database": database,
                "error": str(e)
            }

    def _analyze_plan_operations(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        plan_text = str(plan.get("plan_text", ""))
        
        operations = {
            "sequential_scans": plan_text.count("Seq Scan"),
            "index_scans": plan_text.count("Index Scan"),
            "bitmap_scans": plan_text.count("Bitmap"),
            "nested_loops": plan_text.count("Nested Loop"),
            "hash_joins": plan_text.count("Hash Join"),
            "merge_joins": plan_text.count("Merge Join"),
            "sorts": plan_text.count("Sort"),
            "aggregates": plan_text.count("Aggregate"),
            "limits": plan_text.count("Limit")
        }
        
        return operations

    def _analyze_plan_cost(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        plan_text = str(plan.get("plan_text", ""))
        
        cost_analysis = {
            "estimated_cost": plan.get("estimated_cost"),
            "estimated_rows": plan.get("estimated_rows"),
            "cost_per_row": None
        }
        
        if cost_analysis["estimated_cost"] and cost_analysis["estimated_rows"]:
            cost_analysis["cost_per_row"] = cost_analysis["estimated_cost"] / cost_analysis["estimated_rows"]
        
        return cost_analysis

    def get_schema_analysis(self, database: str) -> Dict[str, Any]:
        self.obs.log_info(f"get_schema_analysis database={database}")
        
        try:
            analysis = {}
            
            table_query = """
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
            """
            result = execute_query(self.connection, table_query)
            if result.success:
                tables = {}
                for record in result.records:
                    table_name = record['table_name']
                    if table_name not in tables:
                        tables[table_name] = []
                    tables[table_name].append({
                        'column': record['column_name'],
                        'type': record['data_type'],
                        'nullable': record['is_nullable']
                    })
                analysis["tables"] = tables
            
            index_query = """
            SELECT schemaname, tablename, indexname, indexdef
            FROM pg_indexes 
            WHERE schemaname = 'public'
            """
            result = execute_query(self.connection, index_query)
            if result.success:
                analysis["indexes"] = result.records
            
            constraint_query = """
            SELECT conname, contype, pg_get_constraintdef(oid) as definition
            FROM pg_constraint 
            WHERE connamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
            """
            result = execute_query(self.connection, constraint_query)
            if result.success:
                analysis["constraints"] = result.records
            
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

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from cassandra.cluster import Session

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
from ..client.cassandra_client import execute_query, explain_query


class CassandraQueryAnalyzer(IQueryAnalyzer):
    def __init__(self, session: Session):
        self.session = session
        self.obs = ObservabilityClient(service_name="cassandra-query-analyzer")

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
            result = explain_query(self.session, query_text)
            
            if result.get("success"):
                return {
                    "plan": result.get("query_plan", {}),
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
            
            if self._has_full_table_scan(plan):
                table_name = self._extract_table_from_query(query_text)
                where_columns = self._extract_where_columns(query_text)
                
                if table_name and where_columns:
                    suggestions.append({
                        'type': 'btree',
                        'table': table_name,
                        'columns': where_columns,
                        'reason': f'Query performs full table scan on {table_name}, index on {", ".join(where_columns)} would improve performance'
                    })
            
            partition_key = self._extract_partition_key_from_query(query_text)
            if partition_key:
                table_name = self._extract_table_from_query(query_text)
                if table_name:
                    suggestions.append({
                        'type': 'partition_key',
                        'table': table_name,
                        'columns': [partition_key],
                        'reason': f'Query uses partition key {partition_key} on table {table_name}, ensure proper partitioning strategy'
                    })
            
            clustering_columns = self._extract_clustering_columns_from_query(query_text)
            if clustering_columns:
                table_name = self._extract_table_from_query(query_text)
                if table_name:
                    suggestions.append({
                        'type': 'clustering_key',
                        'table': table_name,
                        'columns': clustering_columns,
                        'reason': f'Query benefits from clustering on {", ".join(clustering_columns)} for table {table_name}'
                    })
        
        except Exception as e:
            self.obs.log_error(f"Failed to suggest indexes: {e}")
        
        return suggestions

    def generate_performance_report(self, database: str, period_start: datetime, period_end: datetime) -> PerformanceReport:
        self.obs.log_info(f"generate_performance_report database={database}")
        
        try:
            from .cassandra_query_collector import CassandraQueryCollector
            collector = CassandraQueryCollector(self.session)
            
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
        
        if self._has_full_table_scan(plan_analysis):
            score -= 30
        
        if self._has_allow_filtering(plan_analysis):
            score -= 20
        
        if self._has_large_result_set(query_text):
            score -= 15
        
        if self._has_multiple_partitions(query_text):
            score -= 10
        
        return max(0, score)

    def _generate_query_recommendations(self, query_text: str, database: str, plan_analysis: Dict[str, Any]) -> List[str]:
        recommendations = []
        
        if plan_analysis.get('issues'):
            recommendations.extend(plan_analysis['issues'])
        
        if self._has_full_table_scan(plan_analysis):
            recommendations.append("Query performs full table scan - consider adding appropriate indexes")
        
        if self._has_allow_filtering(plan_analysis):
            recommendations.append("Query uses ALLOW FILTERING - consider redesigning schema")
        
        if self._has_large_result_set(query_text):
            recommendations.append("Query may return large result set - consider adding LIMIT or filtering")
        
        if not self._uses_partition_key(query_text):
            recommendations.append("Query doesn't use partition key - consider query optimization")
        
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

    def _has_full_table_scan(self, plan: Dict[str, Any]) -> bool:
        plan_text = str(plan.get("plan", {})).lower()
        return "full scan" in plan_text or "sequential scan" in plan_text

    def _has_allow_filtering(self, plan: Dict[str, Any]) -> bool:
        plan_text = str(plan.get("plan", {})).lower()
        return "allow filtering" in plan_text

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

    def _extract_partition_key_from_query(self, query_text: str) -> Optional[str]:
        try:
            import re
            # Look for WHERE clause with primary key
            where_match = re.search(r'WHERE\s+(\w+)\s*=', query_text, re.IGNORECASE)
            if where_match:
                return where_match.group(1)
        except:
            pass
        return None

    def _extract_clustering_columns_from_query(self, query_text: str) -> List[str]:
        columns = []
        try:
            import re
            # Look for ORDER BY clause
            order_match = re.search(r'ORDER\s+BY\s+(.+?)(?:\s+LIMIT|$)', query_text, re.IGNORECASE)
            if order_match:
                order_clause = order_match.group(1)
                column_matches = re.findall(r'(\w+)', order_clause)
                columns.extend(column_matches)
        except:
            pass
        return list(set(columns))

    def _has_large_result_set(self, query_text: str) -> bool:
        return "LIMIT" not in query_text.upper() and "COUNT(" not in query_text.upper()

    def _has_multiple_partitions(self, query_text: str) -> bool:
        # Check if query spans multiple partitions
        return "IN" in query_text.upper() or "UNION" in query_text.upper()

    def _uses_partition_key(self, query_text: str) -> bool:
        partition_key = self._extract_partition_key_from_query(query_text)
        return partition_key is not None

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
                
                analysis["analysis"]["trace_analysis"] = self._analyze_trace_events(plan)
                analysis["analysis"]["performance_indicators"] = self._analyze_performance_indicators(plan)
            
            return analysis
        
        except Exception as e:
            self.obs.log_error(f"Failed to get query plan analysis: {e}")
            return {
                "query": query_text,
                "database": database,
                "error": str(e)
            }

    def _analyze_trace_events(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        events = plan.get("events", [])
        
        analysis = {
            "total_events": len(events),
            "slowest_event": None,
            "event_types": {},
            "total_duration_micros": 0
        }
        
        slowest_duration = 0
        for event in events:
            duration = event.get("source_elapsed", 0)
            analysis["total_duration_micros"] += duration
            
            if duration > slowest_duration:
                slowest_duration = duration
                analysis["slowest_event"] = {
                    "source": event.get("source"),
                    "description": event.get("description"),
                    "duration_micros": duration
                }
            
            event_type = event.get("source", "unknown")
            if event_type not in analysis["event_types"]:
                analysis["event_types"][event_type] = 0
            analysis["event_types"][event_type] += 1
        
        return analysis

    def _analyze_performance_indicators(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "has_full_scan": self._has_full_table_scan(plan),
            "has_allow_filtering": self._has_allow_filtering(plan),
            "trace_duration_micros": plan.get("duration_micros", 0),
            "event_count": len(plan.get("events", []))
        }

    def get_schema_analysis(self, database: str) -> Dict[str, Any]:
        self.obs.log_info(f"get_schema_analysis database={database}")
        
        try:
            analysis = {}
            
            # Get keyspace info
            keyspace_query = f"SELECT * FROM system_schema.keyspaces WHERE keyspace_name = '{self.session.keyspace}'"
            result = execute_query(self.session, keyspace_query)
            if result.success and result.records:
                analysis["keyspace"] = result.records[0]
            
            # Get table info
            table_query = "SELECT * FROM system_schema.tables WHERE keyspace_name = %s"
            result = execute_query(self.session, table_query, {"keyspace_name": self.session.keyspace})
            if result.success:
                tables = {}
                for record in result.records:
                    table_name = record["table_name"]
                    tables[table_name] = record
                analysis["tables"] = tables
            
            # Get index info
            index_query = "SELECT * FROM system_schema.indexes WHERE keyspace_name = %s"
            result = execute_query(self.session, index_query, {"keyspace_name": self.session.keyspace})
            if result.success:
                analysis["indexes"] = result.records
            
            # Get column info
            column_query = "SELECT * FROM system_schema.columns WHERE keyspace_name = %s"
            result = execute_query(self.session, column_query, {"keyspace_name": self.session.keyspace})
            if result.success:
                columns = {}
                for record in result.records:
                    table_name = record["table_name"]
                    if table_name not in columns:
                        columns[table_name] = []
                    columns[table_name].append(record)
                analysis["columns"] = columns
            
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

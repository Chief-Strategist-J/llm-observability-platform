import hashlib
import time
import re
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from .query_monitoring_interfaces import QueryMetric, QueryPerformanceLevel, QueryStatus


class QueryHashGenerator:
    @staticmethod
    def generate_hash(query_text: str, params: Optional[Dict[str, Any]] = None) -> str:
        normalized_query = QueryHashGenerator._normalize_query(query_text)
        if params:
            param_str = str(sorted(params.items()))
            combined = f"{normalized_query}:{param_str}"
        else:
            combined = normalized_query
        
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    @staticmethod
    def _normalize_query(query: str) -> str:
        query = re.sub(r'\s+', ' ', query.strip())
        query = re.sub(r"'[^']*'", "'?'", query)
        query = re.sub(r'"[^"]*"', '"?"', query)
        query = re.sub(r'\b\d+\b', '?', query)
        query = query.lower()
        return query


class PerformanceClassifier:
    @staticmethod
    def classify_performance(execution_time_ms: float, thresholds: Dict[str, float]) -> QueryPerformanceLevel:
        if execution_time_ms >= thresholds.get('critical', 5000.0):
            return QueryPerformanceLevel.CRITICAL
        elif execution_time_ms >= thresholds.get('slow', 1000.0):
            return QueryPerformanceLevel.SLOW
        elif execution_time_ms >= thresholds.get('normal', 100.0):
            return QueryPerformanceLevel.NORMAL
        else:
            return QueryPerformanceLevel.FAST

    @staticmethod
    def get_default_thresholds() -> Dict[str, float]:
        return {
            'fast': 100.0,
            'normal': 1000.0,
            'slow': 5000.0,
            'critical': 10000.0
        }


class QueryMetricsAggregator:
    @staticmethod
    def aggregate_metrics(metrics: List[QueryMetric]) -> Dict[str, Any]:
        if not metrics:
            return {}

        total_queries = len(metrics)
        execution_times = [m.execution_time_ms for m in metrics]
        
        performance_distribution = {}
        for level in QueryPerformanceLevel:
            performance_distribution[level] = len([m for m in metrics if m.performance_level == level])

        slow_queries = [m for m in metrics if m.performance_level in [QueryPerformanceLevel.SLOW, QueryPerformanceLevel.CRITICAL]]
        
        return {
            'total_queries': total_queries,
            'avg_execution_time_ms': sum(execution_times) / total_queries,
            'min_execution_time_ms': min(execution_times),
            'max_execution_time_ms': max(execution_times),
            'median_execution_time_ms': sorted(execution_times)[total_queries // 2],
            'performance_distribution': performance_distribution,
            'slow_query_count': len(slow_queries),
            'slow_query_percentage': (len(slow_queries) / total_queries) * 100,
            'unique_queries': len(set(m.query_hash for m in metrics)),
            'error_rate': len([m for m in metrics if m.status == QueryStatus.ERROR]) / total_queries * 100
        }

    @staticmethod
    def get_top_slow_queries(metrics: List[QueryMetric], limit: int = 10) -> List[QueryMetric]:
        slow_metrics = [m for m in metrics if m.performance_level in [QueryPerformanceLevel.SLOW, QueryPerformanceLevel.CRITICAL]]
        return sorted(slow_metrics, key=lambda x: x.execution_time_ms, reverse=True)[:limit]


class QueryRecommendationEngine:
    @staticmethod
    def generate_recommendations(metrics: List[QueryMetric]) -> List[str]:
        recommendations = []
        
        if not metrics:
            return recommendations

        slow_queries = [m for m in metrics if m.performance_level in [QueryPerformanceLevel.SLOW, QueryPerformanceLevel.CRITICAL]]
        
        if len(slow_queries) > len(metrics) * 0.1:
            recommendations.append("High percentage of slow queries detected. Consider database optimization.")

        error_queries = [m for m in metrics if m.status == QueryStatus.ERROR]
        if len(error_queries) > len(metrics) * 0.05:
            recommendations.append("Elevated error rate detected. Review query logic and database constraints.")

        avg_execution_time = sum(m.execution_time_ms for m in metrics) / len(metrics)
        if avg_execution_time > 1000:
            recommendations.append("Average query execution time is high. Consider adding indexes or optimizing queries.")

        if slow_queries:
            collections_without_indexes = set()
            for metric in slow_queries:
                if metric.collection_table and (not metric.indexes_used or len(metric.indexes_used) == 0):
                    collections_without_indexes.add(metric.collection_table)
            
            if collections_without_indexes:
                recommendations.append(f"Consider adding indexes for: {', '.join(collections_without_indexes)}")

        return recommendations


class TimeWindowCalculator:
    @staticmethod
    def get_time_windows(period_minutes: int) -> Dict[str, datetime]:
        now = datetime.utcnow()
        period_start = now - timedelta(minutes=period_minutes)
        
        return {
            'now': now,
            'period_start': period_start,
            'period_end': now
        }

    @staticmethod
    def filter_metrics_by_time(metrics: List[QueryMetric], start_time: datetime, end_time: datetime) -> List[QueryMetric]:
        return [m for m in metrics if start_time <= m.timestamp <= end_time]


class MetricsFormatter:
    @staticmethod
    def format_for_prometheus(metrics: List[QueryMetric], database: str) -> str:
        if not metrics:
            return ""

        prometheus_lines = []
        
        query_count = len(metrics)
        prometheus_lines.append(f"# HELP db_query_total Total number of queries executed")
        prometheus_lines.append(f"# TYPE db_query_total counter")
        prometheus_lines.append(f'db_query_total{{database="{database}"}} {query_count}')

        execution_times = [m.execution_time_ms for m in metrics]
        avg_time = sum(execution_times) / len(execution_times)
        prometheus_lines.append(f"# HELP db_query_duration_ms Average query execution duration")
        prometheus_lines.append(f"# TYPE db_query_duration_ms gauge")
        prometheus_lines.append(f'db_query_duration_ms{{database="{database}"}} {avg_time}')

        performance_counts = {}
        for level in QueryPerformanceLevel:
            count = len([m for m in metrics if m.performance_level == level])
            performance_counts[level.value] = count
            prometheus_lines.append(f'db_queries_by_performance{{database="{database}",level="{level.value}"}} {count}')

        slow_count = len([m for m in metrics if m.performance_level in [QueryPerformanceLevel.SLOW, QueryPerformanceLevel.CRITICAL]])
        prometheus_lines.append(f"# HELP db_slow_queries_total Number of slow queries")
        prometheus_lines.append(f"# TYPE db_slow_queries_total counter")
        prometheus_lines.append(f'db_slow_queries_total{{database="{database}"}} {slow_count}')

        error_count = len([m for m in metrics if m.status == QueryStatus.ERROR])
        prometheus_lines.append(f"# HELP db_error_queries_total Number of failed queries")
        prometheus_lines.append(f"# TYPE db_error_queries_total counter")
        prometheus_lines.append(f'db_error_queries_total{{database="{database}"}} {error_count}')

        return "\n".join(prometheus_lines)

    @staticmethod
    def format_for_json_export(metrics: List[QueryMetric], database: str) -> Dict[str, Any]:
        return {
            'database': database,
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': [metric.dict() for metric in metrics],
            'summary': QueryMetricsAggregator.aggregate_metrics(metrics)
        }


class QueryPlanAnalyzer:
    @staticmethod
    def extract_indexes_from_plan(plan_details: Dict[str, Any]) -> List[str]:
        indexes = []
        
        if not plan_details:
            return indexes

        def extract_from_node(node):
            if isinstance(node, dict):
                if 'indexName' in node:
                    indexes.append(node['indexName'])
                if 'index' in node:
                    if isinstance(node['index'], str):
                        indexes.append(node['index'])
                    elif isinstance(node['index'], list):
                        indexes.extend(node['index'])
                
                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        extract_from_node(value)
            elif isinstance(node, list):
                for item in node:
                    extract_from_node(item)

        extract_from_node(plan_details)
        return list(set(indexes))

    @staticmethod
    def analyze_plan_efficiency(plan_details: Dict[str, Any]) -> Dict[str, Any]:
        if not plan_details:
            return {'efficiency_score': 0, 'issues': ['No plan available']}

        issues = []
        efficiency_score = 100

        if 'collectionScan' in str(plan_details):
            issues.append('Collection scan detected - consider adding indexes')
            efficiency_score -= 30

        if 'nestedLoops' in str(plan_details) and str(plan_details).count('nestedLoops') > 3:
            issues.append('Multiple nested loops detected - may indicate inefficient joins')
            efficiency_score -= 20

        return {
            'efficiency_score': max(0, efficiency_score),
            'issues': issues,
            'indexes_used': QueryPlanAnalyzer.extract_indexes_from_plan(plan_details)
        }

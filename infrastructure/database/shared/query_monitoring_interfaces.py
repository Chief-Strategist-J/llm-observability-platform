from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class QueryStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class QueryPerformanceLevel(str, Enum):
    FAST = "fast"
    NORMAL = "normal"
    SLOW = "slow"
    CRITICAL = "critical"


class QueryMetric(BaseModel):
    query_hash: str
    query_type: str
    database: str
    collection_table: Optional[str] = None
    execution_time_ms: float
    status: QueryStatus
    performance_level: QueryPerformanceLevel
    timestamp: datetime
    affected_rows: Optional[int] = None
    error_message: Optional[str] = None
    plan_details: Optional[Dict[str, Any]] = None
    indexes_used: Optional[List[str]] = None
    memory_usage_mb: Optional[float] = None


class QueryAnalysisResult(BaseModel):
    query_hash: str
    query_text: str
    performance_score: float = Field(ge=0, le=100)
    recommendations: List[str]
    suggested_indexes: List[Dict[str, Any]]
    optimization_potential: str
    estimated_improvement_percent: Optional[float] = None


class PerformanceReport(BaseModel):
    database: str
    period_start: datetime
    period_end: datetime
    total_queries: int
    slow_queries: int
    avg_execution_time_ms: float
    performance_distribution: Dict[QueryPerformanceLevel, int]
    top_slow_queries: List[QueryMetric]
    recommendations: List[str]


class IQueryPerformanceCollector(ABC):
    @abstractmethod
    def collect_query_metrics(self, limit: int = 1000) -> List[QueryMetric]:
        pass

    @abstractmethod
    def get_slow_queries(self, threshold_ms: float = 1000.0, limit: int = 50) -> List[QueryMetric]:
        pass

    @abstractmethod
    def get_query_by_hash(self, query_hash: str) -> Optional[QueryMetric]:
        pass

    @abstractmethod
    def record_query_execution(self, query_metric: QueryMetric) -> None:
        pass


class IQueryAnalyzer(ABC):
    @abstractmethod
    def analyze_query(self, query_text: str, database: str) -> QueryAnalysisResult:
        pass

    @abstractmethod
    def explain_query(self, query_text: str, database: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def suggest_indexes(self, query_text: str, database: string) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def generate_performance_report(self, database: str, period_start: datetime, period_end: datetime) -> PerformanceReport:
        pass


class IMetricsExporter(ABC):
    @abstractmethod
    def export_query_metrics(self, metrics: List[QueryMetric]) -> str:
        pass

    @abstractmethod
    def export_database_metrics(self, database: str, metrics: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def get_prometheus_metrics(self) -> str:
        pass


class IQueryMonitoringClient(ABC):
    @abstractmethod
    def execute_with_monitoring(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_performance_summary(self, period_minutes: int = 60) -> Dict[str, Any]:
        pass

    @abstractmethod
    def identify_performance_issues(self) -> List[Dict[str, Any]]:
        pass


class QueryMonitoringConfig(BaseModel):
    slow_query_threshold_ms: float = 1000.0
    critical_query_threshold_ms: float = 5000.0
    enable_query_plans: bool = True
    enable_memory_tracking: bool = True
    max_query_history_size: int = 10000
    metrics_retention_hours: int = 168  # 7 days


class DatabaseConnectionConfig(BaseModel):
    host: str
    port: int
    database_name: str
    username: Optional[str] = None
    password: Optional[str] = None
    connection_timeout_seconds: int = 30
    max_connections: int = 10

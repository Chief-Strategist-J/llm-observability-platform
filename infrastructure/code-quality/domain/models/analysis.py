from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class AnalysisStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueType(Enum):
    BUG = "bug"
    VULNERABILITY = "vulnerability"
    CODE_SMELL = "code_smell"
    SECURITY_HOTSPOT = "security_hotspot"


class Severity(Enum):
    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Issue:
    key: str
    type: IssueType
    severity: Severity
    message: str
    file_path: str
    line_number: int
    rule: str
    status: str

    def is_blocking(self) -> bool:
        return self.severity in [Severity.BLOCKER, Severity.CRITICAL]

    def is_security_related(self) -> bool:
        return self.type in [IssueType.VULNERABILITY, IssueType.SECURITY_HOTSPOT]


@dataclass
class Metric:
    name: str
    value: float
    formatted_value: str

    def is_percentage(self) -> bool:
        return self.formatted_value.endswith('%')

    def is_time_based(self) -> bool:
        return 'ms' in self.formatted_value or 's' in self.formatted_value


@dataclass
class Analysis:
    id: str
    project_key: str
    branch: str
    commit_hash: str
    status: AnalysisStatus
    created_at: datetime
    completed_at: Optional[datetime]
    issues: List[Issue]
    metrics: List[Metric]

    def is_complete(self) -> bool:
        return self.status == AnalysisStatus.COMPLETED

    def has_blocking_issues(self) -> bool:
        return any(issue.is_blocking() for issue in self.issues)

    def get_critical_issues_count(self) -> int:
        return len([issue for issue in self.issues if issue.severity == Severity.CRITICAL])

    def get_coverage_metric(self) -> Optional[float]:
        for metric in self.metrics:
            if metric.name == 'coverage':
                return metric.value
        return None

    def get_issues_by_severity(self, severity: Severity) -> List[Issue]:
        return [issue for issue in self.issues if issue.severity == severity]

    def get_issues_by_type(self, issue_type: IssueType) -> List[Issue]:
        return [issue for issue in self.issues if issue.type == issue_type]

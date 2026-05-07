from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class ProjectStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class QualityGateStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    NONE = "none"


@dataclass
class Project:
    key: str
    name: str
    description: str
    status: ProjectStatus
    created_at: datetime
    last_analysis_at: Optional[datetime]
    quality_gate_status: QualityGateStatus
    languages: List[str]

    def is_active(self) -> bool:
        return self.status == ProjectStatus.ACTIVE

    def has_recent_analysis(self, days: int = 7) -> bool:
        if not self.last_analysis_at:
            return False
        from datetime import timezone
        now = datetime.now(timezone.utc)
        if self.last_analysis_at.tzinfo is None:
            self.last_analysis_at = self.last_analysis_at.replace(tzinfo=timezone.utc)
        return (now - self.last_analysis_at).days <= days

    def supports_language(self, language: str) -> bool:
        return language.lower() in [lang.lower() for lang in self.languages]

    def is_quality_gate_passed(self) -> bool:
        return self.quality_gate_status == QualityGateStatus.PASSED


@dataclass
class QualityGate:
    id: str
    name: str
    project_key: str
    status: QualityGateStatus
    conditions: List[str]

    def is_passed(self) -> bool:
        return self.status == QualityGateStatus.PASSED

    def has_failed(self) -> bool:
        return self.status == QualityGateStatus.FAILED

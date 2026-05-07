from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from domain.models.analysis import Analysis, AnalysisStatus
from domain.models.project import Project


class SonarQubeService(ABC):
    
    @abstractmethod
    def create_project(self, project_key: str, name: str, description: str = "") -> bool:
        pass

    @abstractmethod
    def delete_project(self, project_key: str) -> bool:
        pass

    @abstractmethod
    def trigger_analysis(self, project_key: str, branch: str, commit_hash: str) -> str:
        pass

    @abstractmethod
    def get_analysis_status(self, analysis_id: str) -> AnalysisStatus:
        pass

    @abstractmethod
    def get_analysis_results(self, analysis_id: str) -> Optional[Analysis]:
        pass

    @abstractmethod
    def get_project_analyses(self, project_key: str) -> List[Analysis]:
        pass

    @abstractmethod
    def get_project_quality_gate(self, project_key: str) -> Optional[str]:
        pass

    @abstractmethod
    def set_quality_gate(self, project_key: str, gate_name: str) -> bool:
        pass

    @abstractmethod
    def get_project_metrics(self, project_key: str, metrics: List[str]) -> Dict[str, float]:
        pass

    @abstractmethod
    def get_project_issues(self, project_key: str, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        pass

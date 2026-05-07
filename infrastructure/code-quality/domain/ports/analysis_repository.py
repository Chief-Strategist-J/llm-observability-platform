from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from domain.models.analysis import Analysis, AnalysisStatus


class AnalysisRepository(ABC):
    
    @abstractmethod
    def save(self, analysis: Analysis) -> None:
        pass

    @abstractmethod
    def find_by_id(self, analysis_id: str) -> Optional[Analysis]:
        pass

    @abstractmethod
    def find_by_project(self, project_key: str) -> List[Analysis]:
        pass

    @abstractmethod
    def find_by_branch(self, project_key: str, branch: str) -> List[Analysis]:
        pass

    @abstractmethod
    def find_by_commit(self, project_key: str, commit_hash: str) -> Optional[Analysis]:
        pass

    @abstractmethod
    def find_by_status(self, status: AnalysisStatus) -> List[Analysis]:
        pass

    @abstractmethod
    def find_latest_by_project(self, project_key: str) -> Optional[Analysis]:
        pass

    @abstractmethod
    def update_status(self, analysis_id: str, status: AnalysisStatus) -> None:
        pass

    @abstractmethod
    def delete(self, analysis_id: str) -> None:
        pass

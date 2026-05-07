from abc import ABC, abstractmethod
from typing import List, Optional

from domain.models.project import Project, ProjectStatus, QualityGate


class ProjectRepository(ABC):
    
    @abstractmethod
    def save(self, project: Project) -> None:
        pass

    @abstractmethod
    def find_by_key(self, project_key: str) -> Optional[Project]:
        pass

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Project]:
        pass

    @abstractmethod
    def find_by_status(self, status: ProjectStatus) -> List[Project]:
        pass

    @abstractmethod
    def find_all(self) -> List[Project]:
        pass

    @abstractmethod
    def find_by_language(self, language: str) -> List[Project]:
        pass

    @abstractmethod
    def update_status(self, project_key: str, status: ProjectStatus) -> None:
        pass

    @abstractmethod
    def delete(self, project_key: str) -> None:
        pass


class QualityGateRepository(ABC):
    
    @abstractmethod
    def save(self, quality_gate: QualityGate) -> None:
        pass

    @abstractmethod
    def find_by_id(self, gate_id: str) -> Optional[QualityGate]:
        pass

    @abstractmethod
    def find_by_project(self, project_key: str) -> List[QualityGate]:
        pass

    @abstractmethod
    def find_all(self) -> List[QualityGate]:
        pass

    @abstractmethod
    def delete(self, gate_id: str) -> None:
        pass

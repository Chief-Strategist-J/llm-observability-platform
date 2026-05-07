from typing import Optional
from datetime import datetime

from domain.models.analysis import Analysis, AnalysisStatus
from domain.models.project import Project
from domain.ports.analysis_repository import AnalysisRepository
from domain.ports.project_repository import ProjectRepository
from domain.ports.sonarqube_service import SonarQubeService
from domain.services.analysis_domain_service import AnalysisDomainService
from shared.validators.analysis_validator import AnalysisValidator
from shared.utils.date_utils import DateUtils
from shared.constants.analysis_constants import AnalysisConstants


class TriggerAnalysisUseCase:
    
    def __init__(
        self,
        analysis_repository: AnalysisRepository,
        project_repository: ProjectRepository,
        sonarqube_service: SonarQubeService,
        analysis_domain_service: AnalysisDomainService
    ):
        self.analysis_repository = analysis_repository
        self.project_repository = project_repository
        self.sonarqube_service = sonarqube_service
        self.analysis_domain_service = analysis_domain_service

    def execute(self, project_key: str, branch: str, commit_hash: str) -> str:
        validation_errors = self._validate_input(project_key, branch, commit_hash)
        if validation_errors:
            raise ValueError(f"Validation failed: {', '.join(validation_errors)}")

        project = self.project_repository.find_by_key(project_key)
        if not project:
            raise ValueError(f"Project with key '{project_key}' not found")

        existing_analysis = self.analysis_repository.find_by_commit(project_key, commit_hash)
        if existing_analysis:
            return existing_analysis.id

        analysis_id = self._generate_analysis_id(project_key, commit_hash)
        
        new_analysis = Analysis(
            id=analysis_id,
            project_key=project_key,
            branch=branch,
            commit_hash=commit_hash,
            status=AnalysisStatus.PENDING,
            created_at=DateUtils.utc_now(),
            completed_at=None,
            issues=[],
            metrics=[]
        )

        self.analysis_repository.save(new_analysis)

        try:
            sonar_task_id = self.sonarqube_service.trigger_analysis(project_key, branch, commit_hash)
            self.analysis_repository.update_status(analysis_id, AnalysisStatus.RUNNING)
            return analysis_id
        except Exception as e:
            self.analysis_repository.update_status(analysis_id, AnalysisStatus.FAILED)
            raise RuntimeError(f"Failed to trigger SonarQube analysis: {str(e)}")

    def _validate_input(self, project_key: str, branch: str, commit_hash: str) -> list:
        errors = []
        errors.extend(AnalysisValidator.validate_project_key(project_key))
        errors.extend(AnalysisValidator.validate_branch_name(branch))
        errors.extend(AnalysisValidator.validate_commit_hash(commit_hash))
        return errors

    def _generate_analysis_id(self, project_key: str, commit_hash: str) -> str:
        timestamp = DateUtils.utc_now().strftime('%Y%m%d_%H%M%S')
        return f"{project_key}_{commit_hash[:7]}_{timestamp}"

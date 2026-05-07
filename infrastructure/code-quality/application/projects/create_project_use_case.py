from typing import List

from domain.models.project import Project, ProjectStatus, QualityGateStatus
from domain.ports.project_repository import ProjectRepository
from domain.ports.sonarqube_service import SonarQubeService
from shared.utils.date_utils import DateUtils
from shared.constants.analysis_constants import AnalysisConstants


class CreateProjectUseCase:
    
    def __init__(
        self,
        project_repository: ProjectRepository,
        sonarqube_service: SonarQubeService
    ):
        self.project_repository = project_repository
        self.sonarqube_service = sonarqube_service

    def execute(self, project_key: str, name: str, description: str, languages: List[str]) -> Project:
        validation_errors = self._validate_project_data(project_key, name, languages)
        if validation_errors:
            raise ValueError(f"Validation failed: {', '.join(validation_errors)}")

        existing_project = self.project_repository.find_by_key(project_key)
        if existing_project:
            raise ValueError(f"Project with key '{project_key}' already exists")

        existing_project_by_name = self.project_repository.find_by_name(name)
        if existing_project_by_name:
            raise ValueError(f"Project with name '{name}' already exists")

        validated_languages = self._validate_languages(languages)

        try:
            sonarqube_created = self.sonarqube_service.create_project(project_key, name, description)
            if not sonarqube_created:
                raise RuntimeError(f"Failed to create project in SonarQube")
        except Exception as e:
            raise RuntimeError(f"Failed to create project in SonarQube: {str(e)}")

        project = Project(
            key=project_key,
            name=name,
            description=description,
            status=ProjectStatus.ACTIVE,
            created_at=DateUtils.utc_now(),
            last_analysis_at=None,
            quality_gate_status=QualityGateStatus.NONE,
            languages=validated_languages
        )

        self.project_repository.save(project)
        return project

    def _validate_project_data(self, project_key: str, name: str, languages: List[str]) -> List[str]:
        errors = []

        if not project_key or len(project_key.strip()) < 2:
            errors.append("Project key must be at least 2 characters long")
        elif not project_key.replace('-', '').replace('_', '').isalnum():
            errors.append("Project key can only contain alphanumeric characters, hyphens, and underscores")

        if not name or len(name.strip()) < 2:
            errors.append("Project name must be at least 2 characters long")
        elif len(name) > 255:
            errors.append("Project name cannot exceed 255 characters")

        if not languages:
            errors.append("At least one programming language must be specified")

        return errors

    def _validate_languages(self, languages: List[str]) -> List[str]:
        validated_languages = []
        supported_languages = [lang.lower() for lang in AnalysisConstants.SUPPORTED_LANGUAGES]

        for language in languages:
            normalized_lang = language.lower().strip()
            if normalized_lang in supported_languages:
                validated_languages.append(normalized_lang)
            else:
                raise ValueError(f"Unsupported language: '{language}'. Supported languages: {', '.join(AnalysisConstants.SUPPORTED_LANGUAGES)}")

        return list(set(validated_languages))

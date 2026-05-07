from typing import Optional
from datetime import datetime

from domain.models.analysis import Analysis, AnalysisStatus
from domain.ports.analysis_repository import AnalysisRepository
from domain.ports.sonarqube_service import SonarQubeService
from domain.services.analysis_domain_service import AnalysisDomainService
from shared.utils.date_utils import DateUtils
from shared.constants.analysis_constants import AnalysisConstants


class CheckAnalysisStatusUseCase:
    
    def __init__(
        self,
        analysis_repository: AnalysisRepository,
        sonarqube_service: SonarQubeService,
        analysis_domain_service: AnalysisDomainService
    ):
        self.analysis_repository = analysis_repository
        self.sonarqube_service = sonarqube_service
        self.analysis_domain_service = analysis_domain_service

    def execute(self, analysis_id: str) -> Analysis:
        analysis = self.analysis_repository.find_by_id(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis with ID '{analysis_id}' not found")

        if analysis.status == AnalysisStatus.COMPLETED:
            return analysis

        current_status = self.sonarqube_service.get_analysis_status(analysis_id)
        
        if current_status != analysis.status:
            self.analysis_repository.update_status(analysis_id, current_status)
            analysis.status = current_status

        if current_status == AnalysisStatus.COMPLETED:
            self._process_completed_analysis(analysis_id)

        return self.analysis_repository.find_by_id(analysis_id)

    def _process_completed_analysis(self, analysis_id: str) -> None:
        try:
            sonar_analysis = self.sonarqube_service.get_analysis_results(analysis_id)
            if sonar_analysis:
                self.analysis_repository.save(sonar_analysis)
        except Exception as e:
            self.analysis_repository.update_status(analysis_id, AnalysisStatus.FAILED)
            raise RuntimeError(f"Failed to process completed analysis: {str(e)}")

    def is_analysis_ready_for_merge(self, analysis_id: str) -> bool:
        analysis = self.execute(analysis_id)
        return not self.analysis_domain_service.should_block_merge(analysis)

    def get_analysis_summary(self, analysis_id: str) -> str:
        analysis = self.execute(analysis_id)
        return self.analysis_domain_service.generate_analysis_summary(analysis)

    def get_quality_score(self, analysis_id: str) -> float:
        analysis = self.execute(analysis_id)
        return self.analysis_domain_service.calculate_quality_score(analysis)

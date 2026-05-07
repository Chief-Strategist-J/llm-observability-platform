from typing import Dict, List, Optional
from datetime import datetime, timedelta

from domain.models.analysis import Analysis, AnalysisStatus
from domain.models.project import Project
from domain.ports.analysis_repository import AnalysisRepository
from domain.ports.project_repository import ProjectRepository
from domain.services.analysis_domain_service import AnalysisDomainService
from shared.utils.date_utils import DateUtils


class GenerateQualityReportUseCase:
    
    def __init__(
        self,
        analysis_repository: AnalysisRepository,
        project_repository: ProjectRepository,
        analysis_domain_service: AnalysisDomainService
    ):
        self.analysis_repository = analysis_repository
        self.project_repository = project_repository
        self.analysis_domain_service = analysis_domain_service

    def execute(self, project_key: str, days: int = 30) -> Dict:
        project = self.project_repository.find_by_key(project_key)
        if not project:
            raise ValueError(f"Project with key '{project_key}' not found")

        end_date = DateUtils.utc_now()
        start_date = end_date - timedelta(days=days)

        analyses = self._get_analyses_in_period(project_key, start_date, end_date)
        
        report = {
            'project': {
                'key': project.key,
                'name': project.name,
                'description': project.description,
                'languages': project.languages,
                'status': project.status.value
            },
            'period': {
                'start': DateUtils.format_iso(start_date),
                'end': DateUtils.format_iso(end_date),
                'days': days
            },
            'summary': self._generate_summary(analyses),
            'trends': self._generate_trends(analyses),
            'quality_metrics': self._generate_quality_metrics(analyses),
            'security_analysis': self._generate_security_analysis(analyses),
            'recommendations': self._generate_recommendations(analyses)
        }

        return report

    def _get_analyses_in_period(self, project_key: str, start_date: datetime, end_date: datetime) -> List[Analysis]:
        all_analyses = self.analysis_repository.find_by_project(project_key)
        return [
            analysis for analysis in all_analyses
            if start_date <= analysis.created_at <= end_date
        ]

    def _generate_summary(self, analyses: List[Analysis]) -> Dict:
        if not analyses:
            return {
                'total_analyses': 0,
                'successful_analyses': 0,
                'failed_analyses': 0,
                'average_quality_score': 0.0,
                'last_analysis_date': None
            }

        successful_analyses = [a for a in analyses if a.status == AnalysisStatus.COMPLETED]
        failed_analyses = [a for a in analyses if a.status == AnalysisStatus.FAILED]

        quality_scores = [
            self.analysis_domain_service.calculate_quality_score(a) 
            for a in successful_analyses
        ]
        average_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        return {
            'total_analyses': len(analyses),
            'successful_analyses': len(successful_analyses),
            'failed_analyses': len(failed_analyses),
            'average_quality_score': round(average_quality_score, 2),
            'last_analysis_date': DateUtils.format_iso(max(a.created_at for a in analyses))
        }

    def _generate_trends(self, analyses: List[Analysis]) -> Dict:
        successful_analyses = sorted(
            [a for a in analyses if a.status == AnalysisStatus.COMPLETED],
            key=lambda x: x.created_at
        )

        if len(successful_analyses) < 2:
            return {'trend': 'insufficient_data'}

        first_analysis = successful_analyses[0]
        last_analysis = successful_analyses[-1]

        first_score = self.analysis_domain_service.calculate_quality_score(first_analysis)
        last_score = self.analysis_domain_service.calculate_quality_score(last_analysis)

        score_change = last_score - first_score
        
        if score_change > 5:
            trend = 'improving'
        elif score_change < -5:
            trend = 'declining'
        else:
            trend = 'stable'

        return {
            'trend': trend,
            'score_change': round(score_change, 2),
            'first_score': round(first_score, 2),
            'last_score': round(last_score, 2)
        }

    def _generate_quality_metrics(self, analyses: List[Analysis]) -> Dict:
        successful_analyses = [a for a in analyses if a.status == AnalysisStatus.COMPLETED]
        
        if not successful_analyses:
            return {}

        total_issues = sum(len(a.issues) for a in successful_analyses)
        critical_issues = sum(a.get_critical_issues_count() for a in successful_analyses)
        
        security_issues = []
        reliability_issues = []
        maintainability_issues = []
        
        for analysis in successful_analyses:
            security_issues.extend(self.analysis_domain_service.get_security_issues(analysis))
            reliability_issues.extend(self.analysis_domain_service.get_reliability_issues(analysis))
            maintainability_issues.extend(self.analysis_domain_service.get_maintainability_issues(analysis))

        coverage_values = []
        for analysis in successful_analyses:
            coverage = analysis.get_coverage_metric()
            if coverage is not None:
                coverage_values.append(coverage)

        return {
            'total_issues': total_issues,
            'critical_issues': critical_issues,
            'security_issues': len(security_issues),
            'reliability_issues': len(reliability_issues),
            'maintainability_issues': len(maintainability_issues),
            'average_coverage': round(sum(coverage_values) / len(coverage_values), 2) if coverage_values else 0.0
        }

    def _generate_security_analysis(self, analyses: List[Analysis]) -> Dict:
        successful_analyses = [a for a in analyses if a.status == AnalysisStatus.COMPLETED]
        
        vulnerabilities = []
        security_hotspots = []
        
        for analysis in successful_analyses:
            security_issues = self.analysis_domain_service.get_security_issues(analysis)
            for issue in security_issues:
                if issue.type.value == 'vulnerability':
                    vulnerabilities.append(issue)
                elif issue.type.value == 'security_hotspot':
                    security_hotspots.append(issue)

        return {
            'vulnerabilities': len(vulnerabilities),
            'security_hotspots': len(security_hotspots),
            'high_risk_vulnerabilities': len([v for v in vulnerabilities if v.severity.value in ['blocker', 'critical']]),
            'requires_immediate_attention': len([v for v in vulnerabilities if v.severity.value in ['blocker', 'critical']]) > 0
        }

    def _generate_recommendations(self, analyses: List[Analysis]) -> List[str]:
        recommendations = []
        
        if not analyses:
            return ['No analysis data available. Configure and run code analysis to receive recommendations.']

        successful_analyses = [a for a in analyses if a.status == AnalysisStatus.COMPLETED]
        
        if not successful_analyses:
            return ['All recent analyses have failed. Check SonarQube configuration and connectivity.']

        latest_analysis = successful_analyses[-1]
        
        if self.analysis_domain_service.requires_immediate_attention(latest_analysis):
            recommendations.append('URGENT: Address critical security vulnerabilities and blocking issues immediately.')

        coverage = latest_analysis.get_coverage_metric()
        if coverage is not None and coverage < 80.0:
            recommendations.append(f'Increase test coverage from {coverage:.1f}% to at least 80% to meet quality standards.')

        critical_count = latest_analysis.get_critical_issues_count()
        if critical_count > 0:
            recommendations.append(f'Resolve {critical_count} critical issues to improve code reliability.')

        security_issues = self.analysis_domain_service.get_security_issues(latest_analysis)
        if len(security_issues) > 0:
            recommendations.append(f'Address {len(security_issues)} security issues to improve code security.')

        quality_score = self.analysis_domain_service.calculate_quality_score(latest_analysis)
        if quality_score < 85.0:
            recommendations.append(f'Focus on improving code quality. Current score: {quality_score:.1f}/100.')

        if len(recommendations) == 0:
            recommendations.append('Excellent code quality! Continue maintaining current standards.')

        return recommendations

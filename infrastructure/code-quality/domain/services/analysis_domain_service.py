from typing import List, Optional
from datetime import datetime

from domain.models.analysis import Analysis, Issue, Severity, IssueType
from domain.models.project import Project, QualityGateStatus


class AnalysisDomainService:
    
    def should_block_merge(self, analysis: Analysis) -> bool:
        if not analysis.is_complete():
            return True
        
        if analysis.has_blocking_issues():
            return True
            
        coverage = analysis.get_coverage_metric()
        if coverage is not None and coverage < 80.0:
            return True
            
        return False

    def calculate_quality_score(self, analysis: Analysis) -> float:
        if not analysis.is_complete():
            return 0.0
        
        total_issues = len(analysis.issues)
        if total_issues == 0:
            return 100.0
        
        blocker_weight = 10.0
        critical_weight = 5.0
        major_weight = 2.0
        minor_weight = 0.5
        info_weight = 0.1
        
        score_deduction = 0.0
        for issue in analysis.issues:
            if issue.severity == Severity.BLOCKER:
                score_deduction += blocker_weight
            elif issue.severity == Severity.CRITICAL:
                score_deduction += critical_weight
            elif issue.severity == Severity.MAJOR:
                score_deduction += major_weight
            elif issue.severity == Severity.MINOR:
                score_deduction += minor_weight
            else:
                score_deduction += info_weight
        
        base_score = 100.0
        final_score = max(0.0, base_score - score_deduction)
        
        coverage = analysis.get_coverage_metric()
        if coverage is not None:
            coverage_bonus = (coverage / 100.0) * 5.0
            final_score = min(100.0, final_score + coverage_bonus)
        
        return round(final_score, 2)

    def get_security_issues(self, analysis: Analysis) -> List[Issue]:
        return [issue for issue in analysis.issues if issue.is_security_related()]

    def get_maintainability_issues(self, analysis: Analysis) -> List[Issue]:
        return [issue for issue in analysis.issues if issue.type == IssueType.CODE_SMELL]

    def get_reliability_issues(self, analysis: Analysis) -> List[Issue]:
        return [issue for issue in analysis.issues if issue.type == IssueType.BUG]

    def requires_immediate_attention(self, analysis: Analysis) -> bool:
        return (
            analysis.get_critical_issues_count() > 0 or
            len(self.get_security_issues(analysis)) > 0 or
            analysis.has_blocking_issues()
        )

    def generate_analysis_summary(self, analysis: Analysis) -> str:
        if not analysis.is_complete():
            return f"Analysis {analysis.id} is still in progress"
        
        summary_parts = []
        
        total_issues = len(analysis.issues)
        summary_parts.append(f"Found {total_issues} issues")
        
        critical_count = analysis.get_critical_issues_count()
        if critical_count > 0:
            summary_parts.append(f"{critical_count} critical")
        
        security_count = len(self.get_security_issues(analysis))
        if security_count > 0:
            summary_parts.append(f"{security_count} security")
        
        coverage = analysis.get_coverage_metric()
        if coverage is not None:
            summary_parts.append(f"{coverage:.1f}% coverage")
        
        quality_score = self.calculate_quality_score(analysis)
        summary_parts.append(f"Quality Score: {quality_score}")
        
        return ", ".join(summary_parts)

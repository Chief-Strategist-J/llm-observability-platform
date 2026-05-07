from typing import List, Optional
from datetime import datetime

from domain.models.analysis import Analysis, Issue, Metric, AnalysisStatus, Severity, IssueType
from shared.constants.analysis_constants import AnalysisConstants


class AnalysisValidator:
    
    @staticmethod
    def validate_analysis_id(analysis_id: str) -> List[str]:
        errors = []
        
        if not analysis_id:
            errors.append("Analysis ID cannot be empty")
        elif len(analysis_id) < 3:
            errors.append("Analysis ID must be at least 3 characters long")
        elif not analysis_id.replace('-', '').replace('_', '').isalnum():
            errors.append("Analysis ID can only contain alphanumeric characters, hyphens, and underscores")
        
        return errors

    @staticmethod
    def validate_project_key(project_key: str) -> List[str]:
        errors = []
        
        if not project_key:
            errors.append("Project key cannot be empty")
        elif len(project_key) < 2:
            errors.append("Project key must be at least 2 characters long")
        elif not project_key.replace('-', '').replace('_', '').isalnum():
            errors.append("Project key can only contain alphanumeric characters, hyphens, and underscores")
        
        return errors

    @staticmethod
    def validate_commit_hash(commit_hash: str) -> List[str]:
        errors = []
        
        if not commit_hash:
            errors.append("Commit hash cannot be empty")
        elif len(commit_hash) != 40 and len(commit_hash) != 7:
            errors.append("Commit hash must be either 40 characters (full) or 7 characters (short)")
        elif not commit_hash.isalnum():
            errors.append("Commit hash must contain only alphanumeric characters")
        
        return errors

    @staticmethod
    def validate_branch_name(branch: str) -> List[str]:
        errors = []
        
        if not branch:
            errors.append("Branch name cannot be empty")
        elif len(branch) > 255:
            errors.append("Branch name cannot exceed 255 characters")
        elif branch.startswith('-') or branch.endswith('-'):
            errors.append("Branch name cannot start or end with hyphen")
        
        return errors

    @staticmethod
    def validate_issue(issue: Issue) -> List[str]:
        errors = []
        
        if not issue.key:
            errors.append("Issue key cannot be empty")
        
        if not issue.message:
            errors.append("Issue message cannot be empty")
        elif len(issue.message) > 1000:
            errors.append("Issue message cannot exceed 1000 characters")
        
        if not issue.file_path:
            errors.append("File path cannot be empty")
        
        if issue.line_number <= 0:
            errors.append("Line number must be positive")
        
        if not issue.rule:
            errors.append("Rule cannot be empty")
        
        return errors

    @staticmethod
    def validate_metric(metric: Metric) -> List[str]:
        errors = []
        
        if not metric.name:
            errors.append("Metric name cannot be empty")
        
        if metric.value < 0:
            errors.append("Metric value cannot be negative")
        
        if not metric.formatted_value:
            errors.append("Formatted value cannot be empty")
        
        return errors

    @staticmethod
    def validate_analysis(analysis: Analysis) -> List[str]:
        errors = []
        
        errors.extend(AnalysisValidator.validate_analysis_id(analysis.id))
        errors.extend(AnalysisValidator.validate_project_key(analysis.project_key))
        errors.extend(AnalysisValidator.validate_commit_hash(analysis.commit_hash))
        errors.extend(AnalysisValidator.validate_branch_name(analysis.branch))
        
        if not analysis.created_at:
            errors.append("Created at timestamp cannot be empty")
        elif analysis.created_at > datetime.now():
            errors.append("Created at timestamp cannot be in the future")
        
        if analysis.completed_at and analysis.completed_at < analysis.created_at:
            errors.append("Completed at timestamp cannot be before created at")
        
        for i, issue in enumerate(analysis.issues):
            issue_errors = AnalysisValidator.validate_issue(issue)
            errors.extend([f"Issue {i}: {error}" for error in issue_errors])
        
        for i, metric in enumerate(analysis.metrics):
            metric_errors = AnalysisValidator.validate_metric(metric)
            errors.extend([f"Metric {i}: {error}" for error in metric_errors])
        
        return errors

    @staticmethod
    def is_analysis_complete_for_quality_gate(analysis: Analysis) -> bool:
        return (
            analysis.status == AnalysisStatus.COMPLETED and
            analysis.metrics and
            analysis.issues is not None
        )

    @staticmethod
    def has_required_metrics(analysis: Analysis, required_metrics: List[str]) -> bool:
        metric_names = [metric.name for metric in analysis.metrics]
        return all(metric in metric_names for metric in required_metrics)

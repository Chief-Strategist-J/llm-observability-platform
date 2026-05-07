from flask import Flask, request, jsonify
from typing import Dict, Any

from application.analysis.trigger_analysis_use_case import TriggerAnalysisUseCase
from application.analysis.check_analysis_status_use_case import CheckAnalysisStatusUseCase
from shared.validators.analysis_validator import AnalysisValidator


class AnalysisController:
    
    def __init__(
        self,
        trigger_analysis_use_case: TriggerAnalysisUseCase,
        check_analysis_status_use_case: CheckAnalysisStatusUseCase
    ):
        self.trigger_analysis_use_case = trigger_analysis_use_case
        self.check_analysis_status_use_case = check_analysis_status_use_case

    def trigger_analysis(self) -> Dict[str, Any]:
        try:
            data = request.get_json()
            if not data:
                return {'error': 'Request body is required'}, 400

            project_key = data.get('project_key')
            branch = data.get('branch')
            commit_hash = data.get('commit_hash')

            validation_errors = self._validate_trigger_request(data)
            if validation_errors:
                return {'error': 'Validation failed', 'details': validation_errors}, 400

            analysis_id = self.trigger_analysis_use_case.execute(project_key, branch, commit_hash)
            
            return {
                'message': 'Analysis triggered successfully',
                'analysis_id': analysis_id,
                'project_key': project_key,
                'branch': branch,
                'commit_hash': commit_hash
            }, 202

        except ValueError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            return {'error': 'Internal server error'}, 500

    def check_analysis_status(self, analysis_id: str) -> Dict[str, Any]:
        try:
            if not analysis_id:
                return {'error': 'Analysis ID is required'}, 400

            analysis = self.check_analysis_status_use_case.execute(analysis_id)
            
            return {
                'analysis_id': analysis.id,
                'project_key': analysis.project_key,
                'branch': analysis.branch,
                'commit_hash': analysis.commit_hash,
                'status': analysis.status.value,
                'created_at': analysis.created_at.isoformat(),
                'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None,
                'summary': self.check_analysis_status_use_case.get_analysis_summary(analysis_id),
                'quality_score': self.check_analysis_status_use_case.get_quality_score(analysis_id),
                'ready_for_merge': self.check_analysis_status_use_case.is_analysis_ready_for_merge(analysis_id)
            }, 200

        except ValueError as e:
            return {'error': str(e)}, 404
        except Exception as e:
            return {'error': 'Internal server error'}, 500

    def get_analysis_metrics(self, analysis_id: str) -> Dict[str, Any]:
        try:
            analysis = self.check_analysis_status_use_case.execute(analysis_id)
            
            metrics = []
            for metric in analysis.metrics:
                metrics.append({
                    'name': metric.name,
                    'value': metric.value,
                    'formatted_value': metric.formatted_value
                })

            return {
                'analysis_id': analysis_id,
                'metrics': metrics
            }, 200

        except ValueError as e:
            return {'error': str(e)}, 404
        except Exception as e:
            return {'error': 'Internal server error'}, 500

    def get_analysis_issues(self, analysis_id: str) -> Dict[str, Any]:
        try:
            analysis = self.check_analysis_status_use_case.execute(analysis_id)
            
            issues = []
            for issue in analysis.issues:
                issues.append({
                    'key': issue.key,
                    'type': issue.type.value,
                    'severity': issue.severity.value,
                    'message': issue.message,
                    'file_path': issue.file_path,
                    'line_number': issue.line_number,
                    'rule': issue.rule,
                    'status': issue.status,
                    'is_blocking': issue.is_blocking(),
                    'is_security_related': issue.is_security_related()
                })

            return {
                'analysis_id': analysis_id,
                'issues': issues,
                'total_issues': len(issues),
                'blocking_issues': len([i for i in issues if i['is_blocking']]),
                'security_issues': len([i for i in issues if i['is_security_related']])
            }, 200

        except ValueError as e:
            return {'error': str(e)}, 404
        except Exception as e:
            return {'error': 'Internal server error'}, 500

    def _validate_trigger_request(self, data: Dict[str, Any]) -> list:
        errors = []
        
        project_key = data.get('project_key', '')
        branch = data.get('branch', '')
        commit_hash = data.get('commit_hash', '')

        errors.extend(AnalysisValidator.validate_project_key(project_key))
        errors.extend(AnalysisValidator.validate_branch_name(branch))
        errors.extend(AnalysisValidator.validate_commit_hash(commit_hash))

        return errors

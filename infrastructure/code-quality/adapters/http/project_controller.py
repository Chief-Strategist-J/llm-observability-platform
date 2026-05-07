from flask import request, jsonify
from typing import Dict, Any, List

from application.projects.create_project_use_case import CreateProjectUseCase
from application.reporting.generate_quality_report_use_case import GenerateQualityReportUseCase


class ProjectController:
    
    def __init__(
        self,
        create_project_use_case: CreateProjectUseCase,
        generate_quality_report_use_case: GenerateQualityReportUseCase
    ):
        self.create_project_use_case = create_project_use_case
        self.generate_quality_report_use_case = generate_quality_report_use_case

    def create_project(self) -> Dict[str, Any]:
        try:
            data = request.get_json()
            if not data:
                return {'error': 'Request body is required'}, 400

            project_key = data.get('project_key')
            name = data.get('name')
            description = data.get('description', '')
            languages = data.get('languages', [])

            validation_errors = self._validate_create_request(data)
            if validation_errors:
                return {'error': 'Validation failed', 'details': validation_errors}, 400

            project = self.create_project_use_case.execute(project_key, name, description, languages)
            
            return {
                'message': 'Project created successfully',
                'project': {
                    'key': project.key,
                    'name': project.name,
                    'description': project.description,
                    'status': project.status.value,
                    'languages': project.languages,
                    'created_at': project.created_at.isoformat()
                }
            }, 201

        except ValueError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            return {'error': 'Internal server error'}, 500

    def get_quality_report(self, project_key: str) -> Dict[str, Any]:
        try:
            days = request.args.get('days', 30, type=int)
            
            if days < 1 or days > 365:
                return {'error': 'Days parameter must be between 1 and 365'}, 400

            report = self.generate_quality_report_use_case.execute(project_key, days)
            
            return {
                'report': report,
                'generated_at': report['period']['end']
            }, 200

        except ValueError as e:
            return {'error': str(e)}, 404
        except Exception as e:
            return {'error': 'Internal server error'}, 500

    def _validate_create_request(self, data: Dict[str, Any]) -> List[str]:
        errors = []
        
        if not data.get('project_key'):
            errors.append('project_key is required')
        
        if not data.get('name'):
            errors.append('name is required')
        
        if not data.get('languages'):
            errors.append('languages is required')
        elif not isinstance(data.get('languages'), list):
            errors.append('languages must be an array')
        elif len(data.get('languages')) == 0:
            errors.append('at least one language must be specified')

        return errors

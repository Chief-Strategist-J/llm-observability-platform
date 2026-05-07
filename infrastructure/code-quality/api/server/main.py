from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from typing import Dict, Any

from adapters.http.analysis_controller import AnalysisController
from adapters.http.project_controller import ProjectController
from adapters.cli.quality_cli import QualityCLI
from application.analysis.trigger_analysis_use_case import TriggerAnalysisUseCase
from application.analysis.check_analysis_status_use_case import CheckAnalysisStatusUseCase
from application.projects.create_project_use_case import CreateProjectUseCase
from application.reporting.generate_quality_report_use_case import GenerateQualityReportUseCase
from infrastructure.sonarqube.sonarqube_service_adapter import SonarQubeServiceAdapter
from infrastructure.persistence.postgresql_analysis_repository import PostgreSQLAnalysisRepository
from infrastructure.persistence.postgresql_project_repository import PostgreSQLProjectRepository
from domain.services.analysis_domain_service import AnalysisDomainService


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Initialize dependencies
    database_url = os.getenv('DATABASE_URL', 'postgresql://sonar:sonar@localhost:5432/sonar')
    sonarqube_url = os.getenv('SONARQUBE_URL', 'http://localhost:9000')
    sonarqube_token = os.getenv('SONARQUBE_TOKEN')
    
    if not sonarqube_token:
        logger.warning("SONARQUBE_TOKEN not set, using mock service")
    
    # Infrastructure layer
    sonarqube_service = SonarQubeServiceAdapter(sonarqube_url, sonarqube_token)
    analysis_repository = PostgreSQLAnalysisRepository(database_url)
    project_repository = PostgreSQLProjectRepository(database_url)
    
    # Domain layer
    analysis_domain_service = AnalysisDomainService()
    
    # Application layer
    trigger_analysis_use_case = TriggerAnalysisUseCase(
        analysis_repository, project_repository, sonarqube_service, analysis_domain_service
    )
    check_analysis_status_use_case = CheckAnalysisStatusUseCase(
        analysis_repository, sonarqube_service, analysis_domain_service
    )
    create_project_use_case = CreateProjectUseCase(project_repository, sonarqube_service)
    generate_quality_report_use_case = GenerateQualityReportUseCase(
        analysis_repository, project_repository, analysis_domain_service
    )
    
    # Controllers
    analysis_controller = AnalysisController(trigger_analysis_use_case, check_analysis_status_use_case)
    project_controller = ProjectController(create_project_use_case, generate_quality_report_use_case)
    
    # API Routes
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'quality-api',
            'version': '1.0.0'
        })
    
    @app.route('/ready', methods=['GET'])
    def readiness_check():
        try:
            # Test database connection
            analysis_repository.find_by_status('pending')
            return jsonify({
                'status': 'ready',
                'database': 'connected',
                'sonarqube': 'connected' if sonarqube_token else 'mock'
            })
        except Exception as e:
            return jsonify({
                'status': 'not_ready',
                'error': str(e)
            }), 503
    
    @app.route('/api/v1/analysis/trigger', methods=['POST'])
    def trigger_analysis():
        data, status_code = analysis_controller.trigger_analysis()
        return jsonify(data), status_code
    
    @app.route('/api/v1/analysis/<analysis_id>/status', methods=['GET'])
    def check_analysis_status(analysis_id):
        data, status_code = analysis_controller.check_analysis_status(analysis_id)
        return jsonify(data), status_code
    
    @app.route('/api/v1/analysis/<analysis_id>/metrics', methods=['GET'])
    def get_analysis_metrics(analysis_id):
        data, status_code = analysis_controller.get_analysis_metrics(analysis_id)
        return jsonify(data), status_code
    
    @app.route('/api/v1/analysis/<analysis_id>/issues', methods=['GET'])
    def get_analysis_issues(analysis_id):
        data, status_code = analysis_controller.get_analysis_issues(analysis_id)
        return jsonify(data), status_code
    
    @app.route('/api/v1/projects', methods=['POST'])
    def create_project():
        data, status_code = project_controller.create_project()
        return jsonify(data), status_code
    
    @app.route('/api/v1/projects/<project_key>/report', methods=['GET'])
    def get_quality_report(project_key):
        data, status_code = project_controller.get_quality_report(project_key)
        return jsonify(data), status_code
    
    @app.route('/api/v1/projects', methods=['GET'])
    def list_projects():
        try:
            projects = project_repository.find_all()
            return jsonify({
                'projects': [
                    {
                        'key': project.key,
                        'name': project.name,
                        'description': project.description,
                        'status': project.status.value,
                        'languages': project.languages,
                        'created_at': project.created_at.isoformat(),
                        'last_analysis_at': project.last_analysis_at.isoformat() if project.last_analysis_at else None,
                        'quality_gate_status': project.quality_gate_status.value
                    }
                    for project in projects
                ]
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v1/projects/<project_key>', methods=['GET'])
    def get_project(project_key):
        try:
            project = project_repository.find_by_key(project_key)
            if not project:
                return jsonify({'error': 'Project not found'}), 404
            
            return jsonify({
                'project': {
                    'key': project.key,
                    'name': project.name,
                    'description': project.description,
                    'status': project.status.value,
                    'languages': project.languages,
                    'created_at': project.created_at.isoformat(),
                    'last_analysis_at': project.last_analysis_at.isoformat() if project.last_analysis_at else None,
                    'quality_gate_status': project.quality_gate_status.value
                }
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

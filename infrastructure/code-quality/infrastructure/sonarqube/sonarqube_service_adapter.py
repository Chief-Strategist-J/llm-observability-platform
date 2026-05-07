import requests
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

from domain.models.analysis import Analysis, AnalysisStatus, Issue, Metric, IssueType, Severity
from domain.models.project import Project
from domain.ports.sonarqube_service import SonarQubeService
from shared.constants.analysis_constants import AnalysisConstants
from shared.utils.date_utils import DateUtils


class SonarQubeServiceAdapter(SonarQubeService):
    
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        url = urljoin(self.base_url, endpoint)
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def _post_request(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        url = urljoin(self.base_url, endpoint)
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def create_project(self, project_key: str, name: str, description: str = "") -> bool:
        try:
            data = {
                'project': project_key,
                'name': name,
                'description': description
            }
            self._post_request('/api/projects/create', data)
            return True
        except requests.RequestException:
            return False

    def delete_project(self, project_key: str) -> bool:
        try:
            params = {'project': project_key}
            self._post_request('/api/projects/delete', params)
            return True
        except requests.RequestException:
            return False

    def trigger_analysis(self, project_key: str, branch: str, commit_hash: str) -> str:
        data = {
            'projectKey': project_key,
            'branch': branch,
            'revision': commit_hash
        }
        response = self._post_request('/api/ce/submit', data)
        return response.get('task', {}).get('id', '')

    def get_analysis_status(self, analysis_id: str) -> AnalysisStatus:
        try:
            params = {'id': analysis_id}
            response = self._make_request('/api/ce/task', params)
            status = response.get('task', {}).get('status', 'PENDING')
            
            status_mapping = {
                'PENDING': AnalysisStatus.PENDING,
                'IN_PROGRESS': AnalysisStatus.RUNNING,
                'SUCCESS': AnalysisStatus.COMPLETED,
                'FAILED': AnalysisStatus.FAILED,
                'CANCELED': AnalysisStatus.FAILED
            }
            
            return status_mapping.get(status, AnalysisStatus.PENDING)
        except requests.RequestException:
            return AnalysisStatus.FAILED

    def get_analysis_results(self, analysis_id: str) -> Optional[Analysis]:
        try:
            params = {'id': analysis_id}
            response = self._make_request('/api/ce/task', params)
            task = response.get('task', {})
            
            if task.get('status') != 'SUCCESS':
                return None
            
            project_key = task.get('componentKey', '')
            analysis_data = self._get_project_analysis_data(project_key)
            
            return analysis_data
        except requests.RequestException:
            return None

    def _get_project_analysis_data(self, project_key: str) -> Analysis:
        try:
            metrics = self._get_project_metrics(project_key)
            issues = self._get_project_issues(project_key)
            
            return Analysis(
                id=f"{project_key}_latest",
                project_key=project_key,
                branch="main",
                commit_hash="",
                status=AnalysisStatus.COMPLETED,
                created_at=DateUtils.utc_now(),
                completed_at=DateUtils.utc_now(),
                issues=issues,
                metrics=metrics
            )
        except requests.RequestException:
            return Analysis(
                id=f"{project_key}_error",
                project_key=project_key,
                branch="",
                commit_hash="",
                status=AnalysisStatus.FAILED,
                created_at=DateUtils.utc_now(),
                completed_at=None,
                issues=[],
                metrics=[]
            )

    def _get_project_metrics(self, project_key: str) -> List[Metric]:
        try:
            params = {
                'component': project_key,
                'metricKeys': ','.join(AnalysisConstants.DEFAULT_METRICS)
            }
            response = self._make_request('/api/measures/component', params)
            component = response.get('component', {})
            measures = component.get('measures', [])
            
            metrics = []
            for measure in measures:
                metric = measure.get('metric', '')
                value = measure.get('value', '0')
                
                try:
                    numeric_value = float(value)
                except (ValueError, TypeError):
                    numeric_value = 0.0
                
                metrics.append(Metric(
                    name=metric,
                    value=numeric_value,
                    formatted_value=value
                ))
            
            return metrics
        except requests.RequestException:
            return []

    def _get_project_issues(self, project_key: str) -> List[Issue]:
        try:
            params = {
                'componentKeys': project_key,
                'ps': 500,
                'facets': 'severities,types'
            }
            response = self._make_request('/api/issues/search', params)
            issues_data = response.get('issues', [])
            
            issues = []
            for issue_data in issues_data:
                issue_type_mapping = {
                    'BUG': IssueType.BUG,
                    'VULNERABILITY': IssueType.VULNERABILITY,
                    'CODE_SMELL': IssueType.CODE_SMELL,
                    'SECURITY_HOTSPOT': IssueType.SECURITY_HOTSPOT
                }
                
                severity_mapping = {
                    'BLOCKER': Severity.BLOCKER,
                    'CRITICAL': Severity.CRITICAL,
                    'MAJOR': Severity.MAJOR,
                    'MINOR': Severity.MINOR,
                    'INFO': Severity.INFO
                }
                
                issue = Issue(
                    key=issue_data.get('key', ''),
                    type=issue_type_mapping.get(issue_data.get('type', ''), IssueType.CODE_SMELL),
                    severity=severity_mapping.get(issue_data.get('severity', ''), Severity.MAJOR),
                    message=issue_data.get('message', ''),
                    file_path=issue_data.get('component', ''),
                    line_number=int(issue_data.get('line', 0)),
                    rule=issue_data.get('rule', ''),
                    status=issue_data.get('status', 'OPEN')
                )
                issues.append(issue)
            
            return issues
        except requests.RequestException:
            return []

    def get_project_analyses(self, project_key: str) -> List[Analysis]:
        try:
            analysis = self._get_project_analysis_data(project_key)
            return [analysis] if analysis else []
        except requests.RequestException:
            return []

    def get_project_quality_gate(self, project_key: str) -> Optional[str]:
        try:
            params = {'project': project_key}
            response = self._make_request('/api/qualitygates/project_status', params)
            return response.get('status')
        except requests.RequestException:
            return None

    def set_quality_gate(self, project_key: str, gate_name: str) -> bool:
        try:
            data = {
                'projectKey': project_key,
                'gateName': gate_name
            }
            self._post_request('/api/qualitygates/select', data)
            return True
        except requests.RequestException:
            return False

    def get_project_metrics(self, project_key: str, metrics: List[str]) -> Dict[str, float]:
        try:
            params = {
                'component': project_key,
                'metricKeys': ','.join(metrics)
            }
            response = self._make_request('/api/measures/component', params)
            component = response.get('component', {})
            measures = component.get('measures', [])
            
            result = {}
            for measure in measures:
                metric_name = measure.get('metric', '')
                value = measure.get('value', '0')
                try:
                    result[metric_name] = float(value)
                except (ValueError, TypeError):
                    result[metric_name] = 0.0
            
            return result
        except requests.RequestException:
            return {}

    def get_project_issues(self, project_key: str, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            params = {
                'componentKeys': project_key,
                'ps': 500
            }
            if severity:
                params['severities'] = severity
            
            response = self._make_request('/api/issues/search', params)
            return response.get('issues', [])
        except requests.RequestException:
            return []

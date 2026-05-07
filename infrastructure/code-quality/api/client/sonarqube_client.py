import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json


@dataclass
class AnalysisRequest:
    project_key: str
    branch: str
    commit_hash: str


@dataclass
class ProjectRequest:
    project_key: str
    name: str
    description: str
    languages: List[str]


class SonarQubeClient:
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            })
        else:
            self.session.headers.update({
                'Content-Type': 'application/json'
            })

    def trigger_analysis(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Trigger code analysis for a project"""
        url = f"{self.base_url}/api/v1/analysis/trigger"
        data = {
            'project_key': request.project_key,
            'branch': request.branch,
            'commit_hash': request.commit_hash
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def get_analysis_status(self, analysis_id: str) -> Dict[str, Any]:
        """Get the status of an analysis"""
        url = f"{self.base_url}/api/v1/analysis/{analysis_id}/status"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_analysis_metrics(self, analysis_id: str) -> Dict[str, Any]:
        """Get metrics from an analysis"""
        url = f"{self.base_url}/api/v1/analysis/{analysis_id}/metrics"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_analysis_issues(self, analysis_id: str) -> Dict[str, Any]:
        """Get issues from an analysis"""
        url = f"{self.base_url}/api/v1/analysis/{analysis_id}/issues"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def create_project(self, request: ProjectRequest) -> Dict[str, Any]:
        """Create a new project"""
        url = f"{self.base_url}/api/v1/projects"
        data = {
            'project_key': request.project_key,
            'name': request.name,
            'description': request.description,
            'languages': request.languages
        }
        
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def get_projects(self) -> Dict[str, Any]:
        """List all projects"""
        url = f"{self.base_url}/api/v1/projects"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_project(self, project_key: str) -> Dict[str, Any]:
        """Get project details"""
        url = f"{self.base_url}/api/v1/projects/{project_key}"
        
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_quality_report(self, project_key: str, days: int = 30) -> Dict[str, Any]:
        """Generate quality report for a project"""
        url = f"{self.base_url}/api/v1/projects/{project_key}/report"
        params = {'days': days}
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def wait_for_analysis_completion(self, analysis_id: str, timeout_seconds: int = 3600) -> Dict[str, Any]:
        """Wait for analysis to complete and return results"""
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            status_data = self.get_analysis_status(analysis_id)
            status = status_data.get('status')
            
            if status == 'completed':
                return status_data
            elif status == 'failed':
                raise RuntimeError(f"Analysis failed: {status_data}")
            
            time.sleep(30)  # Check every 30 seconds
        
        raise TimeoutError(f"Analysis did not complete within {timeout_seconds} seconds")

    def get_project_health(self, project_key: str) -> Dict[str, Any]:
        """Get comprehensive project health information"""
        try:
            project_data = self.get_project(project_key)
            report_data = self.get_quality_report(project_key, days=7)
            
            # Get latest analysis
            analyses = self.get_projects().get('projects', [])
            latest_analysis = None
            
            for project in analyses:
                if project.get('key') == project_key:
                    # This would need to be enhanced to get actual analyses
                    break
            
            return {
                'project': project_data.get('project'),
                'health_score': self._calculate_health_score(report_data),
                'recent_issues': report_data.get('report', {}).get('quality_metrics', {}),
                'recommendations': report_data.get('report', {}).get('recommendations', []),
                'last_analysis': latest_analysis
            }
        except Exception as e:
            return {
                'error': str(e),
                'project_key': project_key
            }

    def _calculate_health_score(self, report_data: Dict[str, Any]) -> float:
        """Calculate overall health score from report data"""
        try:
            report = report_data.get('report', {})
            summary = report.get('summary', {})
            quality_metrics = report.get('quality_metrics', {})
            
            base_score = 100.0
            
            # Deduct for failed analyses
            failed_analyses = summary.get('failed_analyses', 0)
            total_analyses = summary.get('total_analyses', 1)
            failure_rate = failed_analyses / total_analyses if total_analyses > 0 else 0
            base_score -= failure_rate * 20
            
            # Deduct for critical issues
            critical_issues = quality_metrics.get('critical_issues', 0)
            base_score -= critical_issues * 5
            
            # Deduct for security issues
            security_issues = quality_metrics.get('security_issues', 0)
            base_score -= security_issues * 3
            
            # Bonus for good coverage
            avg_coverage = quality_metrics.get('average_coverage', 0)
            if avg_coverage >= 80:
                base_score += 5
            elif avg_coverage >= 60:
                base_score += 2
            
            return max(0.0, min(100.0, base_score))
        except Exception:
            return 50.0  # Default score if calculation fails

    def export_analysis_report(self, analysis_id: str, format: str = 'json') -> str:
        """Export analysis report in specified format"""
        analysis_data = self.get_analysis_status(analysis_id)
        metrics_data = self.get_analysis_metrics(analysis_id)
        issues_data = self.get_analysis_issues(analysis_id)
        
        report = {
            'analysis': analysis_data,
            'metrics': metrics_data,
            'issues': issues_data
        }
        
        if format.lower() == 'json':
            return json.dumps(report, indent=2)
        elif format.lower() == 'csv':
            return self._convert_to_csv(report)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _convert_to_csv(self, report: Dict[str, Any]) -> str:
        """Convert report to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write analysis summary
        analysis = report.get('analysis', {})
        writer.writerow(['Analysis Summary'])
        writer.writerow(['Analysis ID', analysis.get('analysis_id')])
        writer.writerow(['Project Key', analysis.get('project_key')])
        writer.writerow(['Status', analysis.get('status')])
        writer.writerow(['Quality Score', analysis.get('quality_score')])
        writer.writerow([])
        
        # Write issues
        issues = report.get('issues', {}).get('issues', [])
        writer.writerow(['Issues'])
        writer.writerow(['Type', 'Severity', 'File', 'Line', 'Message', 'Rule'])
        
        for issue in issues:
            writer.writerow([
                issue.get('type'),
                issue.get('severity'),
                issue.get('file_path'),
                issue.get('line_number'),
                issue.get('message'),
                issue.get('rule')
            ])
        
        return output.getvalue()


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = SonarQubeClient("http://localhost:5000", "your-api-key")
    
    # Create project
    project_request = ProjectRequest(
        project_key="my-project",
        name="My Project",
        description="A sample project",
        languages=["python", "javascript"]
    )
    
    try:
        project = client.create_project(project_request)
        print(f"Created project: {project}")
        
        # Trigger analysis
        analysis_request = AnalysisRequest(
            project_key="my-project",
            branch="main",
            commit_hash="abc123"
        )
        
        analysis = client.trigger_analysis(analysis_request)
        print(f"Triggered analysis: {analysis}")
        
        # Wait for completion
        result = client.wait_for_analysis_completion(analysis['analysis_id'])
        print(f"Analysis completed: {result}")
        
    except Exception as e:
        print(f"Error: {e}")

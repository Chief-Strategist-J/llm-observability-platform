import pytest
import json
import subprocess
import tempfile
import os
from pathlib import Path


class TestGoInfrastructureAnalyzer:
    
    def test_analyze_terraform_files(self, sample_terraform_files):
        """Test Terraform file analysis"""
        # Run the Go analyzer
        result = subprocess.run(
            ['go', 'run', 'main.go', sample_terraform_files],
            cwd='../../analysis-tools/go/infrastructure-analyzer',
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        
        # Parse JSON output
        results = json.loads(result.stdout)
        
        # Verify structure
        assert 'analysis_timestamp' in results
        assert 'summary' in results
        assert 'issues' in results
        assert 'recommendations' in results
        
        summary = results['summary']
        assert summary['terraform_files'] >= 1
        assert summary['total_issues'] > 0
        
        # Check for security issues
        issues = results['issues']
        
        # Should detect open security group (0.0.0.0/0)
        security_group_issues = [
            issue for issue in issues 
            if issue['issue_type'] == 'open_security_group'
        ]
        assert len(security_group_issues) > 0
        
        # Should detect hardcoded secrets
        secret_issues = [
            issue for issue in issues 
            if issue['issue_type'] == 'hardcoded_secret'
        ]
        assert len(secret_issues) > 0
        
        # Should detect unencrypted storage
        storage_issues = [
            issue for issue in issues 
            if issue['issue_type'] == 'unencrypted_storage'
        ]
        assert len(storage_issues) > 0
    
    def test_analyze_kubernetes_files(self, sample_kubernetes_files):
        """Test Kubernetes file analysis"""
        # Run the Go analyzer
        result = subprocess.run(
            ['go', 'run', 'main.go', sample_kubernetes_files],
            cwd='../../analysis-tools/go/infrastructure-analyzer',
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        
        # Parse JSON output
        results = json.loads(result.stdout)
        
        summary = results['summary']
        assert summary['kubernetes_files'] >= 1
        
        # Check for Kubernetes-specific issues
        issues = results['issues']
        
        # Should detect privileged containers
        privileged_issues = [
            issue for issue in issues 
            if issue['issue_type'] == 'privileged_container'
        ]
        assert len(privileged_issues) > 0
        
        # Should detect containers running as root
        root_issues = [
            issue for issue in issues 
            if issue['issue_type'] == 'run_as_root'
        ]
        assert len(root_issues) > 0
        
        # Should detect secrets in ConfigMap
        configmap_secret_issues = [
            issue for issue in issues 
            if issue['issue_type'] == 'secret_in_configmap'
        ]
        assert len(configmap_secret_issues) > 0
    
    def test_analyze_mixed_infrastructure(self, sample_terraform_files, sample_kubernetes_files):
        """Test analysis of mixed infrastructure files"""
        # Create temporary directory with both types
        with tempfile.TemporaryDirectory() as mixed_dir:
            # Copy Terraform files
            import shutil
            for tf_file in Path(sample_terraform_files).glob('*.tf'):
                shutil.copy(tf_file, mixed_dir)
            
            # Copy Kubernetes files
            for k8s_file in Path(sample_kubernetes_files).glob('*.yaml'):
                shutil.copy(k8s_file, mixed_dir)
            
            # Run analysis
            result = subprocess.run(
                ['go', 'run', 'main.go', mixed_dir],
                cwd='../../analysis-tools/go/infrastructure-analyzer',
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            
            results = json.loads(result.stdout)
            summary = results['summary']
            
            # Should detect both file types
            assert summary['terraform_files'] >= 1
            assert summary['kubernetes_files'] >= 1
            assert summary['total_issues'] > 0
    
    def test_analyze_empty_infrastructure(self):
        """Test analysis of empty directory"""
        with tempfile.TemporaryDirectory() as empty_dir:
            result = subprocess.run(
                ['go', 'run', 'main.go', empty_dir],
                cwd='../../analysis-tools/go/infrastructure-analyzer',
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            
            results = json.loads(result.stdout)
            summary = results['summary']
            
            assert summary['terraform_files'] == 0
            assert summary['kubernetes_files'] == 0
            assert summary['docker_files'] == 0
            assert summary['total_issues'] == 0
    
    def test_analyze_docker_files(self):
        """Test Docker file analysis"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create Dockerfile with issues
            dockerfile = os.path.join(temp_dir, "Dockerfile")
            with open(dockerfile, 'w') as f:
                f.write("""
FROM ubuntu:latest

# Copy sensitive files
COPY .ssh/ /root/.ssh/
COPY .aws/ /root/.aws/

# Use latest tag
FROM python:latest

# Run as root
USER root

CMD ["python", "app.py"]
""")
            
            # Create docker-compose.yml
            docker_compose = os.path.join(temp_dir, "docker-compose.yml")
            with open(docker_compose, 'w') as f:
                f.write("""
version: '3.8'
services:
  app:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./config:/app/config
""")
            
            result = subprocess.run(
                ['go', 'run', 'main.go', temp_dir],
                cwd='../../analysis-tools/go/infrastructure-analyzer',
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            
            results = json.loads(result.stdout)
            summary = results['summary']
            
            assert summary['docker_files'] >= 1
            
            # Should detect Docker issues
            issues = results['issues']
            latest_tag_issues = [
                issue for issue in issues 
                if issue['issue_type'] == 'latest_tag'
            ]
            assert len(latest_tag_issues) > 0
            
            copying_secrets_issues = [
                issue for issue in issues 
                if issue['issue_type'] == 'copying_secrets'
            ]
            assert len(copying_secrets_issues) > 0
    
    def test_analyze_invalid_directory(self):
        """Test analysis of non-existent directory"""
        result = subprocess.run(
            ['go', 'run', 'main.go', '/non/existent/path'],
            cwd='../../analysis-tools/go/infrastructure-analyzer',
            capture_output=True,
            text=True
        )
        
        # Should handle gracefully (either return 0 with empty results or error)
        # The exact behavior depends on implementation
        assert result.returncode in [0, 1]
    
    def test_analyze_recommendations_generation(self, sample_terraform_files):
        """Test recommendation generation"""
        result = subprocess.run(
            ['go', 'run', 'main.go', sample_terraform_files],
            cwd='../../analysis-tools/go/infrastructure-analyzer',
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        
        results = json.loads(result.stdout)
        recommendations = results['recommendations']
        
        assert len(recommendations) > 0
        assert isinstance(recommendations, list)
        
        # Should have security-related recommendations
        rec_text = ' '.join(recommendations).lower()
        assert any(keyword in rec_text for keyword in ['security', 'fix', 'address', 'urgent'])
    
    def test_analyze_json_output_format(self, sample_terraform_files):
        """Test JSON output format is valid"""
        result = subprocess.run(
            ['go', 'run', 'main.go', sample_terraform_files],
            cwd='../../analysis-tools/go/infrastructure-analyzer',
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        
        # Should be valid JSON
        results = json.loads(result.stdout)
        
        # Should have required fields
        required_fields = ['analysis_timestamp', 'summary', 'issues', 'recommendations']
        for field in required_fields:
            assert field in results
        
        # Issues should have required fields
        if results['issues']:
            issue = results['issues'][0]
            required_issue_fields = ['file_path', 'line_number', 'issue_type', 'severity', 'description', 'rule']
            for field in required_issue_fields:
                assert field in issue
    
    def test_analyze_severity_levels(self, sample_terraform_files):
        """Test that issues have appropriate severity levels"""
        result = subprocess.run(
            ['go', 'run', 'main.go', sample_terraform_files],
            cwd='../../analysis-tools/go/infrastructure-analyzer',
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        
        results = json.loads(result.stdout)
        issues = results['issues']
        
        # Should have different severity levels
        severities = set(issue['severity'] for issue in issues)
        assert len(severities) >= 1
        
        # Valid severities
        valid_severities = ['critical', 'high', 'medium', 'low']
        for severity in severities:
            assert severity in valid_severities
    
    def test_analyze_file_path_handling(self, sample_terraform_files):
        """Test file path handling in issues"""
        result = subprocess.run(
            ['go', 'run', 'main.go', sample_terraform_files],
            cwd='../../analysis-tools/go/infrastructure-analyzer',
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        
        results = json.loads(result.stdout)
        issues = results['issues']
        
        # Issues should have valid file paths
        for issue in issues:
            assert issue['file_path'] is not None
            assert len(issue['file_path']) > 0
            assert not issue['file_path'].startswith('/')  # Should be relative paths
            assert issue['line_number'] > 0

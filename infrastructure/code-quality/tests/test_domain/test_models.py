import pytest
from datetime import datetime, timezone

from domain.models.analysis import Analysis, AnalysisStatus, Issue, Metric, IssueType, Severity
from domain.models.project import Project, ProjectStatus, QualityGateStatus, QualityGate


class TestAnalysis:
    
    def test_analysis_creation(self, sample_analysis):
        """Test analysis object creation"""
        assert sample_analysis.id == "test-analysis-123"
        assert sample_analysis.project_key == "test-project"
        assert sample_analysis.status == AnalysisStatus.COMPLETED
        assert len(sample_analysis.issues) == 1
        assert len(sample_analysis.metrics) == 1
    
    def test_analysis_is_complete(self, sample_analysis):
        """Test is_complete method"""
        assert sample_analysis.is_complete() is True
        
        sample_analysis.status = AnalysisStatus.RUNNING
        assert sample_analysis.is_complete() is False
    
    def test_analysis_has_blocking_issues(self, sample_analysis):
        """Test has_blocking_issues method"""
        assert sample_analysis.has_blocking_issues() is False
        
        # Add a blocking issue
        blocking_issue = Issue(
            key="BLOCKING-1",
            type=IssueType.VULNERABILITY,
            severity=Severity.BLOCKER,
            message="Blocking issue",
            file_path="test.py",
            line_number=1,
            rule="BLOCKING_RULE",
            status="OPEN"
        )
        sample_analysis.issues.append(blocking_issue)
        
        assert sample_analysis.has_blocking_issues() is True
    
    def test_analysis_get_critical_issues_count(self, sample_analysis):
        """Test get_critical_issues_count method"""
        assert sample_analysis.get_critical_issues_count() == 0
        
        # Add critical issues
        critical_issue = Issue(
            key="CRITICAL-1",
            type=IssueType.BUG,
            severity=Severity.CRITICAL,
            message="Critical issue",
            file_path="test.py",
            line_number=1,
            rule="CRITICAL_RULE",
            status="OPEN"
        )
        sample_analysis.issues.append(critical_issue)
        
        assert sample_analysis.get_critical_issues_count() == 1
    
    def test_analysis_get_coverage_metric(self, sample_analysis):
        """Test get_coverage_metric method"""
        coverage = sample_analysis.get_coverage_metric()
        assert coverage == 85.5
        
        # Test when no coverage metric exists
        sample_analysis.metrics = []
        coverage = sample_analysis.get_coverage_metric()
        assert coverage is None
    
    def test_analysis_get_issues_by_severity(self, sample_analysis):
        """Test get_issues_by_severity method"""
        major_issues = sample_analysis.get_issues_by_severity(Severity.MAJOR)
        assert len(major_issues) == 1
        assert major_issues[0].severity == Severity.MAJOR
        
        critical_issues = sample_analysis.get_issues_by_severity(Severity.CRITICAL)
        assert len(critical_issues) == 0
    
    def test_analysis_get_issues_by_type(self, sample_analysis):
        """Test get_issues_by_type method"""
        bug_issues = sample_analysis.get_issues_by_type(IssueType.BUG)
        assert len(bug_issues) == 1
        assert bug_issues[0].type == IssueType.BUG
        
        vuln_issues = sample_analysis.get_issues_by_type(IssueType.VULNERABILITY)
        assert len(vuln_issues) == 0


class TestIssue:
    
    def test_issue_creation(self):
        """Test issue object creation"""
        issue = Issue(
            key="ISSUE-1",
            type=IssueType.BUG,
            severity=Severity.MAJOR,
            message="Test issue",
            file_path="test.py",
            line_number=10,
            rule="TEST_RULE",
            status="OPEN"
        )
        
        assert issue.key == "ISSUE-1"
        assert issue.type == IssueType.BUG
        assert issue.severity == Severity.MAJOR
        assert issue.line_number == 10
    
    def test_issue_is_blocking(self):
        """Test is_blocking method"""
        blocker_issue = Issue(
            key="BLOCKER-1",
            type=IssueType.VULNERABILITY,
            severity=Severity.BLOCKER,
            message="Blocker issue",
            file_path="test.py",
            line_number=1,
            rule="BLOCKER_RULE",
            status="OPEN"
        )
        assert blocker_issue.is_blocking() is True
        
        critical_issue = Issue(
            key="CRITICAL-1",
            type=IssueType.BUG,
            severity=Severity.CRITICAL,
            message="Critical issue",
            file_path="test.py",
            line_number=1,
            rule="CRITICAL_RULE",
            status="OPEN"
        )
        assert critical_issue.is_blocking() is True
        
        major_issue = Issue(
            key="MAJOR-1",
            type=IssueType.BUG,
            severity=Severity.MAJOR,
            message="Major issue",
            file_path="test.py",
            line_number=1,
            rule="MAJOR_RULE",
            status="OPEN"
        )
        assert major_issue.is_blocking() is False
    
    def test_issue_is_security_related(self):
        """Test is_security_related method"""
        vuln_issue = Issue(
            key="VULN-1",
            type=IssueType.VULNERABILITY,
            severity=Severity.HIGH,
            message="Vulnerability",
            file_path="test.py",
            line_number=1,
            rule="VULN_RULE",
            status="OPEN"
        )
        assert vuln_issue.is_security_related() is True
        
        hotspot_issue = Issue(
            key="HOTSPOT-1",
            type=IssueType.SECURITY_HOTSPOT,
            severity=Severity.MEDIUM,
            message="Security hotspot",
            file_path="test.py",
            line_number=1,
            rule="HOTSPOT_RULE",
            status="OPEN"
        )
        assert hotspot_issue.is_security_related() is True
        
        bug_issue = Issue(
            key="BUG-1",
            type=IssueType.BUG,
            severity=Severity.MAJOR,
            message="Bug",
            file_path="test.py",
            line_number=1,
            rule="BUG_RULE",
            status="OPEN"
        )
        assert bug_issue.is_security_related() is False


class TestMetric:
    
    def test_metric_creation(self):
        """Test metric object creation"""
        metric = Metric(
            name="coverage",
            value=85.5,
            formatted_value="85.5%"
        )
        
        assert metric.name == "coverage"
        assert metric.value == 85.5
        assert metric.formatted_value == "85.5%"
    
    def test_metric_is_percentage(self):
        """Test is_percentage method"""
        percentage_metric = Metric(
            name="coverage",
            value=85.5,
            formatted_value="85.5%"
        )
        assert percentage_metric.is_percentage() is True
        
        time_metric = Metric(
            name="complexity",
            value=25.0,
            formatted_value="25"
        )
        assert time_metric.is_percentage() is False
    
    def test_metric_is_time_based(self):
        """Test is_time_based method"""
        ms_metric = Metric(
            name="response_time",
            value=150.0,
            formatted_value="150ms"
        )
        assert ms_metric.is_time_based() is True
        
        s_metric = Metric(
            name="duration",
            value=2.5,
            formatted_value="2.5s"
        )
        assert s_metric.is_time_based() is True
        
        non_time_metric = Metric(
            name="coverage",
            value=85.5,
            formatted_value="85.5%"
        )
        assert non_time_metric.is_time_based() is False


@pytest.fixture
def sample_project():
    return Project(
        key="test-project",
        name="Test Project",
        description="A test project",
        status=ProjectStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
        last_analysis_at=datetime.now(timezone.utc),
        quality_gate_status=QualityGateStatus.NONE,
        languages=["python", "javascript"]
    )


class TestProject:
    
    def test_project_creation(self, sample_project):
        """Test project object creation"""
        assert sample_project.key == "test-project"
        assert sample_project.name == "Test Project"
        assert sample_project.status == ProjectStatus.ACTIVE
        assert "python" in sample_project.languages
        assert "javascript" in sample_project.languages
    
    def test_project_is_active(self, sample_project):
        """Test is_active method"""
        assert sample_project.is_active() is True
        
        sample_project.status = ProjectStatus.INACTIVE
        assert sample_project.is_active() is False
        
        sample_project.status = ProjectStatus.ARCHIVED
        assert sample_project.is_active() is False
    
    def test_project_has_recent_analysis(self, sample_project):
        """Test has_recent_analysis method"""
        # No analysis yet
        sample_project.last_analysis_at = None
        assert sample_project.has_recent_analysis() is False
        
        # Recent analysis (within 7 days)
        sample_project.last_analysis_at = datetime.now(timezone.utc)
        assert sample_project.has_recent_analysis() is True
        
        # Old analysis (more than 7 days)
        from datetime import timedelta
        old_date = datetime.now(timezone.utc) - timedelta(days=15)
        sample_project.last_analysis_at = old_date
        assert sample_project.has_recent_analysis() is False
    
    def test_project_supports_language(self, sample_project):
        """Test supports_language method"""
        assert sample_project.supports_language("python") is True
        assert sample_project.supports_language("javascript") is True
        assert sample_project.supports_language("java") is False
        assert sample_project.supports_language("PYTHON") is True  # Case insensitive
    
    def test_project_is_quality_gate_passed(self, sample_project):
        """Test is_quality_gate_passed method"""
        sample_project.quality_gate_status = QualityGateStatus.PASSED
        assert sample_project.is_quality_gate_passed() is True
        
        sample_project.quality_gate_status = QualityGateStatus.FAILED
        assert sample_project.is_quality_gate_passed() is False
        
        sample_project.quality_gate_status = QualityGateStatus.WARNING
        assert sample_project.is_quality_gate_passed() is False
        
        sample_project.quality_gate_status = QualityGateStatus.NONE
        assert sample_project.is_quality_gate_passed() is False


class TestQualityGate:
    
    def test_quality_gate_creation(self):
        """Test quality gate object creation"""
        quality_gate = QualityGate(
            id="gate-1",
            name="Default Gate",
            project_key="test-project",
            status=QualityGateStatus.PASSED,
            conditions=["coverage >= 80", "duplicated_lines_density <= 3"]
        )
        
        assert quality_gate.id == "gate-1"
        assert quality_gate.name == "Default Gate"
        assert quality_gate.project_key == "test-project"
        assert len(quality_gate.conditions) == 2
    
    def test_quality_gate_is_passed(self):
        """Test is_passed method"""
        passed_gate = QualityGate(
            id="gate-1",
            name="Passed Gate",
            project_key="test-project",
            status=QualityGateStatus.PASSED,
            conditions=[]
        )
        assert passed_gate.is_passed() is True
        
        failed_gate = QualityGate(
            id="gate-2",
            name="Failed Gate",
            project_key="test-project",
            status=QualityGateStatus.FAILED,
            conditions=[]
        )
        assert failed_gate.is_passed() is False
    
    def test_quality_gate_has_failed(self):
        """Test has_failed method"""
        failed_gate = QualityGate(
            id="gate-1",
            name="Failed Gate",
            project_key="test-project",
            status=QualityGateStatus.FAILED,
            conditions=[]
        )
        assert failed_gate.has_failed() is True
        
        passed_gate = QualityGate(
            id="gate-2",
            name="Passed Gate",
            project_key="test-project",
            status=QualityGateStatus.PASSED,
            conditions=[]
        )
        assert passed_gate.has_failed() is False

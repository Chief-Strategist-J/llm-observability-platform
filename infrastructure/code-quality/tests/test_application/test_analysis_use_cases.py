import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from application.analysis.trigger_analysis_use_case import TriggerAnalysisUseCase
from application.analysis.check_analysis_status_use_case import CheckAnalysisStatusUseCase
from domain.models.analysis import Analysis, AnalysisStatus, Issue, Metric, IssueType, Severity
from domain.models.project import Project, ProjectStatus, QualityGateStatus


class TestTriggerAnalysisUseCase:
    
    def test_execute_success(self, mock_sonarqube_service, analysis_repository, project_repository):
        """Test successful analysis triggering"""
        # Setup
        project = Project(
            key="test-project",
            name="Test Project",
            description="Test",
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            last_analysis_at=None,
            quality_gate_status=QualityGateStatus.NONE,
            languages=["python"]
        )
        project_repository.save(project)
        
        mock_sonarqube_service.trigger_analysis.return_value = "task-123"
        
        use_case = TriggerAnalysisUseCase(
            analysis_repository,
            project_repository,
            mock_sonarqube_service,
            Mock()
        )
        
        # Execute
        analysis_id = use_case.execute("test-project", "main", "abc123def456789012345678901234567890abcd")
        
        # Verify
        assert analysis_id is not None
        assert "test-project" in analysis_id
        assert "abc123" in analysis_id
        
        # Check analysis was saved
        saved_analysis = analysis_repository.find_by_id(analysis_id)
        assert saved_analysis is not None
        assert saved_analysis.project_key == "test-project"
        assert saved_analysis.branch == "main"
        assert saved_analysis.commit_hash == "abc123def456789012345678901234567890abcd"
        assert saved_analysis.status == AnalysisStatus.RUNNING
        
        # Verify SonarQube was called
        mock_sonarqube_service.trigger_analysis.assert_called_once_with(
            "test-project", "main", "abc123def456789012345678901234567890abcd"
        )
    
    def test_execute_project_not_found(self, analysis_repository, project_repository):
        """Test execution with non-existent project"""
        use_case = TriggerAnalysisUseCase(
            analysis_repository,
            project_repository,
            Mock(),
            Mock()
        )
        
        with pytest.raises(ValueError, match="Project with key 'non-existent' not found"):
            use_case.execute("non-existent", "main", "abc123def456")
    
    def test_execute_existing_analysis(self, mock_sonarqube_service, analysis_repository, project_repository):
        """Test execution with existing analysis for same commit"""
        # Setup project
        project = Project(
            key="test-project",
            name="Test Project",
            description="Test",
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            last_analysis_at=None,
            quality_gate_status=QualityGateStatus.NONE,
            languages=["python"]
        )
        project_repository.save(project)
        
        # Setup existing analysis
        existing_analysis = Analysis(
            id="existing-analysis",
            project_key="test-project",
            branch="main",
            commit_hash="abc123def456",
            status=AnalysisStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            issues=[],
            metrics=[]
        )
        analysis_repository.save(existing_analysis)
        
        use_case = TriggerAnalysisUseCase(
            analysis_repository,
            project_repository,
            mock_sonarqube_service,
            Mock()
        )
        
        # Execute
        analysis_id = use_case.execute("test-project", "main", "abc123def456")
        
        # Should return existing analysis ID
        assert analysis_id == "existing-analysis"
        
        # SonarQube should not be called again
        mock_sonarqube_service.trigger_analysis.assert_not_called()
    
    def test_execute_sonarqube_failure(self, mock_sonarqube_service, analysis_repository, project_repository):
        """Test execution when SonarQube call fails"""
        # Setup project
        project = Project(
            key="test-project",
            name="Test Project",
            description="Test",
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            last_analysis_at=None,
            quality_gate_status=QualityGateStatus.NONE,
            languages=["python"]
        )
        project_repository.save(project)
        
        # Mock SonarQube failure
        mock_sonarqube_service.trigger_analysis.side_effect = Exception("SonarQube error")
        
        use_case = TriggerAnalysisUseCase(
            analysis_repository,
            project_repository,
            mock_sonarqube_service,
            Mock()
        )
        
        # Execute and verify error
        with pytest.raises(RuntimeError, match="Failed to trigger SonarQube analysis"):
            use_case.execute("test-project", "main", "abc123def456")
        
        # Check analysis status was updated to FAILED
        analyses = analysis_repository.find_by_project("test-project")
        assert len(analyses) > 0
        latest_analysis = max(analyses, key=lambda a: a.created_at)
        assert latest_analysis.status == AnalysisStatus.FAILED
    
    def test_execute_validation_errors(self, analysis_repository, project_repository):
        """Test execution with invalid input"""
        use_case = TriggerAnalysisUseCase(
            analysis_repository,
            project_repository,
            Mock(),
            Mock()
        )
        
        # Test invalid project key
        with pytest.raises(ValueError, match="Validation failed"):
            use_case.execute("", "main", "abc123def456")
        
        # Test invalid branch
        with pytest.raises(ValueError, match="Validation failed"):
            use_case.execute("test-project", "", "abc123def456")
        
        # Test invalid commit hash
        with pytest.raises(ValueError, match="Validation failed"):
            use_case.execute("test-project", "main", "invalid")


class TestCheckAnalysisStatusUseCase:
    
    def test_execute_completed_analysis(self, mock_sonarqube_service, analysis_repository):
        """Test checking status of completed analysis"""
        # Setup analysis
        analysis = Analysis(
            id="test-analysis",
            project_key="test-project",
            branch="main",
            commit_hash="abc123def456",
            status=AnalysisStatus.RUNNING,
            created_at=datetime.now(timezone.utc),
            completed_at=None,
            issues=[],
            metrics=[]
        )
        analysis_repository.save(analysis)
        
        # Mock SonarQube response
        mock_sonarqube_service.get_analysis_status.return_value = AnalysisStatus.COMPLETED
        mock_sonarqube_service.get_analysis_results.return_value = Analysis(
            id="test-analysis",
            project_key="test-project",
            branch="main",
            commit_hash="abc123def456",
            status=AnalysisStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            issues=[
                Issue(
                    key="ISSUE-1",
                    type=IssueType.BUG,
                    severity=Severity.MAJOR,
                    message="Test issue",
                    file_path="test.py",
                    line_number=10,
                    rule="TEST_RULE",
                    status="OPEN"
                )
            ],
            metrics=[
                Metric(name="coverage", value=85.0, formatted_value="85.0%")
            ]
        )
        
        use_case = CheckAnalysisStatusUseCase(
            analysis_repository,
            mock_sonarqube_service,
            Mock()
        )
        
        # Execute
        result = use_case.execute("test-analysis")
        
        # Verify
        assert result.status == AnalysisStatus.COMPLETED
        assert len(result.issues) == 1
        assert len(result.metrics) == 1
        assert result.completed_at is not None
        
        # Verify repository was updated
        updated_analysis = analysis_repository.find_by_id("test-analysis")
        assert updated_analysis.status == AnalysisStatus.COMPLETED
        assert updated_analysis.completed_at is not None
    
    def test_execute_running_analysis(self, mock_sonarqube_service, analysis_repository):
        """Test checking status of running analysis"""
        # Setup analysis
        analysis = Analysis(
            id="test-analysis",
            project_key="test-project",
            branch="main",
            commit_hash="abc123def456",
            status=AnalysisStatus.RUNNING,
            created_at=datetime.now(timezone.utc),
            completed_at=None,
            issues=[],
            metrics=[]
        )
        analysis_repository.save(analysis)
        
        # Mock SonarQube response
        mock_sonarqube_service.get_analysis_status.return_value = AnalysisStatus.RUNNING
        
        use_case = CheckAnalysisStatusUseCase(
            analysis_repository,
            mock_sonarqube_service,
            Mock()
        )
        
        # Execute
        result = use_case.execute("test-analysis")
        
        # Verify
        assert result.status == AnalysisStatus.RUNNING
        assert len(result.issues) == 0
        assert len(result.metrics) == 0
    
    def test_execute_analysis_not_found(self, analysis_repository):
        """Test checking status of non-existent analysis"""
        use_case = CheckAnalysisStatusUseCase(
            analysis_repository,
            Mock(),
            Mock()
        )
        
        with pytest.raises(ValueError, match="Analysis with ID 'non-existent' not found"):
            use_case.execute("non-existent")
    
    def test_execute_sonarqube_failure_on_completion(self, mock_sonarqube_service, analysis_repository):
        """Test handling SonarQube failure when processing completed analysis"""
        # Setup analysis
        analysis = Analysis(
            id="test-analysis",
            project_key="test-project",
            branch="main",
            commit_hash="abc123def456",
            status=AnalysisStatus.RUNNING,
            created_at=datetime.now(timezone.utc),
            completed_at=None,
            issues=[],
            metrics=[]
        )
        analysis_repository.save(analysis)
        
        # Mock SonarQube - status is completed but results call fails
        mock_sonarqube_service.get_analysis_status.return_value = AnalysisStatus.COMPLETED
        mock_sonarqube_service.get_analysis_results.side_effect = Exception("Results fetch failed")
        
        use_case = CheckAnalysisStatusUseCase(
            analysis_repository,
            mock_sonarqube_service,
            Mock()
        )
        
        # Execute
        with pytest.raises(RuntimeError, match="Failed to process completed analysis"):
            use_case.execute("test-analysis")
        
        # Check analysis status was updated to FAILED
        updated_analysis = analysis_repository.find_by_id("test-analysis")
        assert updated_analysis.status == AnalysisStatus.FAILED
    
    def test_is_analysis_ready_for_merge_true(self, mock_sonarqube_service, analysis_repository):
        """Test is_analysis_ready_for_merge when ready"""
        # Setup completed analysis with no blocking issues
        analysis = Analysis(
            id="test-analysis",
            project_key="test-project",
            branch="main",
            commit_hash="abc123def456",
            status=AnalysisStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            issues=[
                Issue(
                    key="MINOR-1",
                    type=IssueType.CODE_SMELL,
                    severity=Severity.MINOR,
                    message="Minor issue",
                    file_path="test.py",
                    line_number=1,
                    rule="MINOR_RULE",
                    status="OPEN"
                )
            ],
            metrics=[Metric(name="coverage", value=85.0, formatted_value="85.0%")]
        )
        analysis_repository.save(analysis)
        
        mock_sonarqube_service.get_analysis_status.return_value = AnalysisStatus.COMPLETED
        
        use_case = CheckAnalysisStatusUseCase(
            analysis_repository,
            mock_sonarqube_service,
            Mock()
        )
        
        # Execute
        ready = use_case.is_analysis_ready_for_merge("test-analysis")
        
        # Verify
        assert ready is True
    
    def test_is_analysis_ready_for_merge_false_blocking_issues(self, mock_sonarqube_service, analysis_repository):
        """Test is_analysis_ready_for_merge with blocking issues"""
        # Setup completed analysis with blocking issues
        analysis = Analysis(
            id="test-analysis",
            project_key="test-project",
            branch="main",
            commit_hash="abc123def456",
            status=AnalysisStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            issues=[
                Issue(
                    key="BLOCKER-1",
                    type=IssueType.VULNERABILITY,
                    severity=Severity.BLOCKER,
                    message="Blocker issue",
                    file_path="test.py",
                    line_number=1,
                    rule="BLOCKER_RULE",
                    status="OPEN"
                )
            ],
            metrics=[Metric(name="coverage", value=85.0, formatted_value="85.0%")]
        )
        analysis_repository.save(analysis)
        
        mock_sonarqube_service.get_analysis_status.return_value = AnalysisStatus.COMPLETED
        
        use_case = CheckAnalysisStatusUseCase(
            analysis_repository,
            mock_sonarqube_service,
            Mock()
        )
        
        # Execute
        ready = use_case.is_analysis_ready_for_merge("test-analysis")
        
        # Verify
        assert ready is False
    
    def test_get_analysis_summary(self, mock_sonarqube_service, analysis_repository):
        """Test get_analysis_summary method"""
        # Setup analysis
        analysis = Analysis(
            id="test-analysis",
            project_key="test-project",
            branch="main",
            commit_hash="abc123def456",
            status=AnalysisStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            issues=[
                Issue(
                    key="ISSUE-1",
                    type=IssueType.BUG,
                    severity=Severity.MAJOR,
                    message="Test issue",
                    file_path="test.py",
                    line_number=10,
                    rule="TEST_RULE",
                    status="OPEN"
                )
            ],
            metrics=[Metric(name="coverage", value=85.0, formatted_value="85.0%")]
        )
        analysis_repository.save(analysis)
        
        mock_sonarqube_service.get_analysis_status.return_value = AnalysisStatus.COMPLETED
        
        use_case = CheckAnalysisStatusUseCase(
            analysis_repository,
            mock_sonarqube_service,
            Mock()
        )
        
        # Execute
        summary = use_case.get_analysis_summary("test-analysis")
        
        # Verify
        assert "Found 1 issues" in summary
        assert "85.0% coverage" in summary
    
    def test_get_quality_score(self, mock_sonarqube_service, analysis_repository):
        """Test get_quality_score method"""
        # Setup analysis
        analysis = Analysis(
            id="test-analysis",
            project_key="test-project",
            branch="main",
            commit_hash="abc123def456",
            status=AnalysisStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            issues=[],
            metrics=[Metric(name="coverage", value=90.0, formatted_value="90.0%")]
        )
        analysis_repository.save(analysis)
        
        mock_sonarqube_service.get_analysis_status.return_value = AnalysisStatus.COMPLETED
        
        use_case = CheckAnalysisStatusUseCase(
            analysis_repository,
            mock_sonarqube_service,
            Mock()
        )
        
        # Execute
        score = use_case.get_quality_score("test-analysis")
        
        # Verify
        assert score == 100.0  # Perfect score for analysis with no issues and good coverage

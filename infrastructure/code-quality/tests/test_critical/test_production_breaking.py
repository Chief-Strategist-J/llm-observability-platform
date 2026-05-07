"""
Critical production-breaking tests for SonarQube Code Quality Infrastructure
These tests simulate scenarios that could cause production failures
"""
import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from domain.models.analysis import Analysis, AnalysisStatus, Issue, Metric, IssueType, Severity
from domain.models.project import Project, ProjectStatus, QualityGateStatus
from domain.services.analysis_domain_service import AnalysisDomainService
from application.analysis.trigger_analysis_use_case import TriggerAnalysisUseCase
from application.analysis.check_analysis_status_use_case import CheckAnalysisStatusUseCase


class TestCriticalProductionScenarios:
    """Tests for critical production-breaking scenarios"""
    
    def test_concurrent_analysis_triggering_race_condition(self, mock_sonarqube_service, analysis_repository, project_repository):
        """Test concurrent analysis triggering doesn't create duplicate analyses"""
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
        
        # Track created analyses
        created_analyses = []
        
        def mock_save(analysis):
            created_analyses.append(analysis.id)
            return analysis.id
        
        analysis_repository.save.side_effect = mock_save
        analysis_repository.find_by_commit.return_value = None  # Initially no existing analysis
        
        use_case = TriggerAnalysisUseCase(
            analysis_repository,
            project_repository,
            mock_sonarqube_service,
            Mock()
        )
        
        # Trigger multiple analyses concurrently
        commit_hash = "abc123def456789012345678901234567890abcd"
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(use_case.execute, "test-project", "main", commit_hash)
                for _ in range(20)
            ]
            
            results = [future.result() for future in as_completed(futures)]
        
        # Critical: Should only create one analysis for the same commit
        assert len(set(created_analyses)) == 1, f"Race condition detected: {len(set(created_analyses))} analyses created instead of 1"
        assert len(results) == 20
        assert all(result == created_analyses[0] for result in results)
    
    def test_memory_exhaustion_large_analysis(self, mock_sonarqube_service):
        """Test system handles large analyses without memory exhaustion"""
        service = AnalysisDomainService()
        
        # Create analysis with thousands of issues (simulating large codebase)
        issues = []
        for i in range(10000):  # 10,000 issues
            issue = Issue(
                key=f"ISSUE-{i}",
                type=IssueType.BUG if i % 3 == 0 else IssueType.CODE_SMELL,
                severity=Severity.MAJOR if i % 2 == 0 else Severity.MINOR,
                message=f"Test issue {i}",
                file_path=f"file_{i % 100}.py",
                line_number=i % 1000 + 1,
                rule=f"RULE_{i % 50}",
                status="OPEN"
            )
            issues.append(issue)
        
        metrics = [
            Metric(name="coverage", value=75.5, formatted_value="75.5%"),
            Metric(name="complexity", value=10000.0, formatted_value="10000"),
            Metric(name="duplicated_lines", value=5000.0, formatted_value="5000")
        ]
        
        large_analysis = Analysis(
            id="large-analysis",
            project_key="test-project",
            branch="main",
            commit_hash="abc123def456789012345678901234567890abcd",
            status=AnalysisStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            issues=issues,
            metrics=metrics
        )
        
        # Critical: Should handle large analysis without memory issues
        start_time = time.time()
        
        # Test operations that could cause memory issues
        score = service.calculate_quality_score(large_analysis)
        blocking_issues = [issue for issue in issues if issue.is_blocking()]
        security_issues = service.get_security_issues(large_analysis)
        summary = service.generate_analysis_summary(large_analysis)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Critical assertions
        assert score is not None
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
        assert processing_time < 5.0, f"Processing took too long: {processing_time}s"
        assert len(blocking_issues) == len([issue for issue in issues if issue.is_blocking()])
        assert len(security_issues) == len([issue for issue in issues if issue.is_security_related()])
        assert "Found" in summary and "issues" in summary
    
    def test_database_connection_timeout_handling(self):
        """Test system handles database timeouts gracefully"""
        from unittest.mock import Mock
        import psycopg2
        
        # Mock repository that simulates database timeout
        mock_repo = Mock()
        
        def mock_timeout(*args, **kwargs):
            # Simulate database timeout
            raise psycopg2.OperationalError("connection timeout")
        
        mock_repo.find_by_id.side_effect = mock_timeout
        mock_repo.save.side_effect = mock_timeout
        
        use_case = CheckAnalysisStatusUseCase(
            mock_repo,
            Mock(),
            Mock()
        )
        
        # Critical: Should handle timeout gracefully without crashing
        with pytest.raises(Exception):  # Should raise some exception, not crash
            use_case.execute("test-analysis")
    
    def test_external_service_failure_cascade(self, mock_sonarqube_service, analysis_repository, project_repository):
        """Test external service failures don't cascade to system failure"""
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
        
        # Simulate SonarQube service failure
        mock_sonarqube_service.trigger_analysis.side_effect = Exception("SonarQube service unavailable")
        
        use_case = TriggerAnalysisUseCase(
            analysis_repository,
            project_repository,
            mock_sonarqube_service,
            Mock()
        )
        
        # Critical: Should handle external service failure gracefully
        with pytest.raises(Exception) as exc_info:
            use_case.execute("test-project", "main", "abc123def456789012345678901234567890abcd")
        
        # Should not crash the entire system
        assert "SonarQube service unavailable" in str(exc_info.value)
    
    def test_data_corruption_handling(self):
        """Test system handles corrupted data gracefully"""
        service = AnalysisDomainService()
        
        # Test with corrupted analysis data
        corrupted_analysis = Analysis(
            id="corrupted-analysis",
            project_key="test-project",
            branch="main",
            commit_hash="abc123def456789012345678901234567890abcd",
            status=AnalysisStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            issues=[
                # Corrupted issue with negative line number
                Issue(
                    key="CORRUPTED-1",
                    type=IssueType.BUG,
                    severity=Severity.CRITICAL,
                    message="Corrupted issue",
                    file_path="test.py",
                    line_number=-1,  # Invalid
                    rule="CORRUPTED_RULE",
                    status="OPEN"
                )
            ],
            metrics=[
                # Corrupted metric with negative value
                Metric(
                    name="coverage",
                    value=-50.0,  # Invalid
                    formatted_value="-50.0%"
                )
            ]
        )
        
        # Critical: Should handle corrupted data without crashing
        try:
            score = service.calculate_quality_score(corrupted_analysis)
            # If it doesn't crash, that's good - just verify it returns something reasonable
            assert isinstance(score, (int, float))
        except Exception as e:
            # If it does raise an exception, it should be a meaningful one
            assert "corrupted" in str(e).lower() or "invalid" in str(e).lower()
    
    def test_resource_exhaustion_thread_safety(self):
        """Test thread safety under resource exhaustion"""
        service = AnalysisDomainService()
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                # Create analysis and perform operations
                analysis = Analysis(
                    id=f"analysis-{worker_id}",
                    project_key="test-project",
                    branch="main",
                    commit_hash=f"hash{worker_id:040}",
                    status=AnalysisStatus.COMPLETED,
                    created_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    issues=[
                        Issue(
                            key=f"ISSUE-{worker_id}",
                            type=IssueType.BUG,
                            severity=Severity.MAJOR,
                            message=f"Issue {worker_id}",
                            file_path="test.py",
                            line_number=worker_id,
                            rule="TEST_RULE",
                            status="OPEN"
                        )
                    ],
                    metrics=[
                        Metric(
                            name="coverage",
                            value=80.0 + worker_id % 20,
                            formatted_value=f"{80.0 + worker_id % 20}%"
                        )
                    ]
                )
                
                # Perform operations
                score = service.calculate_quality_score(analysis)
                blocking = service.should_block_merge(analysis)
                summary = service.generate_analysis_summary(analysis)
                
                results.append((worker_id, score, blocking, summary))
                
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Run multiple threads concurrently
        threads = []
        for i in range(100):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Critical: No thread safety violations should occur
        assert len(errors) == 0, f"Thread safety violations: {errors}"
        assert len(results) == 100
        
        # Verify all results are unique and valid
        worker_ids = [result[0] for result in results]
        assert len(set(worker_ids)) == 100, "Duplicate worker IDs detected"
    
    def test_cascading_failure_prevention(self, mock_sonarqube_service, analysis_repository, project_repository):
        """Test that failures don't cascade through the system"""
        # Setup multiple projects
        projects = []
        for i in range(5):
            project = Project(
                key=f"project-{i}",
                name=f"Project {i}",
                description=f"Test project {i}",
                status=ProjectStatus.ACTIVE,
                created_at=datetime.now(timezone.utc),
                last_analysis_at=None,
                quality_gate_status=QualityGateStatus.NONE,
                languages=["python"]
            )
            projects.append(project)
            project_repository.save(project)
        
        # Make SonarQube fail for specific project only
        def trigger_analysis_side_effect(project_key, branch, commit_hash):
            if project_key == "project-2":
                raise Exception("SonarQube failure for project-2")
            return f"task-{project_key}"
        
        mock_sonarqube_service.trigger_analysis.side_effect = trigger_analysis_side_effect
        
        use_case = TriggerAnalysisUseCase(
            analysis_repository,
            project_repository,
            mock_sonarqube_service,
            Mock()
        )
        
        # Try to trigger analyses for all projects
        results = {}
        for project in projects:
            try:
                analysis_id = use_case.execute(project.key, "main", "abc123def456789012345678901234567890abcd")
                results[project.key] = {"success": True, "analysis_id": analysis_id}
            except Exception as e:
                results[project.key] = {"success": False, "error": str(e)}
        
        # Critical: Only project-2 should fail, others should succeed
        assert results["project-0"]["success"] is True
        assert results["project-1"]["success"] is True
        assert results["project-2"]["success"] is False
        assert results["project-3"]["success"] is True
        assert results["project-4"]["success"] is True
    
    def test_infinite_loop_prevention(self):
        """Test that infinite loops are prevented in recursive operations"""
        service = AnalysisDomainService()
        
        # Create analysis with circular references (if possible)
        # This tests ensures that any recursive operations don't cause infinite loops
        analysis = Analysis(
            id="loop-test",
            project_key="test-project",
            branch="main",
            commit_hash="abc123def456789012345678901234567890abcd",
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
                Metric(
                    name="coverage",
                    value=85.0,
                    formatted_value="85.0%"
                )
            ]
        )
        
        # Test operations that could potentially cause infinite loops
        start_time = time.time()
        
        try:
            # Set a timeout to prevent infinite loops
            def timeout_handler():
                raise TimeoutError("Operation timed out - possible infinite loop")
            
            # Use a timer to prevent infinite loops
            timer = threading.Timer(10.0, timeout_handler)
            timer.start()
            
            # Perform potentially recursive operations
            score = service.calculate_quality_score(analysis)
            summary = service.generate_analysis_summary(analysis)
            
            timer.cancel()
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Critical: Should complete within reasonable time
            assert processing_time < 5.0, f"Operation took too long: {processing_time}s"
            assert score is not None
            assert summary is not None
            
        except TimeoutError:
            pytest.fail("Infinite loop detected - operation timed out")
    
    def test_malformed_input_handling(self):
        """Test handling of malformed and malicious input"""
        service = AnalysisDomainService()
        
        # Test with various malformed inputs
        malformed_cases = [
            # None values
            None,
            # Empty strings
            "",
            # Very long strings
            "x" * 10000,
            # Special characters
            "!@#$%^&*()_+{}|:<>?[]\\;'\",./",
            # Unicode characters
            "测试🚀💻🔥",
            # SQL injection attempts
            "'; DROP TABLE analyses; --",
            # XSS attempts
            "<script>alert('xss')</script>",
            # JSON injection
            '{"key":"value","injected":true}',
        ]
        
        for malformed_input in malformed_cases:
            # Test that malformed inputs don't crash the system
            try:
                # Create analysis with potentially malformed data
                analysis = Analysis(
                    id="test-analysis" if malformed_input is None else str(malformed_input)[:100],
                    project_key="test-project",
                    branch="main",
                    commit_hash="abc123def456789012345678901234567890abcd",
                    status=AnalysisStatus.COMPLETED,
                    created_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    issues=[],
                    metrics=[]
                )
                
                # Perform operations
                score = service.calculate_quality_score(analysis)
                summary = service.generate_analysis_summary(analysis)
                
                # Should not crash and should return reasonable values
                assert score is not None
                assert isinstance(score, (int, float))
                
            except Exception as e:
                # If it does raise an exception, it should be a validation error, not a crash
                assert any(keyword in str(e).lower() for keyword in ["invalid", "malformed", "validation", "input"])
    
    def test_memory_leak_detection(self):
        """Test for memory leaks in long-running operations"""
        import gc
        import psutil
        import os
        
        service = AnalysisDomainService()
        process = psutil.Process(os.getpid())
        
        # Get initial memory usage
        initial_memory = process.memory_info().rss
        
        # Perform many operations to detect memory leaks
        for i in range(1000):
            analysis = Analysis(
                id=f"test-analysis-{i}",
                project_key="test-project",
                branch="main",
                commit_hash=f"hash{i:040}",
                status=AnalysisStatus.COMPLETED,
                created_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                issues=[
                    Issue(
                        key=f"ISSUE-{i}",
                        type=IssueType.BUG,
                        severity=Severity.MAJOR,
                        message=f"Issue {i}",
                        file_path="test.py",
                        line_number=i % 100 + 1,
                        rule="TEST_RULE",
                        status="OPEN"
                    )
                ],
                    metrics=[
                        Metric(
                            name="coverage",
                            value=80.0 + i % 20,
                            formatted_value=f"{80.0 + i % 20}%"
                        )
                    ]
                )
            
            # Perform operations
            score = service.calculate_quality_score(analysis)
            summary = service.generate_analysis_summary(analysis)
            
            # Force garbage collection periodically
            if i % 100 == 0:
                gc.collect()
        
        # Final garbage collection
        gc.collect()
        
        # Get final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Critical: Memory increase should be reasonable (less than 50MB)
        max_allowed_increase = 50 * 1024 * 1024  # 50MB
        assert memory_increase < max_allowed_increase, f"Memory leak detected: {memory_increase / 1024 / 1024:.2f}MB increase"
    
    def test_concurrent_resource_contention(self):
        """Test handling of concurrent resource contention"""
        service = AnalysisDomainService()
        shared_resource = {"count": 0, "lock": threading.Lock()}
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                # Simulate resource contention
                for i in range(10):
                    with shared_resource["lock"]:
                        shared_resource["count"] += 1
                        current_count = shared_resource["count"]
                    
                    # Create analysis and perform operations
                    analysis = Analysis(
                        id=f"analysis-{worker_id}-{i}",
                        project_key="test-project",
                        branch="main",
                        commit_hash=f"hash{current_count:040}",
                        status=AnalysisStatus.COMPLETED,
                        created_at=datetime.now(timezone.utc),
                        completed_at=datetime.now(timezone.utc),
                        issues=[
                            Issue(
                                key=f"ISSUE-{worker_id}-{i}",
                                type=IssueType.BUG,
                                severity=Severity.MAJOR,
                                message=f"Issue {worker_id}-{i}",
                                file_path="test.py",
                                line_number=current_count,
                                rule="TEST_RULE",
                                status="OPEN"
                            )
                        ],
                        metrics=[
                            Metric(
                                name="coverage",
                                value=80.0,
                                formatted_value="80.0%"
                            )
                        ]
                    )
                    
                    # Perform operations
                    score = service.calculate_quality_score(analysis)
                    results.append((worker_id, i, score))
                    
                    # Small delay to increase contention
                    time.sleep(0.001)
                    
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Run multiple threads concurrently
        threads = []
        for i in range(20):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Critical: No resource contention issues should occur
        assert len(errors) == 0, f"Resource contention issues: {errors}"
        assert len(results) == 200  # 20 workers * 10 operations each
        assert shared_resource["count"] == 200

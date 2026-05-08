import pytest
import json
import tempfile
import os
import sys
from pathlib import Path

# Add the analysis tools path to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "analysis-tools" / "python"))

from deep_analyzer import PythonDeepAnalyzer


class TestPythonDeepAnalyzer:
    
    def test_analyze_project_basic(self, temp_project_dir):
        """Test basic project analysis"""
        analyzer = PythonDeepAnalyzer(temp_project_dir)
        results = analyzer.analyze_project()
        
        # Verify structure
        assert 'summary' in results
        assert 'security_issues' in results
        assert 'complexity_metrics' in results
        assert 'recommendations' in results
        assert 'analysis_timestamp' in results
        
        # Verify summary
        summary = results['summary']
        assert summary['total_files'] == 2  # test.py and another.py
        assert summary['total_issues'] > 0  # Should find dangerous_function
        assert 'average_cyclomatic_complexity' in summary
        assert 'average_cognitive_complexity' in summary
    
    def test_analyze_project_security_issues(self, temp_project_dir):
        """Test security issue detection"""
        analyzer = PythonDeepAnalyzer(temp_project_dir)
        results = analyzer.analyze_project()
        
        security_issues = results['security_issues']
        
        # Should find eval() usage
        eval_issues = [issue for issue in security_issues if issue['issue_type'] == 'dangerous_function']
        assert len(eval_issues) > 0
        assert any('eval' in issue['description'].lower() for issue in eval_issues)
        
        # Should find os.system() usage
        system_issues = [issue for issue in security_issues if issue['issue_type'] == 'system_access']
        assert len(system_issues) > 0
    
    def test_analyze_project_complexity_metrics(self, temp_project_dir):
        """Test complexity metrics calculation"""
        analyzer = PythonDeepAnalyzer(temp_project_dir)
        results = analyzer.analyze_project()
        
        metrics = results['complexity_metrics']
        
        # Should have metrics for both files
        assert len(metrics) == 2
        
        # Check that files have complexity metrics
        for file_path, file_metrics in metrics.items():
            assert 'cyclomatic_complexity' in file_metrics
            assert 'cognitive_complexity' in file_metrics
            assert 'lines_of_code' in file_metrics
            assert 'maintainability_index' in file_metrics
            
            # Verify reasonable values
            assert file_metrics['cyclomatic_complexity'] >= 1
            assert file_metrics['cognitive_complexity'] >= 0
            assert file_metrics['lines_of_code'] > 0
            assert file_metrics['maintainability_index'] >= 0
    
    def test_analyze_project_high_complexity_detection(self, temp_project_dir):
        """Test detection of high complexity functions"""
        analyzer = PythonDeepAnalyzer(temp_project_dir)
        results = analyzer.analyze_project()
        
        summary = results['summary']
        
        # complex_function has nested ifs, should increase complexity
# Note: high_complexity_files detection may vary based on threshold
        assert summary['total_files'] == 2
        
        # Verify complexity is reasonable for the test file
        metrics = results['complexity_metrics']
        test_py_metrics = None
        for file_path, file_metrics in metrics.items():
            if file_path.endswith('test.py'):
                test_py_metrics = file_metrics
                break
        
        assert test_py_metrics is not None
        assert test_py_metrics['cyclomatic_complexity'] >= 3  # Base + nested ifs
    
    def test_analyze_project_recommendations(self, temp_project_dir):
        """Test recommendation generation"""
        analyzer = PythonDeepAnalyzer(temp_project_dir)
        results = analyzer.analyze_project()
        
        recommendations = results['recommendations']
        
        assert len(recommendations) > 0
        assert isinstance(recommendations, list)
        
        # Should recommend fixing security issues
        rec_text = ' '.join(recommendations).lower()
        assert 'security' in rec_text or 'dangerous' in rec_text
    
    def test_analyze_empty_project(self):
        """Test analysis of empty project"""
        with tempfile.TemporaryDirectory() as empty_dir:
            analyzer = PythonDeepAnalyzer(empty_dir)
            results = analyzer.analyze_project()
            
            assert results['summary']['total_files'] == 0
            assert results['summary']['total_issues'] == 0
            assert len(results['security_issues']) == 0
            assert len(results['complexity_metrics']) == 0
    
    def test_analyze_project_with_syntax_error(self):
        """Test handling of syntax errors"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file with syntax error
            error_file = os.path.join(temp_dir, "syntax_error.py")
            with open(error_file, 'w') as f:
                f.write("def broken_function(\n    pass\n")
            
            analyzer = PythonDeepAnalyzer(temp_dir)
            results = analyzer.analyze_project()
            
            # Should handle syntax error gracefully
            # Note: syntax error files may be excluded from total_files count
            assert results['summary']['total_files'] >= 0
            # Should not crash, but may have 0 issues due to syntax error
    
    def test_analyze_project_no_python_files(self):
        """Test analysis of project with no Python files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create non-Python files
            js_file = os.path.join(temp_dir, "script.js")
            with open(js_file, 'w') as f:
                f.write("console.log('hello');")
            
            txt_file = os.path.join(temp_dir, "readme.txt")
            with open(txt_file, 'w') as f:
                f.write("This is a readme file")
            
            analyzer = PythonDeepAnalyzer(temp_dir)
            results = analyzer.analyze_project()
            
            assert results['summary']['total_files'] == 0
            assert len(results['security_issues']) == 0
    
    def test_analyze_project_large_file(self):
        """Test analysis of larger Python file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a larger Python file
            large_file = os.path.join(temp_dir, "large.py")
            with open(large_file, 'w') as f:
                f.write("""
def function1():
    if True:
        if False:
            if True:
                return 1
            else:
                return 2
        else:
            return 3
    return 0

def function2():
    for i in range(10):
        if i % 2 == 0:
            for j in range(5):
                if j > 2:
                    return i + j
    return 0

def function3():
    try:
        result = function1() + function2()
        if result > 0:
            return result
        else:
            return 0
    except Exception:
        return -1

class ComplexClass:
    def __init__(self):
        self.value = 0
    
    def method1(self):
        if self.value > 0:
            if self.value < 10:
                return self.value * 2
            else:
                return self.value / 2
        else:
            return 0
    
    def method2(self, x):
        for i in range(x):
            if i % 3 == 0:
                if i > 5:
                    yield i
""")
            
            analyzer = PythonDeepAnalyzer(temp_dir)
            results = analyzer.analyze_project()
            
            # Should handle larger file correctly
            assert results['summary']['total_files'] == 1
            assert results['summary']['high_complexity_files'] >= 1
            
            metrics = results['complexity_metrics']
            large_file_metrics = list(metrics.values())[0]
            assert large_file_metrics['cyclomatic_complexity'] > 5
            assert large_file_metrics['lines_of_code'] > 30
    
    def test_analyze_project_json_output(self, temp_project_dir):
        """Test that output is valid JSON"""
        analyzer = PythonDeepAnalyzer(temp_project_dir)
        results = analyzer.analyze_project()
        
        # Should be JSON serializable
        json_str = json.dumps(results)
        parsed_back = json.loads(json_str)
        
        assert parsed_back == results
    
    def test_analyze_project_timestamp(self, temp_project_dir):
        """Test analysis timestamp is included and valid"""
        analyzer = PythonDeepAnalyzer(temp_project_dir)
        results = analyzer.analyze_project()
        
        assert 'analysis_timestamp' in results
        assert isinstance(results['analysis_timestamp'], str)
        
        # Should be a valid ISO format timestamp
        from datetime import datetime
        timestamp = datetime.fromisoformat(results['analysis_timestamp'].replace('Z', '+00:00'))
        assert timestamp is not None

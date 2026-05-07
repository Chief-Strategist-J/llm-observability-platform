#!/usr/bin/env python3

import ast
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ComplexityMetrics:
    cyclomatic_complexity: int
    cognitive_complexity: int
    lines_of_code: int
    maintainability_index: float


@dataclass
class SecurityIssue:
    file_path: str
    line_number: int
    issue_type: str
    severity: str
    description: str
    rule: str


class PythonDeepAnalyzer:
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.issues: List[SecurityIssue] = []
        self.metrics: Dict[str, ComplexityMetrics] = {}

    def analyze_project(self) -> Dict[str, Any]:
        """Perform deep analysis of Python project"""
        print(f"🔍 Starting deep analysis of {self.root_path}")
        
        python_files = self._find_python_files()
        print(f"📁 Found {len(python_files)} Python files")
        
        for file_path in python_files:
            self._analyze_file(file_path)
        
        return {
            'summary': self._generate_summary(),
            'security_issues': [self._issue_to_dict(issue) for issue in self.issues],
            'complexity_metrics': {k: self._metrics_to_dict(v) for k, v in self.metrics.items()},
            'recommendations': self._generate_recommendations(),
            'analysis_timestamp': datetime.now().isoformat()
        }

    def _find_python_files(self) -> List[Path]:
        """Find all Python files in the project"""
        python_files = []
        for root, dirs, files in os.walk(self.root_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        return python_files

    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Calculate complexity metrics
            complexity = self._calculate_complexity(tree, content)
            self.metrics[str(file_path.relative_to(self.root_path))] = complexity
            
            # Check for security issues
            self._check_security_issues(tree, file_path, content)
            
        except SyntaxError as e:
            print(f"⚠️  Syntax error in {file_path}: {e}")
        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}")

    def _calculate_complexity(self, tree: ast.AST, content: str) -> ComplexityMetrics:
        """Calculate various complexity metrics"""
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        
        lines_of_code = len([line for line in content.split('\n') if line.strip()])
        
        # Simplified maintainability index calculation
        maintainability_index = max(0, 171 - 5.2 * visitor.log_volume - 0.23 * visitor.cyclomatic_complexity - 16.2 * visitor.log_lines)
        
        return ComplexityMetrics(
            cyclomatic_complexity=visitor.cyclomatic_complexity,
            cognitive_complexity=visitor.cognitive_complexity,
            lines_of_code=lines_of_code,
            maintainability_index=maintainability_index
        )

    def _check_security_issues(self, tree: ast.AST, file_path: Path, content: str) -> None:
        """Check for common security issues in Python code"""
        visitor = SecurityVisitor(str(file_path.relative_to(self.root_path)), content)
        visitor.visit(tree)
        self.issues.extend(visitor.issues)

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate analysis summary"""
        if not self.metrics:
            return {'total_files': 0, 'total_issues': 0}
        
        total_files = len(self.metrics)
        total_issues = len(self.issues)
        
        avg_complexity = sum(m.cyclomatic_complexity for m in self.metrics.values()) / total_files
        avg_cognitive = sum(m.cognitive_complexity for m in self.metrics.values()) / total_files
        avg_maintainability = sum(m.maintainability_index for m in self.metrics.values()) / total_files
        
        severity_counts = {}
        for issue in self.issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        return {
            'total_files': total_files,
            'total_issues': total_issues,
            'average_cyclomatic_complexity': round(avg_complexity, 2),
            'average_cognitive_complexity': round(avg_cognitive, 2),
            'average_maintainability_index': round(avg_maintainability, 2),
            'severity_breakdown': severity_counts,
            'high_complexity_files': len([m for m in self.metrics.values() if m.cyclomatic_complexity > 10]),
            'low_maintainability_files': len([m for m in self.metrics.values() if m.maintainability_index < 65])
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if self.issues:
            critical_issues = [i for i in self.issues if i.severity == 'critical']
            if critical_issues:
                recommendations.append(f"URGENT: Fix {len(critical_issues)} critical security issues")
        
        if self.metrics:
            high_complexity = [k for k, v in self.metrics.items() if v.cyclomatic_complexity > 15]
            if high_complexity:
                recommendations.append(f"Refactor {len(high_complexity)} files with high cyclomatic complexity (>15)")
            
            low_maintainability = [k for k, v in self.metrics.items() if v.maintainability_index < 65]
            if low_maintainability:
                recommendations.append(f"Improve maintainability of {len(low_maintainability)} files (index < 65)")
        
        if not recommendations:
            recommendations.append("Excellent code quality! Continue maintaining current standards.")
        
        return recommendations

    def _issue_to_dict(self, issue: SecurityIssue) -> Dict[str, Any]:
        """Convert SecurityIssue to dictionary"""
        return {
            'file_path': issue.file_path,
            'line_number': issue.line_number,
            'issue_type': issue.issue_type,
            'severity': issue.severity,
            'description': issue.description,
            'rule': issue.rule
        }

    def _metrics_to_dict(self, metrics: ComplexityMetrics) -> Dict[str, Any]:
        """Convert ComplexityMetrics to dictionary"""
        return {
            'cyclomatic_complexity': metrics.cyclomatic_complexity,
            'cognitive_complexity': metrics.cognitive_complexity,
            'lines_of_code': metrics.lines_of_code,
            'maintainability_index': round(metrics.maintainability, 2)
        }


class ComplexityVisitor(ast.NodeVisitor):
    
    def __init__(self):
        self.cyclomatic_complexity = 1  # Base complexity
        self.cognitive_complexity = 0
        self.log_volume = 0
        self.log_lines = 0
        self.nesting_level = 0

    def visit_FunctionDef(self, node):
        self.cyclomatic_complexity += 1
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_If(self, node):
        self.cyclomatic_complexity += 1
        self.cognitive_complexity += 1 + self.nesting_level
        self.generic_visit(node)

    def visit_For(self, node):
        self.cyclomatic_complexity += 1
        self.cognitive_complexity += 1 + self.nesting_level
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1

    def visit_While(self, node):
        self.cyclomatic_complexity += 1
        self.cognitive_complexity += 1 + self.nesting_level
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1

    def visit_ExceptHandler(self, node):
        self.cyclomatic_complexity += 1
        self.cognitive_complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        self.cyclomatic_complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.cyclomatic_complexity += len(node.values) - 1
        self.generic_visit(node)


class SecurityVisitor(ast.NodeVisitor):
    
    def __init__(self, file_path: str, content: str):
        self.file_path = file_path
        self.content = content
        self.issues: List[SecurityIssue] = []
        self.lines = content.split('\n')

    def visit_Call(self, node):
        # Check for dangerous function calls
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            
            if func_name in ['eval', 'exec', 'compile']:
                self._add_issue(node, 'dangerous_function', 'critical', 
                              f"Use of dangerous function '{func_name}' can lead to code injection")
            elif func_name == 'input' and len(node.args) == 0:
                self._add_issue(node, 'unsafe_input', 'medium',
                              'Unvalidated input() can be dangerous')
        
        # Check for shell command execution
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in ['system', 'popen', 'call', 'check_output']:
                if isinstance(node.func.value, ast.Name) and node.func.value.id == 'os':
                    self._add_issue(node, 'shell_injection', 'high',
                                  'Potential shell injection vulnerability')
        
        self.generic_visit(node)

    def visit_Import(self, node):
        # Check for dangerous imports
        for alias in node.names:
            if alias.name in ['pickle', 'cPickle']:
                self._add_issue(node, 'unsafe_deserialization', 'medium',
                              f"Unsafe deserialization with '{alias.name}'")
            elif alias.name in ['subprocess', 'os']:
                self._add_issue(node, 'system_access', 'low',
                              f"System access module '{alias.name}' imported")
        
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.visit_Import(node)

    def _add_issue(self, node: ast.AST, issue_type: str, severity: str, description: str):
        """Add a security issue to the list"""
        issue = SecurityIssue(
            file_path=self.file_path,
            line_number=getattr(node, 'lineno', 0),
            issue_type=issue_type,
            severity=severity,
            description=description,
            rule=f"PYTHON_{issue_type.upper()}"
        )
        self.issues.append(issue)


def main():
    if len(sys.argv) != 2:
        print("Usage: python deep_analyzer.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    analyzer = PythonDeepAnalyzer(project_path)
    results = analyzer.analyze_project()
    
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

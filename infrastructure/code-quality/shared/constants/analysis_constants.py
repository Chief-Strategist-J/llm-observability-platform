from enum import Enum


class AnalysisConstants:
    
    DEFAULT_TIMEOUT_SECONDS = 3600
    
    MAX_RETRY_ATTEMPTS = 3
    
    RETRY_DELAY_SECONDS = 30
    
    MINIMUM_COVERAGE_THRESHOLD = 80.0
    
    QUALITY_SCORE_WEIGHTS = {
        'BLOCKER': 10.0,
        'CRITICAL': 5.0,
        'MAJOR': 2.0,
        'MINOR': 0.5,
        'INFO': 0.1
    }
    
    COVERAGE_BONUS_MULTIPLIER = 5.0
    
    SUPPORTED_LANGUAGES = [
        'python',
        'java',
        'javascript',
        'typescript',
        'go',
        'rust',
        'c++',
        'c',
        'c#',
        'php',
        'ruby',
        'scala',
        'kotlin'
    ]
    
    DEFAULT_METRICS = [
        'coverage',
        'duplicated_lines_density',
        'maintainability_rating',
        'reliability_rating',
        'security_rating',
        'sqale_index',
        'ncloc',
        'complexity'
    ]
    
    QUALITY_GATE_CONDITIONS = {
        'coverage': '>= 80',
        'duplicated_lines_density': '<= 3',
        'new_coverage': '>= 80',
        'new_duplicated_lines_density': '<= 3'
    }


class AnalysisStatusConstants:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SeverityConstants:
    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


class IssueTypeConstants:
    BUG = "bug"
    VULNERABILITY = "vulnerability"
    CODE_SMELL = "code_smell"
    SECURITY_HOTSPOT = "security_hotspot"

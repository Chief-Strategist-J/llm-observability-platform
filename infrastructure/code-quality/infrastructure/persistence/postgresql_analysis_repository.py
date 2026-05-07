import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional
from datetime import datetime

from domain.models.analysis import Analysis, AnalysisStatus, Issue, Metric, IssueType, Severity
from domain.ports.analysis_repository import AnalysisRepository
from shared.utils.date_utils import DateUtils


class PostgreSQLAnalysisRepository(AnalysisRepository):
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def _get_connection(self):
        return psycopg2.connect(self.connection_string)

    def _map_row_to_analysis(self, row: dict) -> Analysis:
        return Analysis(
            id=row['id'],
            project_key=row['project_key'],
            branch=row['branch'],
            commit_hash=row['commit_hash'],
            status=AnalysisStatus(row['status']),
            created_at=row['created_at'],
            completed_at=row['completed_at'],
            issues=self._get_analysis_issues(row['id']),
            metrics=self._get_analysis_metrics(row['id'])
        )

    def _get_analysis_issues(self, analysis_id: str) -> List[Issue]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT key, type, severity, message, file_path, line_number, rule, status
                    FROM analysis_issues
                    WHERE analysis_id = %s
                """, (analysis_id,))
                
                issues = []
                for row in cursor.fetchall():
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
                        key=row['key'],
                        type=issue_type_mapping.get(row['type'], IssueType.CODE_SMELL),
                        severity=severity_mapping.get(row['severity'], Severity.MAJOR),
                        message=row['message'],
                        file_path=row['file_path'],
                        line_number=row['line_number'],
                        rule=row['rule'],
                        status=row['status']
                    )
                    issues.append(issue)
                
                return issues

    def _get_analysis_metrics(self, analysis_id: str) -> List[Metric]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT name, value, formatted_value
                    FROM analysis_metrics
                    WHERE analysis_id = %s
                """, (analysis_id,))
                
                metrics = []
                for row in cursor.fetchall():
                    metric = Metric(
                        name=row['name'],
                        value=float(row['value']),
                        formatted_value=row['formatted_value']
                    )
                    metrics.append(metric)
                
                return metrics

    def save(self, analysis: Analysis) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO analyses (id, project_key, branch, commit_hash, status, created_at, completed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        project_key = EXCLUDED.project_key,
                        branch = EXCLUDED.branch,
                        commit_hash = EXCLUDED.commit_hash,
                        status = EXCLUDED.status,
                        completed_at = EXCLUDED.completed_at
                """, (
                    analysis.id,
                    analysis.project_key,
                    analysis.branch,
                    analysis.commit_hash,
                    analysis.status.value,
                    analysis.created_at,
                    analysis.completed_at
                ))
                
                self._save_issues(cursor, analysis.id, analysis.issues)
                self._save_metrics(cursor, analysis.id, analysis.metrics)
                
                conn.commit()

    def _save_issues(self, cursor, analysis_id: str, issues: List[Issue]) -> None:
        cursor.execute("DELETE FROM analysis_issues WHERE analysis_id = %s", (analysis_id,))
        
        for issue in issues:
            cursor.execute("""
                INSERT INTO analysis_issues (analysis_id, key, type, severity, message, file_path, line_number, rule, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                analysis_id,
                issue.key,
                issue.type.value,
                issue.severity.value,
                issue.message,
                issue.file_path,
                issue.line_number,
                issue.rule,
                issue.status
            ))

    def _save_metrics(self, cursor, analysis_id: str, metrics: List[Metric]) -> None:
        cursor.execute("DELETE FROM analysis_metrics WHERE analysis_id = %s", (analysis_id,))
        
        for metric in metrics:
            cursor.execute("""
                INSERT INTO analysis_metrics (analysis_id, name, value, formatted_value)
                VALUES (%s, %s, %s, %s)
            """, (
                analysis_id,
                metric.name,
                metric.value,
                metric.formatted_value
            ))

    def find_by_id(self, analysis_id: str) -> Optional[Analysis]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, project_key, branch, commit_hash, status, created_at, completed_at
                    FROM analyses
                    WHERE id = %s
                """, (analysis_id,))
                
                row = cursor.fetchone()
                if row:
                    return self._map_row_to_analysis(row)
                return None

    def find_by_project(self, project_key: str) -> List[Analysis]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, project_key, branch, commit_hash, status, created_at, completed_at
                    FROM analyses
                    WHERE project_key = %s
                    ORDER BY created_at DESC
                """, (project_key,))
                
                return [self._map_row_to_analysis(row) for row in cursor.fetchall()]

    def find_by_branch(self, project_key: str, branch: str) -> List[Analysis]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, project_key, branch, commit_hash, status, created_at, completed_at
                    FROM analyses
                    WHERE project_key = %s AND branch = %s
                    ORDER BY created_at DESC
                """, (project_key, branch))
                
                return [self._map_row_to_analysis(row) for row in cursor.fetchall()]

    def find_by_commit(self, project_key: str, commit_hash: str) -> Optional[Analysis]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, project_key, branch, commit_hash, status, created_at, completed_at
                    FROM analyses
                    WHERE project_key = %s AND commit_hash = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (project_key, commit_hash))
                
                row = cursor.fetchone()
                if row:
                    return self._map_row_to_analysis(row)
                return None

    def find_by_status(self, status: AnalysisStatus) -> List[Analysis]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, project_key, branch, commit_hash, status, created_at, completed_at
                    FROM analyses
                    WHERE status = %s
                    ORDER BY created_at DESC
                """, (status.value,))
                
                return [self._map_row_to_analysis(row) for row in cursor.fetchall()]

    def find_latest_by_project(self, project_key: str) -> Optional[Analysis]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, project_key, branch, commit_hash, status, created_at, completed_at
                    FROM analyses
                    WHERE project_key = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (project_key,))
                
                row = cursor.fetchone()
                if row:
                    return self._map_row_to_analysis(row)
                return None

    def update_status(self, analysis_id: str, status: AnalysisStatus) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                if status == AnalysisStatus.COMPLETED:
                    cursor.execute("""
                        UPDATE analyses
                        SET status = %s, completed_at = %s
                        WHERE id = %s
                    """, (status.value, DateUtils.utc_now(), analysis_id))
                else:
                    cursor.execute("""
                        UPDATE analyses
                        SET status = %s
                        WHERE id = %s
                    """, (status.value, analysis_id))
                
                conn.commit()

    def delete(self, analysis_id: str) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM analysis_issues WHERE analysis_id = %s", (analysis_id,))
                cursor.execute("DELETE FROM analysis_metrics WHERE analysis_id = %s", (analysis_id,))
                cursor.execute("DELETE FROM analyses WHERE id = %s", (analysis_id,))
                conn.commit()

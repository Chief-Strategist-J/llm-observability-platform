import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional
from datetime import datetime

from domain.models.project import Project, ProjectStatus, QualityGate, QualityGateStatus
from domain.ports.project_repository import ProjectRepository, QualityGateRepository


class PostgreSQLProjectRepository(ProjectRepository):
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def _get_connection(self):
        return psycopg2.connect(self.connection_string)

    def _map_row_to_project(self, row: dict) -> Project:
        return Project(
            key=row['key'],
            name=row['name'],
            description=row['description'],
            status=ProjectStatus(row['status']),
            created_at=row['created_at'],
            last_analysis_at=row['last_analysis_at'],
            quality_gate_status=QualityGateStatus(row['quality_gate_status']),
            languages=row['languages'].split(',') if row['languages'] else []
        )

    def save(self, project: Project) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO projects (key, name, description, status, created_at, last_analysis_at, quality_gate_status, languages)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (key) DO UPDATE SET
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        status = EXCLUDED.status,
                        last_analysis_at = EXCLUDED.last_analysis_at,
                        quality_gate_status = EXCLUDED.quality_gate_status,
                        languages = EXCLUDED.languages
                """, (
                    project.key,
                    project.name,
                    project.description,
                    project.status.value,
                    project.created_at,
                    project.last_analysis_at,
                    project.quality_gate_status.value,
                    ','.join(project.languages)
                ))
                conn.commit()

    def find_by_key(self, project_key: str) -> Optional[Project]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT key, name, description, status, created_at, last_analysis_at, quality_gate_status, languages
                    FROM projects
                    WHERE key = %s
                """, (project_key,))
                
                row = cursor.fetchone()
                if row:
                    return self._map_row_to_project(row)
                return None

    def find_by_name(self, name: str) -> Optional[Project]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT key, name, description, status, created_at, last_analysis_at, quality_gate_status, languages
                    FROM projects
                    WHERE name = %s
                """, (name,))
                
                row = cursor.fetchone()
                if row:
                    return self._map_row_to_project(row)
                return None

    def find_by_status(self, status: ProjectStatus) -> List[Project]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT key, name, description, status, created_at, last_analysis_at, quality_gate_status, languages
                    FROM projects
                    WHERE status = %s
                    ORDER BY name
                """, (status.value,))
                
                return [self._map_row_to_project(row) for row in cursor.fetchall()]

    def find_all(self) -> List[Project]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT key, name, description, status, created_at, last_analysis_at, quality_gate_status, languages
                    FROM projects
                    ORDER BY name
                """)
                
                return [self._map_row_to_project(row) for row in cursor.fetchall()]

    def find_by_language(self, language: str) -> List[Project]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT key, name, description, status, created_at, last_analysis_at, quality_gate_status, languages
                    FROM projects
                    WHERE %s = ANY(string_to_array(languages, ','))
                    ORDER BY name
                """, (language.lower(),))
                
                return [self._map_row_to_project(row) for row in cursor.fetchall()]

    def update_status(self, project_key: str, status: ProjectStatus) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE projects
                    SET status = %s
                    WHERE key = %s
                """, (status.value, project_key))
                conn.commit()

    def delete(self, project_key: str) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM projects WHERE key = %s", (project_key,))
                conn.commit()


class PostgreSQLQualityGateRepository(QualityGateRepository):
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def _get_connection(self):
        return psycopg2.connect(self.connection_string)

    def _map_row_to_quality_gate(self, row: dict) -> QualityGate:
        return QualityGate(
            id=row['id'],
            name=row['name'],
            project_key=row['project_key'],
            status=QualityGateStatus(row['status']),
            conditions=row['conditions'].split('|') if row['conditions'] else []
        )

    def save(self, quality_gate: QualityGate) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO quality_gates (id, name, project_key, status, conditions)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        project_key = EXCLUDED.project_key,
                        status = EXCLUDED.status,
                        conditions = EXCLUDED.conditions
                """, (
                    quality_gate.id,
                    quality_gate.name,
                    quality_gate.project_key,
                    quality_gate.status.value,
                    '|'.join(quality_gate.conditions)
                ))
                conn.commit()

    def find_by_id(self, gate_id: str) -> Optional[QualityGate]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, name, project_key, status, conditions
                    FROM quality_gates
                    WHERE id = %s
                """, (gate_id,))
                
                row = cursor.fetchone()
                if row:
                    return self._map_row_to_quality_gate(row)
                return None

    def find_by_project(self, project_key: str) -> List[QualityGate]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, name, project_key, status, conditions
                    FROM quality_gates
                    WHERE project_key = %s
                    ORDER BY name
                """, (project_key,))
                
                return [self._map_row_to_quality_gate(row) for row in cursor.fetchall()]

    def find_all(self) -> List[QualityGate]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, name, project_key, status, conditions
                    FROM quality_gates
                    ORDER BY name
                """)
                
                return [self._map_row_to_quality_gate(row) for row in cursor.fetchall()]

    def delete(self, gate_id: str) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM quality_gates WHERE id = %s", (gate_id,))
                conn.commit()

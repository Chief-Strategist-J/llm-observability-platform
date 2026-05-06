import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2.extensions import connection as Connection
from pydantic import BaseModel, Field, ConfigDict

project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.observability.scripts.observability_client import ObservabilityClient


class PostgreSQLConnectionConfig(BaseModel):
    model_config = ConfigDict(extra='allow')
    host: str = "172.29.0.10"
    port: int = 5432
    database: str = "scaibu_default"
    username: str = "postgres"
    password: str = "PostgresPassword123!"
    connection_timeout: int = 30
    application_name: str = "llm-observability-platform"


class PostgreSQLQueryResult(BaseModel):
    records: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float
    success: bool
    error_message: Optional[str] = None
    query_plan: Optional[Dict[str, Any]] = None


obs = ObservabilityClient(service_name="postgres-client")


def get_connection(config: Optional[PostgreSQLConnectionConfig] = None) -> Connection:
    if config is None:
        config = PostgreSQLConnectionConfig()
    
    obs.log_info("Initializing PostgreSQL connection", {
        "host": config.host,
        "port": config.port,
        "database": config.database
    })
    
    try:
        conn = psycopg2.connect(
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.username,
            password=config.password,
            connect_timeout=config.connection_timeout,
            application_name=config.application_name
        )
        
        conn.autocommit = False
        obs.log_info("PostgreSQL connection established successfully")
        return conn
    
    except Exception as e:
        obs.log_error(f"Failed to establish PostgreSQL connection: {e}")
        raise


def execute_query(
    connection: Connection,
    query: str,
    parameters: Optional[Union[Dict[str, Any], List[Any]]] = None,
    fetch_all: bool = True
) -> PostgreSQLQueryResult:
    start_time = datetime.now()
    
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            if parameters:
                if isinstance(parameters, dict):
                    cursor.execute(query, parameters)
                else:
                    cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            
            if fetch_all:
                records = [dict(record) for record in cursor.fetchall()]
            else:
                record = cursor.fetchone()
                records = [dict(record)] if record else []
            
            row_count = cursor.rowcount
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            obs.log_info(f"Query executed successfully", {
                "execution_time_ms": execution_time_ms,
                "row_count": row_count,
                "fetch_all": fetch_all
            })
            
            return PostgreSQLQueryResult(
                records=records,
                row_count=row_count,
                execution_time_ms=execution_time_ms,
                success=True
            )
    
    except Exception as e:
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        obs.log_error(f"Query execution failed: {e}")
        
        return PostgreSQLQueryResult(
            records=[],
            row_count=0,
            execution_time_ms=execution_time_ms,
            success=False,
            error_message=str(e)
        )


def execute_query_with_plan(
    connection: Connection,
    query: str,
    parameters: Optional[Union[Dict[str, Any], List[Any]]] = None,
    analyze: bool = False
) -> PostgreSQLQueryResult:
    start_time = datetime.now()
    
    try:
        explain_query = f"EXPLAIN {'ANALYZE' if analyze else ''} {query}"
        
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            if parameters:
                if isinstance(parameters, dict):
                    cursor.execute(explain_query, parameters)
                else:
                    cursor.execute(explain_query, parameters)
            else:
                cursor.execute(explain_query)
            
            plan_records = [dict(record) for record in cursor.fetchall()]
            
            query_plan = _parse_query_plan(plan_records)
            
            cursor.execute(query, parameters or [])
            records = [dict(record) for record in cursor.fetchall()]
            row_count = cursor.rowcount
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            obs.log_info(f"Query with plan executed successfully", {
                "execution_time_ms": execution_time_ms,
                "row_count": row_count,
                "has_plan": bool(query_plan)
            })
            
            return PostgreSQLQueryResult(
                records=records,
                row_count=row_count,
                execution_time_ms=execution_time_ms,
                success=True,
                query_plan=query_plan
            )
    
    except Exception as e:
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        obs.log_error(f"Query with plan execution failed: {e}")
        
        return PostgreSQLQueryResult(
            records=[],
            row_count=0,
            execution_time_ms=execution_time_ms,
            success=False,
            error_message=str(e)
        )


def execute_transaction(
    connection: Connection,
    queries: List[Dict[str, Any]]
) -> Dict[str, Any]:
    start_time = datetime.now()
    
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            results = []
            
            try:
                connection.begin()
                
                for query_info in queries:
                    query = query_info["query"]
                    parameters = query_info.get("parameters")
                    fetch_all = query_info.get("fetch_all", True)
                    
                    if parameters:
                        if isinstance(parameters, dict):
                            cursor.execute(query, parameters)
                        else:
                            cursor.execute(query, parameters)
                    else:
                        cursor.execute(query)
                    
                    if fetch_all:
                        records = [dict(record) for record in cursor.fetchall()]
                    else:
                        record = cursor.fetchone()
                        records = [dict(record)] if record else []
                    
                    results.append({
                        "records": records,
                        "row_count": cursor.rowcount
                    })
                
                connection.commit()
                execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                obs.log_info(f"Transaction executed successfully", {
                    "queries_count": len(queries),
                    "execution_time_ms": execution_time_ms
                })
                
                return {
                    "success": True,
                    "results": results,
                    "execution_time_ms": execution_time_ms,
                    "queries_count": len(queries)
                }
            
            except Exception as e:
                connection.rollback()
                raise e
    
    except Exception as e:
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        obs.log_error(f"Transaction execution failed: {e}")
        
        return {
            "success": False,
            "error": str(e),
            "execution_time_ms": execution_time_ms,
            "queries_count": len(queries)
        }


def explain_query(
    connection: Connection,
    query: str,
    parameters: Optional[Union[Dict[str, Any], List[Any]]] = None,
    analyze: bool = False
) -> Dict[str, Any]:
    try:
        explain_query = f"EXPLAIN {'ANALYZE' if analyze else ''} {query}"
        
        result = execute_query(connection, explain_query, parameters)
        
        if result.success:
            plan = _parse_query_plan(result.records)
            return {
                "success": True,
                "plan": plan,
                "execution_time_ms": result.execution_time_ms
            }
        else:
            return {
                "success": False,
                "error": result.error_message,
                "execution_time_ms": result.execution_time_ms
            }
    
    except Exception as e:
        obs.log_error(f"Query explanation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def get_database_info(connection: Connection) -> Dict[str, Any]:
    try:
        info = {}
        
        queries = {
            "version": "SELECT version()",
            "size": "SELECT pg_size_pretty(pg_database_size(current_database())) as size",
            "connections": "SELECT count(*) as connections FROM pg_stat_activity WHERE state = 'active'",
            "tables": "SELECT count(*) as tables FROM information_schema.tables WHERE table_schema = 'public'",
            "indexes": "SELECT count(*) as indexes FROM pg_indexes WHERE schemaname = 'public'"
        }
        
        for key, query in queries.items():
            result = execute_query(connection, query)
            if result.success and result.records:
                info[key] = result.records[0]
        
        return {
            "success": True,
            "info": info,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"Failed to get database info: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def get_query_statistics(connection: Connection) -> Dict[str, Any]:
    try:
        queries = [
            "SELECT query, calls, total_time, mean_time, rows FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10",
            "SELECT datname, numbackends, xact_commit, xact_rollback, blks_read, blks_hit, tup_returned, tup_fetched, tup_inserted, tup_updated, tup_deleted FROM pg_stat_database WHERE datname = current_database()",
            "SELECT schemaname, tablename, seq_scan, seq_tup_read, idx_scan, idx_tup_fetch, n_tup_ins, n_tup_upd, n_tup_del FROM pg_stat_user_tables ORDER BY seq_scan + idx_scan DESC LIMIT 10"
        ]
        
        stats = {}
        for i, query in enumerate(queries):
            result = execute_query(connection, query)
            if result.success:
                key = ["statements", "database", "tables"][i]
                stats[key] = result.records
        
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"Failed to get query statistics: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def close_connection(connection: Connection):
    try:
        if connection and not connection.closed:
            connection.close()
            obs.log_info("PostgreSQL connection closed successfully")
    except Exception as e:
        obs.log_error(f"Failed to close PostgreSQL connection: {e}")


def _parse_query_plan(plan_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        if not plan_records:
            return {}
        
        plan_text = plan_records[0].get("QUERY PLAN", "")
        if not plan_text:
            return {}
        
        return {
            "plan_text": plan_text,
            "estimated_cost": _extract_cost_from_plan(plan_text),
            "estimated_rows": _extract_rows_from_plan(plan_text),
            "operations": _extract_operations_from_plan(plan_text)
        }
    
    except Exception as e:
        obs.log_error(f"Failed to parse query plan: {e}")
        return {}


def _extract_cost_from_plan(plan_text: str) -> Optional[float]:
    try:
        import re
        match = re.search(r'cost=\d+\.\d+\.\.(\d+\.\d+)', plan_text)
        if match:
            return float(match.group(1))
    except:
        pass
    return None


def _extract_rows_from_plan(plan_text: str) -> Optional[int]:
    try:
        import re
        match = re.search(r'rows=(\d+)', plan_text)
        if match:
            return int(match.group(1))
    except:
        pass
    return None


def _extract_operations_from_plan(plan_text: str) -> List[str]:
    try:
        operations = []
        lines = plan_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and ('->' in line or line.startswith(('Seq Scan', 'Index Scan', 'Bitmap Heap Scan', 'Nested Loop', 'Hash Join', 'Merge Join'))):
                operations.append(line)
        return operations
    except:
        return []


class PostgreSQLTransactionManager:
    def __init__(self, connection: Connection):
        self.connection = connection
        self.obs = ObservabilityClient(service_name="postgres-transaction-manager")

    def execute_transaction(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        return execute_transaction(self.connection, queries)

    def execute_batch_insert(
        self,
        table: str,
        columns: List[str],
        values: List[List[Any]]
    ) -> Dict[str, Any]:
        start_time = datetime.now()
        
        try:
            with self.connection.cursor() as cursor:
                query = sql.SQL("INSERT INTO {} ({}) VALUES %s").format(
                    sql.Identifier(table),
                    sql.SQL(', ').join(map(sql.Identifier, columns))
                )
                
                execute_values(cursor, query, values)
                self.connection.commit()
                
                execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                self.obs.log_info(f"Batch insert executed successfully", {
                    "table": table,
                    "rows_count": len(values),
                    "execution_time_ms": execution_time_ms
                })
                
                return {
                    "success": True,
                    "rows_inserted": len(values),
                    "execution_time_ms": execution_time_ms
                }
        
        except Exception as e:
            self.connection.rollback()
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.obs.log_error(f"Batch insert failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time_ms
            }

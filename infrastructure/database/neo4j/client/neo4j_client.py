import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from neo4j import GraphDatabase, Driver, Session, Result
from neo4j.exceptions import ServiceUnavailable, TransientError
from pydantic import BaseModel, Field, ConfigDict

project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.observability.scripts.observability_client import ObservabilityClient


class Neo4jConnectionConfig(BaseModel):
    model_config = ConfigDict(extra='allow')
    uri: str = "bolt://172.29.0.30:7687"
    username: str = "neo4j"
    password: str = "NeoPassword123!"
    database: str = "neo4j"
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 100
    connection_timeout: int = 30


class Neo4jQueryResult(BaseModel):
    records: List[Dict[str, Any]]
    summary: Dict[str, Any]
    execution_time_ms: float
    success: bool
    error_message: Optional[str] = None


obs = ObservabilityClient(service_name="neo4j-client")


def get_driver(config: Optional[Neo4jConnectionConfig] = None) -> Driver:
    if config is None:
        config = Neo4jConnectionConfig()
    
    obs.log_info("Initializing Neo4j driver", {"uri": config.uri, "database": config.database})
    
    try:
        driver = GraphDatabase.driver(
            config.uri,
            auth=(config.username, config.password),
            max_connection_lifetime=config.max_connection_lifetime,
            max_connection_pool_size=config.max_connection_pool_size,
            connection_timeout=config.connection_timeout
        )
        
        driver.verify_connectivity()
        obs.log_info("Neo4j driver initialized successfully")
        return driver
    
    except Exception as e:
        obs.log_error(f"Failed to initialize Neo4j driver: {e}")
        raise


def get_session(driver: Driver, database: Optional[str] = None) -> Session:
    if database is None:
        database = Neo4jConnectionConfig().database
    
    return driver.session(database=database)


def execute_query(
    driver: Driver,
    query: str,
    parameters: Optional[Dict[str, Any]] = None,
    database: Optional[str] = None
) -> Neo4jQueryResult:
    start_time = datetime.now()
    
    try:
        with get_session(driver, database) as session:
            result = session.run(query, parameters or {})
            records = [record.data() for record in result]
            summary = result.consume()
            
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            obs.log_info(f"Query executed successfully", {
                "execution_time_ms": execution_time_ms,
                "records_returned": len(records),
                "database": database or "default"
            })
            
            return Neo4jQueryResult(
                records=records,
                summary={
                    "result_available_after": summary.result_available_after,
                    "result_consumed_after": summary.result_consumed_after,
                    "counters": dict(summary.counters),
                    "query_type": summary.query_type,
                    "database": summary.database
                },
                execution_time_ms=execution_time_ms,
                success=True
            )
    
    except (ServiceUnavailable, TransientError) as e:
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        obs.log_error(f"Neo4j service error: {e}")
        
        return Neo4jQueryResult(
            records=[],
            summary={},
            execution_time_ms=execution_time_ms,
            success=False,
            error_message=str(e)
        )
    
    except Exception as e:
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        obs.log_error(f"Query execution failed: {e}")
        
        return Neo4jQueryResult(
            records=[],
            summary={},
            execution_time_ms=execution_time_ms,
            success=False,
            error_message=str(e)
        )


def execute_read_query(
    driver: Driver,
    query: str,
    parameters: Optional[Dict[str, Any]] = None,
    database: Optional[str] = None
) -> Neo4jQueryResult:
    try:
        with get_session(driver, database) as session:
            start_time = datetime.now()
            result = session.execute_read(lambda tx: tx.run(query, parameters or {}))
            records = [record.data() for record in result]
            summary = result.consume()
            
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            obs.log_info(f"Read query executed successfully", {
                "execution_time_ms": execution_time_ms,
                "records_returned": len(records)
            })
            
            return Neo4jQueryResult(
                records=records,
                summary={
                    "result_available_after": summary.result_available_after,
                    "result_consumed_after": summary.result_consumed_after,
                    "counters": dict(summary.counters),
                    "query_type": summary.query_type,
                    "database": summary.database
                },
                execution_time_ms=execution_time_ms,
                success=True
            )
    
    except Exception as e:
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        obs.log_error(f"Read query execution failed: {e}")
        
        return Neo4jQueryResult(
            records=[],
            summary={},
            execution_time_ms=execution_time_ms,
            success=False,
            error_message=str(e)
        )


def execute_write_query(
    driver: Driver,
    query: str,
    parameters: Optional[Dict[str, Any]] = None,
    database: Optional[str] = None
) -> Neo4jQueryResult:
    try:
        with get_session(driver, database) as session:
            start_time = datetime.now()
            result = session.execute_write(lambda tx: tx.run(query, parameters or {}))
            records = [record.data() for record in result]
            summary = result.consume()
            
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            obs.log_info(f"Write query executed successfully", {
                "execution_time_ms": execution_time_ms,
                "records_returned": len(records),
                "nodes_created": summary.counters.nodes_created,
                "relationships_created": summary.counters.relationships_created
            })
            
            return Neo4jQueryResult(
                records=records,
                summary={
                    "result_available_after": summary.result_available_after,
                    "result_consumed_after": summary.result_consumed_after,
                    "counters": dict(summary.counters),
                    "query_type": summary.query_type,
                    "database": summary.database
                },
                execution_time_ms=execution_time_ms,
                success=True
            )
    
    except Exception as e:
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        obs.log_error(f"Write query execution failed: {e}")
        
        return Neo4jQueryResult(
            records=[],
            summary={},
            execution_time_ms=execution_time_ms,
            success=False,
            error_message=str(e)
        )


def explain_query(
    driver: Driver,
    query: str,
    parameters: Optional[Dict[str, Any]] = None,
    database: Optional[str] = None
) -> Dict[str, Any]:
    try:
        explain_query = f"EXPLAIN {query}"
        result = execute_query(driver, explain_query, parameters, database)
        
        if result.success and result.records:
            plan = result.records[0].get("plan", {})
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


def profile_query(
    driver: Driver,
    query: str,
    parameters: Optional[Dict[str, Any]] = None,
    database: Optional[str] = None
) -> Dict[str, Any]:
    try:
        profile_query = f"PROFILE {query}"
        result = execute_query(driver, profile_query, parameters, database)
        
        if result.success and result.records:
            profile = result.records[0].get("profile", {})
            return {
                "success": True,
                "profile": profile,
                "execution_time_ms": result.execution_time_ms,
                "db_hits": profile.get("dbHits", 0),
                "rows": profile.get("rows", 0)
            }
        else:
            return {
                "success": False,
                "error": result.error_message,
                "execution_time_ms": result.execution_time_ms
            }
    
    except Exception as e:
        obs.log_error(f"Query profiling failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def get_database_info(driver: Driver, database: Optional[str] = None) -> Dict[str, Any]:
    try:
        queries = [
            "CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Kernel') YIELD attributes RETURN attributes",
            "CALL db.info() YIELD name, value RETURN name, value",
            "CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition"
        ]
        
        info = {}
        
        for query in queries:
            result = execute_query(driver, query, {}, database)
            if result.success:
                query_key = query.split("CALL")[1].split("(")[0].strip()
                info[query_key] = result.records
        
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


def get_query_statistics(driver: Driver, database: Optional[str] = None) -> Dict[str, Any]:
    try:
        query = "CALL dbms.listQueries() YIELD queryId, query, metaData, runtime, allocatedBytes, hitCount, faultCount RETURN queryId, query, metaData, runtime, allocatedBytes, hitCount, faultCount"
        
        result = execute_query(driver, query, {}, database)
        
        if result.success:
            return {
                "success": True,
                "active_queries": result.records,
                "count": len(result.records),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "success": False,
                "error": result.error_message
            }
    
    except Exception as e:
        obs.log_error(f"Failed to get query statistics: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def close_driver(driver: Driver):
    try:
        driver.close()
        obs.log_info("Neo4j driver closed successfully")
    except Exception as e:
        obs.log_error(f"Failed to close Neo4j driver: {e}")


class Neo4jTransactionManager:
    def __init__(self, driver: Driver, database: Optional[str] = None):
        self.driver = driver
        self.database = database
        self.obs = ObservabilityClient(service_name="neo4j-transaction-manager")

    def execute_transaction(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        start_time = datetime.now()
        
        try:
            with get_session(self.driver, self.database) as session:
                results = []
                
                with session.begin_transaction() as tx:
                    for query_info in queries:
                        query = query_info["query"]
                        parameters = query_info.get("parameters", {})
                        
                        result = tx.run(query, parameters)
                        records = [record.data() for record in result]
                        summary = result.consume()
                        
                        results.append({
                            "records": records,
                            "summary": {
                                "counters": dict(summary.counters),
                                "query_type": summary.query_type
                            }
                        })
                
                execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                
                self.obs.log_info(f"Transaction executed successfully", {
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
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.obs.log_error(f"Transaction execution failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "queries_count": len(queries)
            }

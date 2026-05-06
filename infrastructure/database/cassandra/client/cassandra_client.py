import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from cassandra.cluster import Cluster, Session
from cassandra.query import SimpleStatement, PreparedStatement
from cassandra.protocol import ConsistencyLevel
from cassandra.query import dict_factory
from cassandra.auth import PlainTextAuthProvider
from pydantic import BaseModel, Field, ConfigDict

project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.observability.scripts.observability_client import ObservabilityClient


class CassandraConnectionConfig(BaseModel):
    model_config = ConfigDict(extra='allow')
    contact_points: List[str] = Field(default=["172.29.0.40:9042"])
    keyspace: str = Field("scaibu_default")
    username: Optional[str] = Field("cassandra")
    password: Optional[str] = Field("CassandraPassword123!")
    consistency_level: str = Field("QUORUM")
    connection_timeout: int = Field(30)
    request_timeout: int = Field(60)


class CassandraQueryResult(BaseModel):
    records: List[Dict[str, Any]]
    execution_time_ms: float
    success: bool
    error_message: Optional[str] = None
    query_plan: Optional[Dict[str, Any]] = None
    consistency_level: Optional[str] = None


obs = ObservabilityClient(service_name="cassandra-client")


def get_cluster(config: Optional[CassandraConnectionConfig] = None) -> Cluster:
    if config is None:
        config = CassandraConnectionConfig()
    
    obs.log_info("Initializing Cassandra cluster", {
        "contact_points": config.contact_points,
        "keyspace": config.keyspace
    })
    
    try:
        auth_provider = None
        if config.username and config.password:
            auth_provider = PlainTextAuthProvider(
                username=config.username,
                password=config.password
            )
        
        cluster = Cluster(
            contact_points=config.contact_points,
            auth_provider=auth_provider,
            connect_timeout=config.connection_timeout
        )
        
        obs.log_info("Cassandra cluster initialized successfully")
        return cluster
    
    except Exception as e:
        obs.log_error(f"Failed to initialize Cassandra cluster: {e}")
        raise


def get_session(cluster: Cluster, keyspace: Optional[str] = None) -> Session:
    try:
        session = cluster.connect()
        
        if keyspace:
            session.set_keyspace(keyspace)
        
        session.row_factory = dict_factory
        session.default_consistency_level = ConsistencyLevel.QUORUM
        
        obs.log_info(f"Cassandra session established for keyspace: {keyspace}")
        return session
    
    except Exception as e:
        obs.log_error(f"Failed to create Cassandra session: {e}")
        raise


def execute_query(
    session: Session,
    query: str,
    parameters: Optional[Dict[str, Any]] = None,
    consistency_level: Optional[str] = None
) -> CassandraQueryResult:
    start_time = datetime.now()
    
    try:
        if consistency_level:
            original_consistency = session.default_consistency_level
            session.default_consistency_level = getattr(ConsistencyLevel, consistency_level.upper())
        
        if parameters:
            prepared = session.prepare(query)
            result = session.execute(prepared, parameters)
        else:
            result = session.execute(query)
        
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        records = [dict(row) for row in result]
        
        obs.log_info(f"Cassandra query executed successfully", {
            "execution_time_ms": execution_time_ms,
            "records_returned": len(records)
        })
        
        return CassandraQueryResult(
            records=records,
            execution_time_ms=execution_time_ms,
            success=True,
            consistency_level=consistency_level
        )
    
    except Exception as e:
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        obs.log_error(f"Cassandra query execution failed: {e}")
        
        return CassandraQueryResult(
            records=[],
            execution_time_ms=execution_time_ms,
            success=False,
            error_message=str(e)
        )


def execute_query_with_plan(
    session: Session,
    query: str,
    parameters: Optional[Dict[str, Any]] = None,
    consistency_level: Optional[str] = None
) -> CassandraQueryResult:
    start_time = datetime.now()
    
    try:
        # Enable tracing for query plan
        if consistency_level:
            original_consistency = session.default_consistency_level
            session.default_consistency_level = getattr(ConsistencyLevel, consistency_level.upper())
        
        # Execute with tracing enabled
        if parameters:
            prepared = session.prepare(query)
            prepared.is_idempotent = True
            result = session.execute(prepared, parameters, trace=True)
        else:
            simple_stmt = SimpleStatement(query, is_idempotent=True)
            result = session.execute(simple_stmt, trace=True)
        
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        records = [dict(row) for row in result]
        
        # Get query plan from trace
        query_plan = None
        if result.query_trace:
            query_plan = {
                "trace_id": str(result.query_trace.trace_id),
                "events": [
                    {
                        "source": event.source,
                        "source_elapsed": event.source_elapsed,
                        "description": event.description
                    }
                    for event in result.query_trace.events
                ],
                "duration_micros": result.query_trace.duration
            }
        
        obs.log_info(f"Cassandra query with plan executed successfully", {
            "execution_time_ms": execution_time_ms,
            "records_returned": len(records),
            "has_trace": result.query_trace is not None
        })
        
        return CassandraQueryResult(
            records=records,
            execution_time_ms=execution_time_ms,
            success=True,
            query_plan=query_plan,
            consistency_level=consistency_level
        )
    
    except Exception as e:
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        obs.log_error(f"Cassandra query with plan execution failed: {e}")
        
        return CassandraQueryResult(
            records=[],
            execution_time_ms=execution_time_ms,
            success=False,
            error_message=str(e)
        )


def explain_query(
    session: Session,
    query: str,
    parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    try:
        # Use tracing to get execution plan
        result = execute_query_with_plan(session, query, parameters)
        
        if result.success and result.query_plan:
            return {
                "success": True,
                "query_plan": result.query_plan,
                "execution_time_ms": result.execution_time_ms
            }
        else:
            return {
                "success": False,
                "error": result.error_message,
                "execution_time_ms": result.execution_time_ms
            }
    
    except Exception as e:
        obs.log_error(f"Cassandra query explanation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def get_cluster_info(session: Session) -> Dict[str, Any]:
    try:
        info = {}
        
        # Get cluster name
        cluster_query = "SELECT cluster_name FROM system.local"
        result = execute_query(session, cluster_query)
        if result.success and result.records:
            info["cluster_name"] = result.records[0].get("cluster_name")
        
        # Get keyspace info
        keyspace_query = f"SELECT * FROM system_schema.keyspaces WHERE keyspace_name = '{session.keyspace}'"
        result = execute_query(session, keyspace_query)
        if result.success and result.records:
            info["keyspace_info"] = result.records
        
        # Get table info
        table_query = "SELECT table_name FROM system_schema.tables WHERE keyspace_name = %s"
        result = execute_query(session, table_query, {"keyspace_name": session.keyspace})
        if result.success and result.records:
            info["tables"] = [record["table_name"] for record in result.records]
        
        return {
            "success": True,
            "info": info,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"Failed to get cluster info: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def get_table_statistics(session: Session, table_name: str) -> Dict[str, Any]:
    try:
        stats = {}
        
        # Get table stats
        stats_query = f"SELECT * FROM system_schema.tables WHERE keyspace_name = %s AND table_name = %s"
        result = execute_query(session, stats_query, {
            "keyspace_name": session.keyspace,
            "table_name": table_name
        })
        
        if result.success and result.records:
            stats["table_info"] = result.records[0]
        
        # Get column info
        column_query = "SELECT * FROM system_schema.columns WHERE keyspace_name = %s AND table_name = %s"
        result = execute_query(session, column_query, {
            "keyspace_name": session.keyspace,
            "table_name": table_name
        })
        
        if result.success and result.records:
            stats["columns"] = result.records
        
        # Get index info
        index_query = "SELECT * FROM system_schema.indexes WHERE keyspace_name = %s AND table_name = %s"
        result = execute_query(session, index_query, {
            "keyspace_name": session.keyspace,
            "table_name": table_name
        })
        
        if result.success and result.records:
            stats["indexes"] = result.records
        
        return stats
    
    except Exception as e:
        obs.log_error(f"Failed to get table statistics: {e}")
        return {}


def close_cluster(cluster: Cluster):
    try:
        cluster.shutdown()
        obs.log_info("Cassandra cluster shut down successfully")
    except Exception as e:
        obs.log_error(f"Failed to shut down Cassandra cluster: {e}")


class CassandraTransactionManager:
    def __init__(self, session: Session):
        self.session = session
        self.obs = ObservabilityClient(service_name="cassandra-transaction-manager")

    def execute_batch(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        start_time = datetime.now()
        
        try:
            batch = self.session.batch()
            
            for query_info in queries:
                query = query_info["query"]
                parameters = query_info.get("parameters", {})
                
                if parameters:
                    prepared = self.session.prepare(query)
                    batch.add(prepared, parameters)
                else:
                    batch.add(query)
            
            results = self.session.execute(batch)
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            self.obs.log_info(f"Cassandra batch executed successfully", {
                "queries_count": len(queries),
                "execution_time_ms": execution_time_ms
            })
            
            return {
                "success": True,
                "execution_time_ms": execution_time_ms,
                "queries_count": len(queries)
            }
        
        except Exception as e:
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.obs.log_error(f"Cassandra batch execution failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time_ms,
                "queries_count": len(queries)
            }

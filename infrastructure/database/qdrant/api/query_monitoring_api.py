import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

project_root = Path(__file__).resolve().parents[4)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.database.shared.query_monitoring_interfaces import QueryMonitoringConfig
from infrastructure.observability.scripts.observability_client import ObservabilityClient
from infrastructure.database.qdrant.client.qdrant_client import get_http_client, QdrantConnectionConfig
from .qdrant_monitoring_client import QdrantMonitoringClient
from .qdrant_query_analyzer import QdrantQueryAnalyzer
from .qdrant_metrics_exporter import QdrantMetricsExporter


router = APIRouter(prefix="/qdrant/queries", tags=["qdrant-query-monitoring"])
obs = ObservabilityClient(service_name="qdrant-query-monitoring-api")


class QueryExecutionRequest(BaseModel):
    query: str = Field(..., description="Qdrant operation to execute")
    params: Optional[Dict[str, Any]] = Field(None, description="Operation parameters")


class QueryAnalysisRequest(BaseModel):
    query: str = Field(..., description="Qdrant operation to analyze")
    database: str = Field("qdrant", description="Database name")


class PerformanceReportRequest(BaseModel):
    database: str = Field("qdrant", description="Database name")
    period_hours: int = Field(24, description="Report period in hours")


class SlowQueryRequest(BaseModel):
    threshold_ms: float = Field(1000.0, description="Slow query threshold in milliseconds")
    limit: int = Field(50, description="Maximum number of results")


def get_monitoring_client() -> QdrantMonitoringClient:
    try:
        config = QdrantConnectionConfig()
        session = get_http_client(config)
        monitoring_config = QueryMonitoringConfig()
        return QdrantMonitoringClient(session, monitoring_config)
    except Exception as e:
        obs.log_error(f"Failed to create monitoring client: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect to database")


@router.post("/execute", summary="Execute query with monitoring")
async def execute_query_with_monitoring(request: QueryExecutionRequest):
    obs.log_info("execute_query_with_monitoring")
    
    try:
        client = get_monitoring_client()
        result = client.execute_with_monitoring(request.query, request.params)
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"execute_query_with_monitoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slow", summary="Get slow queries")
async def get_slow_queries(
    threshold_ms: float = Query(1000.0, description="Slow query threshold in milliseconds"),
    limit: int = Query(50, description="Maximum number of results")
):
    obs.log_info(f"get_slow_queries threshold_ms={threshold_ms} limit={limit}")
    
    try:
        client = get_monitoring_client()
        slow_queries = client.collector.get_slow_queries(threshold_ms, limit)
        
        return {
            "success": True,
            "data": {
                "slow_queries": [query.dict() for query in slow_queries],
                "count": len(slow_queries),
                "threshold_ms": threshold_ms
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_slow_queries failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance", summary="Get query performance metrics")
async def get_query_performance(
    period_minutes: int = Query(60, description="Performance period in minutes")
):
    obs.log_info(f"get_query_performance period_minutes={period_minutes}")
    
    try:
        client = get_monitoring_client()
        summary = client.get_performance_summary(period_minutes)
        
        return {
            "success": True,
            "data": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_query_performance failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", summary="Analyze query performance")
async def analyze_query(request: QueryAnalysisRequest):
    obs.log_info(f"analyze_query database={request.database}")
    
    try:
        config = QdrantConnectionConfig()
        session = get_http_client(config)
        analyzer = QdrantQueryAnalyzer(session)
        
        result = analyzer.analyze_query(request.query, request.database)
        
        return {
            "success": True,
            "data": result.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"analyze_query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explain", summary="Explain query execution plan")
async def explain_query(
    query: str = Query(..., description="Qdrant operation to explain"),
    database: str = Query("qdrant", description="Database name")
):
    obs.log_info(f"explain_query database={database}")
    
    try:
        config = QdrantConnectionConfig()
        session = get_http_client(config)
        analyzer = QdrantQueryAnalyzer(session)
        
        plan = analyzer.explain_query(query, database)
        
        return {
            "success": True,
            "data": {
                "query": query,
                "database": database,
                "execution_plan": plan
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"explain_query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/indexes/suggest", summary="Suggest optimizations for query")
async def suggest_optimizations(request: QueryAnalysisRequest):
    obs.log_info(f"suggest_optimizations database={request.database}")
    
    try:
        config = QdrantConnectionConfig()
        session = get_http_client(config)
        analyzer = QdrantQueryAnalyzer(session)
        
        suggestions = analyzer.suggest_indexes(request.query, request.database)
        
        return {
            "success": True,
            "data": {
                "query": request.query,
                "database": request.database,
                "suggested_optimizations": suggestions
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"suggest_optimizations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/performance", summary="Generate performance report")
async def generate_performance_report(request: PerformanceReportRequest):
    obs.log_info(f"generate_performance_report database={request.database} period_hours={request.period_hours}")
    
    try:
        config = QdrantConnectionConfig()
        session = get_http_client(config)
        analyzer = QdrantQueryAnalyzer(session)
        
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(hours=request.period_hours)
        
        report = analyzer.generate_performance_report(request.database, period_start, period_end)
        
        return {
            "success": True,
            "data": report.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"generate_performance_report failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/issues", summary="Identify performance issues")
async def identify_performance_issues():
    obs.log_info("identify_performance_issues")
    
    try:
        client = get_monitoring_client()
        issues = client.identify_performance_issues()
        
        return {
            "success": True,
            "data": {
                "issues": issues,
                "count": len(issues),
                "severity_breakdown": {
                    "critical": len([i for i in issues if i["severity"] == "critical"]),
                    "high": len([i for i in issues if i["severity"] == "high"]),
                    "medium": len([i for i in issues if i["severity"] == "medium"]),
                    "low": len([i for i in issues if i["severity"] == "low"])
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"identify_performance_issues failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/slow", summary="Get slow queries analysis")
async def get_slow_queries_analysis(
    hours: int = Query(24, description="Analysis period in hours")
):
    obs.log_info(f"get_slow_queries_analysis hours={hours}")
    
    try:
        client = get_monitoring_client()
        analysis = client.get_slow_queries_analysis(hours)
        
        return {
            "success": True,
            "data": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_slow_queries_analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Get database health report")
async def get_database_health_report():
    obs.log_info("get_database_health_report")
    
    try:
        client = get_monitoring_client()
        health_report = client.get_database_health_report()
        
        return {
            "success": True,
            "data": health_report,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_database_health_report failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", summary="Get Prometheus metrics")
async def get_prometheus_metrics():
    obs.log_info("get_prometheus_metrics")
    
    try:
        config = QdrantConnectionConfig()
        session = get_http_client(config)
        exporter = QdrantMetricsExporter(session)
        
        metrics = exporter.get_prometheus_metrics()
        
        return metrics, 200, {"Content-Type": "text/plain"}
    
    except Exception as e:
        obs.log_error(f"get_prometheus_metrics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/json", summary="Get metrics in JSON format")
async def get_json_metrics():
    obs.log_info("get_json_metrics")
    
    try:
        config = QdrantConnectionConfig()
        session = get_http_client(config)
        exporter = QdrantMetricsExporter(session)
        
        metrics = exporter.export_json_metrics()
        
        return {
            "success": True,
            "data": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_json_metrics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_name}/performance", summary="Get collection-specific performance")
async def get_collection_performance(
    collection_name: str,
    period_minutes: int = Query(60, description="Performance period in minutes")
):
    obs.log_info(f"get_collection_performance collection={collection_name} period_minutes={period_minutes}")
    
    try:
        client = get_monitoring_client()
        performance = client.get_collection_performance_analysis(collection_name)
        
        return {
            "success": True,
            "data": performance,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_collection_performance failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/analysis", summary="Get schema performance analysis")
async def get_schema_performance_analysis():
    obs.log_info("get_schema_performance_analysis")
    
    try:
        client = get_monitoring_client()
        schema_analysis = client.get_schema_performance_analysis()
        
        return {
            "success": True,
            "data": schema_analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_schema_performance_analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/info", summary="Get database schema information")
async def get_schema_info(
    database: str = Query("qdrant", description="Database name")
):
    obs.log_info(f"get_schema_info database={database}")
    
    try:
        config = QdrantConnectionConfig()
        session = get_http_client(config)
        analyzer = QdrantQueryAnalyzer(session)
        
        schema_analysis = analyzer.get_schema_analysis(database)
        
        return {
            "success": True,
            "data": schema_analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_schema_info failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plan/analysis", summary="Get detailed query plan analysis")
async def get_query_plan_analysis(
    query: str = Query(..., description="Qdrant operation to analyze"),
    database: str = Query("qdrant", description="Database name")
):
    obs.log_info(f"get_query_plan_analysis database={database}")
    
    try:
        config = QdrantConnectionConfig()
        session = get_http_client(config)
        analyzer = QdrantQueryAnalyzer(session)
        
        analysis = analyzer.get_query_plan_analysis(query, database)
        
        return {
            "success": True,
            "data": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_query_plan_analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hnsw/analysis", summary="Get HNSW performance analysis")
async def get_hnsw_performance_analysis(
    collection_name: str = Query(..., description="Collection name to analyze")
):
    obs.log_info(f"get_hnsw_performance_analysis collection={collection_name}")
    
    try:
        client = get_monitoring_client()
        hnsw_analysis = client.collector.get_hnsw_performance_analysis(collection_name)
        
        return {
            "success": True,
            "data": hnsw_analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_hnsw_performance_analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vector/performance", summary="Get vector search performance")
async def get_vector_search_performance(
    collection_name: str = Query(..., description="Collection name to analyze")
):
    obs.log_info(f"get_vector_search_performance collection={collection_name}")
    
    try:
        client = get_monitoring_client()
        vector_performance = client.collector.get_vector_search_performance(collection_name)
        
        return {
            "success": True,
            "data": vector_performance,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_vector_search_performance failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/operation-types/performance", summary="Get performance by operation type")
async def get_operation_type_performance(
    period_minutes: int = Query(60, description="Performance period in minutes")
):
    obs.log_info(f"get_operation_type_performance period_minutes={period_minutes}")
    
    try:
        client = get_monitoring_client()
        metrics = client.collector.collect_query_metrics(limit=1000)
        
        period_start = datetime.utcnow() - timedelta(minutes=period_minutes)
        recent_metrics = [m for m in metrics if m.timestamp >= period_start]
        
        operation_type_stats = {}
        for metric in recent_metrics:
            operation_type = metric.query_type or "unknown"
            if operation_type not in operation_type_stats:
                operation_type_stats[operation_type] = {
                    "count": 0,
                    "total_time": 0,
                    "avg_time": 0,
                    "max_time": 0,
                    "slow_count": 0
                }
            
            stats = operation_type_stats[operation_type]
            stats["count"] += 1
            stats["total_time"] += metric.execution_time_ms
            stats["max_time"] = max(stats["max_time"], metric.execution_time_ms)
            
            if metric.performance_level in ["slow", "critical"]:
                stats["slow_count"] += 1
        
        for operation_type, stats in operation_type_stats.items():
            if stats["count"] > 0:
                stats["avg_time"] = stats["total_time"] / stats["count"]
                stats["slow_percentage"] = (stats["slow_count"] / stats["count"]) * 100
        
        return {
            "success": True,
            "data": {
                "period_minutes": period_minutes,
                "operation_type_performance": operation_type_stats
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_operation_type_performance failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/overview", summary="Get collections overview")
async def get_collections_overview():
    obs.log_info("get_collections_overview")
    
    try:
        config = QdrantConnectionConfig()
        session = get_http_client(config)
        
        from infrastructure.database.qdrant.client.qdrant_client import list_collections, get_collection_info, count_points
        
        collections_result = list_collections(session)
        
        if not collections_result.success:
            raise HTTPException(status_code=500, detail="Failed to list collections")
        
        collections = collections_result.result.get("collections", [])
        overview = {
            "total_collections": len(collections),
            "collections": []
        }
        
        for collection in collections[:20]:  # Limit to first 20 collections
            collection_name = collection.get("name", "unknown")
            
            try:
                # Get collection info
                info_result = get_collection_info(session, collection_name)
                count_result = count_points(session, collection_name)
                
                collection_data = {
                    "name": collection_name,
                    "vectors_config": collection.get("vectors", {}),
                    "point_count": count_result.result.get("result", {}).get("count", 0) if count_result.success else 0,
                    "config": info_result.result.get("result", {}).get("config", {}) if info_result.success else {}
                }
                
                overview["collections"].append(collection_data)
                
            except Exception:
                # Skip collections that can't be analyzed
                pass
        
        return {
            "success": True,
            "data": overview,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_collections_overview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

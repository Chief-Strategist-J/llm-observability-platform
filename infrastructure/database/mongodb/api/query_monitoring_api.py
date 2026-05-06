import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

project_root = Path(__file__).resolve().parents[4]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.database.shared.query_monitoring_interfaces import QueryMonitoringConfig
from infrastructure.observability.scripts.observability_client import ObservabilityClient
from infrastructure.database.mongodb.client.mongodb_client import get_client, MongoConnectionConfig
from .mongodb_monitoring_client import MongoDBMonitoringClient
from .mongodb_query_analyzer import MongoDBQueryAnalyzer
from .mongodb_metrics_exporter import MongoDBMetricsExporter


router = APIRouter(prefix="/mongodb/queries", tags=["mongodb-query-monitoring"])
obs = ObservabilityClient(service_name="mongodb-query-monitoring-api")


class QueryExecutionRequest(BaseModel):
    query: str = Field(..., description="MongoDB query to execute")
    params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")


class QueryAnalysisRequest(BaseModel):
    query: str = Field(..., description="MongoDB query to analyze")
    database: str = Field("scaibu_default", description="Database name")


class PerformanceReportRequest(BaseModel):
    database: str = Field("scaibu_default", description="Database name")
    period_hours: int = Field(24, description="Report period in hours")


class SlowQueryRequest(BaseModel):
    threshold_ms: float = Field(1000.0, description="Slow query threshold in milliseconds")
    limit: int = Field(50, description="Maximum number of results")


def get_monitoring_client() -> MongoDBMonitoringClient:
    try:
        config = MongoConnectionConfig()
        client = get_client(config.uri)
        monitoring_config = QueryMonitoringConfig()
        return MongoDBMonitoringClient(client, monitoring_config)
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
        config = MongoConnectionConfig()
        client = get_client(config.uri)
        analyzer = MongoDBQueryAnalyzer(client)
        
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
    query: str = Query(..., description="Query to explain"),
    database: str = Query("scaibu_default", description="Database name")
):
    obs.log_info(f"explain_query database={database}")
    
    try:
        config = MongoConnectionConfig()
        client = get_client(config.uri)
        analyzer = MongoDBQueryAnalyzer(client)
        
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


@router.post("/indexes/suggest", summary="Suggest indexes for query")
async def suggest_indexes(request: QueryAnalysisRequest):
    obs.log_info(f"suggest_indexes database={request.database}")
    
    try:
        config = MongoConnectionConfig()
        client = get_client(config.uri)
        analyzer = MongoDBQueryAnalyzer(client)
        
        suggestions = analyzer.suggest_indexes(request.query, request.database)
        
        return {
            "success": True,
            "data": {
                "query": request.query,
                "database": request.database,
                "suggested_indexes": suggestions
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"suggest_indexes failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/performance", summary="Generate performance report")
async def generate_performance_report(request: PerformanceReportRequest):
    obs.log_info(f"generate_performance_report database={request.database} period_hours={request.period_hours}")
    
    try:
        config = MongoConnectionConfig()
        client = get_client(config.uri)
        analyzer = MongoDBQueryAnalyzer(client)
        
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
        config = MongoConnectionConfig()
        client = get_client(config.uri)
        exporter = MongoDBMetricsExporter(client)
        
        metrics = exporter.get_prometheus_metrics()
        
        return metrics, 200, {"Content-Type": "text/plain"}
    
    except Exception as e:
        obs.log_error(f"get_prometheus_metrics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/json", summary="Get metrics in JSON format")
async def get_json_metrics():
    obs.log_info("get_json_metrics")
    
    try:
        config = MongoConnectionConfig()
        client = get_client(config.uri)
        exporter = MongoDBMetricsExporter(client)
        
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
        performance = client.collector.get_collection_performance(collection_name, period_minutes)
        
        return {
            "success": True,
            "data": {
                "collection": collection_name,
                "period_minutes": period_minutes,
                "performance": performance
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_collection_performance failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index-gaps", summary="Identify index optimization opportunities")
async def get_index_gaps():
    obs.log_info("get_index_gaps")
    
    try:
        client = get_monitoring_client()
        gaps = client.collector.identify_index_gaps()
        
        return {
            "success": True,
            "data": {
                "index_gaps": gaps,
                "count": len(gaps)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_index_gaps failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

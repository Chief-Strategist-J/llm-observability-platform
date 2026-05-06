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
from infrastructure.database.neo4j.client.neo4j_client import get_driver, Neo4jConnectionConfig
from .neo4j_monitoring_client import Neo4jMonitoringClient
from .neo4j_query_analyzer import Neo4jQueryAnalyzer
from .neo4j_metrics_exporter import Neo4jMetricsExporter


router = APIRouter(prefix="/neo4j/queries", tags=["neo4j-query-monitoring"])
obs = ObservabilityClient(service_name="neo4j-query-monitoring-api")


class QueryExecutionRequest(BaseModel):
    query: str = Field(..., description="Neo4j Cypher query to execute")
    params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")


class QueryAnalysisRequest(BaseModel):
    query: str = Field(..., description="Neo4j Cypher query to analyze")
    database: str = Field("neo4j", description="Database name")


class PerformanceReportRequest(BaseModel):
    database: str = Field("neo4j", description="Database name")
    period_hours: int = Field(24, description="Report period in hours")


class SlowQueryRequest(BaseModel):
    threshold_ms: float = Field(1000.0, description="Slow query threshold in milliseconds")
    limit: int = Field(50, description="Maximum number of results")


def get_monitoring_client() -> Neo4jMonitoringClient:
    try:
        config = Neo4jConnectionConfig()
        driver = get_driver(config)
        monitoring_config = QueryMonitoringConfig()
        return Neo4jMonitoringClient(driver, monitoring_config)
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
        config = Neo4jConnectionConfig()
        driver = get_driver(config)
        analyzer = Neo4jQueryAnalyzer(driver)
        
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
    query: str = Query(..., description="Cypher query to explain"),
    database: str = Query("neo4j", description="Database name")
):
    obs.log_info(f"explain_query database={database}")
    
    try:
        config = Neo4jConnectionConfig()
        driver = get_driver(config)
        analyzer = Neo4jQueryAnalyzer(driver)
        
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
        config = Neo4jConnectionConfig()
        driver = get_driver(config)
        analyzer = Neo4jQueryAnalyzer(driver)
        
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
        config = Neo4jConnectionConfig()
        driver = get_driver(config)
        analyzer = Neo4jQueryAnalyzer(driver)
        
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
        config = Neo4jConnectionConfig()
        driver = get_driver(config)
        exporter = Neo4jMetricsExporter(driver)
        
        metrics = exporter.get_prometheus_metrics()
        
        return metrics, 200, {"Content-Type": "text/plain"}
    
    except Exception as e:
        obs.log_error(f"get_prometheus_metrics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/json", summary="Get metrics in JSON format")
async def get_json_metrics():
    obs.log_info("get_json_metrics")
    
    try:
        config = Neo4jConnectionConfig()
        driver = get_driver(config)
        exporter = Neo4jMetricsExporter(driver)
        
        metrics = exporter.export_json_metrics()
        
        return {
            "success": True,
            "data": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_json_metrics failed: {e}")
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
async def get_schema_info(database: str = Query("neo4j", description="Database name")):
    obs.log_info(f"get_schema_info database={database}")
    
    try:
        config = Neo4jConnectionConfig()
        driver = get_driver(config)
        analyzer = Neo4jQueryAnalyzer(driver)
        
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
    query: str = Query(..., description="Cypher query to analyze"),
    database: str = Query("neo4j", description="Database name")
):
    obs.log_info(f"get_query_plan_analysis database={database}")
    
    try:
        config = Neo4jConnectionConfig()
        driver = get_driver(config)
        analyzer = Neo4jQueryAnalyzer(driver)
        
        analysis = analyzer.get_query_plan_analysis(query, database)
        
        return {
            "success": True,
            "data": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_query_plan_analysis failed: {e}")
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


@router.get("/query-types/performance", summary="Get performance by query type")
async def get_query_type_performance(
    period_minutes: int = Query(60, description="Performance period in minutes")
):
    obs.log_info(f"get_query_type_performance period_minutes={period_minutes}")
    
    try:
        client = get_monitoring_client()
        metrics = client.collector.collect_query_metrics(limit=1000)
        
        from datetime import timedelta
        period_start = datetime.utcnow() - timedelta(minutes=period_minutes)
        recent_metrics = [m for m in metrics if m.timestamp >= period_start]
        
        query_type_stats = {}
        for metric in recent_metrics:
            query_type = metric.query_type or "unknown"
            if query_type not in query_type_stats:
                query_type_stats[query_type] = {
                    "count": 0,
                    "total_time": 0,
                    "avg_time": 0,
                    "max_time": 0,
                    "slow_count": 0
                }
            
            stats = query_type_stats[query_type]
            stats["count"] += 1
            stats["total_time"] += metric.execution_time_ms
            stats["max_time"] = max(stats["max_time"], metric.execution_time_ms)
            
            if metric.performance_level in ["slow", "critical"]:
                stats["slow_count"] += 1
        
        for query_type, stats in query_type_stats.items():
            if stats["count"] > 0:
                stats["avg_time"] = stats["total_time"] / stats["count"]
                stats["slow_percentage"] = (stats["slow_count"] / stats["count"]) * 100
        
        return {
            "success": True,
            "data": {
                "period_minutes": period_minutes,
                "query_type_performance": query_type_stats
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"get_query_type_performance failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

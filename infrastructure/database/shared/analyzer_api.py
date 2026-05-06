import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.observability.scripts.observability_client import ObservabilityClient


router = APIRouter(prefix="/analyzer", tags=["database-query-analyzer"])
obs = ObservabilityClient(service_name="database-query-analyzer-api")


class CrossDatabaseAnalysisRequest(BaseModel):
    query: str = Field(..., description="Query to analyze across databases")
    databases: List[str] = Field(["mongodb", "neo4j", "postgres"], description="Databases to analyze")


class PerformanceComparisonRequest(BaseModel):
    period_hours: int = Field(24, description="Comparison period in hours")
    databases: List[str] = Field(["mongodb", "neo4j", "postgres"], description="Databases to compare")


class OptimizationReportRequest(BaseModel):
    databases: List[str] = Field(["mongodb", "neo4j", "postgres"], description="Databases to include")
    include_recommendations: bool = Field(True, description="Include optimization recommendations")


@router.post("/cross-database/analyze", summary="Analyze query across multiple databases")
async def cross_database_analysis(request: CrossDatabaseAnalysisRequest):
    obs.log_info(f"cross_database_analysis databases={request.databases}")
    
    try:
        results = {}
        
        for database in request.databases:
            try:
                if database == "mongodb":
                    result = await _analyze_mongodb_query(request.query)
                elif database == "neo4j":
                    result = await _analyze_neo4j_query(request.query)
                elif database == "postgres":
                    result = await _analyze_postgres_query(request.query)
                elif database == "cassandra":
                    result = await _analyze_cassandra_query(request.query)
                elif database == "redis":
                    result = await _analyze_redis_query(request.query)
                elif database == "qdrant":
                    result = await _analyze_qdrant_query(request.query)
                else:
                    continue
                
                results[database] = result
            except Exception as e:
                results[database] = {"error": str(e)}
        
        comparison = _compare_database_results(results)
        
        return {
            "success": True,
            "data": {
                "query": request.query,
                "database_results": results,
                "comparison": comparison
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"cross_database_analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/performance/comparison", summary="Compare performance across databases")
async def performance_comparison(request: PerformanceComparisonRequest):
    obs.log_info(f"performance_comparison databases={request.databases} period_hours={request.period_hours}")
    
    try:
        results = {}
        
        for database in request.databases:
            try:
                if database == "mongodb":
                    result = await _get_mongodb_performance_summary(request.period_hours)
                elif database == "neo4j":
                    result = await _get_neo4j_performance_summary(request.period_hours)
                elif database == "postgres":
                    result = await _get_postgres_performance_summary(request.period_hours)
                elif database == "cassandra":
                    result = await _get_cassandra_performance_summary(request.period_hours)
                elif database == "redis":
                    result = await _get_redis_performance_summary(request.period_hours)
                elif database == "qdrant":
                    result = await _get_qdrant_performance_summary(request.period_hours)
                else:
                    continue
                
                results[database] = result
            except Exception as e:
                results[database] = {"error": str(e)}
        
        comparison = _compare_performance_metrics(results)
        
        return {
            "success": True,
            "data": {
                "period_hours": request.period_hours,
                "database_performance": results,
                "comparison": comparison
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"performance_comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimization/report", summary="Generate comprehensive optimization report")
async def optimization_report(request: OptimizationReportRequest):
    obs.log_info(f"optimization_report databases={request.databases}")
    
    try:
        results = {}
        
        for database in request.databases:
            try:
                if database == "mongodb":
                    result = await _get_mongodb_optimization_report()
                elif database == "neo4j":
                    result = await _get_neo4j_optimization_report()
                elif database == "postgres":
                    result = await _get_postgres_optimization_report()
                elif database == "cassandra":
                    result = await _get_cassandra_optimization_report()
                elif database == "redis":
                    result = await _get_redis_optimization_report()
                elif database == "qdrant":
                    result = await _get_qdrant_optimization_report()
                else:
                    continue
                
                results[database] = result
            except Exception as e:
                results[database] = {"error": str(e)}
        
        overall_recommendations = _generate_overall_recommendations(results)
        
        return {
            "success": True,
            "data": {
                "database_reports": results,
                "overall_recommendations": overall_recommendations,
                "summary": _generate_optimization_summary(results)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"optimization_report failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/overview", summary="Get overall database health overview")
async def health_overview():
    obs.log_info("health_overview")
    
    try:
        databases = ["mongodb", "neo4j", "postgres", "cassandra", "redis", "qdrant"]
        health_status = {}
        
        for database in databases:
            try:
                if database == "mongodb":
                    status = await _get_mongodb_health()
                elif database == "neo4j":
                    status = await _get_neo4j_health()
                elif database == "postgres":
                    status = await _get_postgres_health()
                elif database == "cassandra":
                    status = await _get_cassandra_health()
                elif database == "redis":
                    status = await _get_redis_health()
                elif database == "qdrant":
                    status = await _get_qdrant_health()
                else:
                    continue
                
                health_status[database] = status
            except Exception as e:
                health_status[database] = {"healthy": False, "error": str(e)}
        
        overall_health = _calculate_overall_health(health_status)
        
        return {
            "success": True,
            "data": {
                "individual_health": health_status,
                "overall_health": overall_health
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"health_overview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/aggregated", summary="Get aggregated metrics across databases")
async def aggregated_metrics(
    period_minutes: int = Query(60, description="Metrics period in minutes")
):
    obs.log_info(f"aggregated_metrics period_minutes={period_minutes}")
    
    try:
        databases = ["mongodb", "neo4j", "postgres", "cassandra", "redis", "qdrant"]
        metrics = {}
        
        for database in databases:
            try:
                if database == "mongodb":
                    db_metrics = await _get_mongodb_metrics(period_minutes)
                elif database == "neo4j":
                    db_metrics = await _get_neo4j_metrics(period_minutes)
                elif database == "postgres":
                    db_metrics = await _get_postgres_metrics(period_minutes)
                elif database == "cassandra":
                    db_metrics = await _get_cassandra_metrics(period_minutes)
                elif database == "redis":
                    db_metrics = await _get_redis_metrics(period_minutes)
                elif database == "qdrant":
                    db_metrics = await _get_qdrant_metrics(period_minutes)
                else:
                    continue
                
                metrics[database] = db_metrics
            except Exception as e:
                metrics[database] = {"error": str(e)}
        
        aggregated = _aggregate_metrics(metrics)
        
        return {
            "success": True,
            "data": {
                "period_minutes": period_minutes,
                "individual_metrics": metrics,
                "aggregated_metrics": aggregated
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        obs.log_error(f"aggregated_metrics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _analyze_mongodb_query(query: str) -> Dict[str, Any]:
    try:
        from infrastructure.database.mongodb.api.query_monitoring_api import analyze_query
        from infrastructure.database.shared.query_monitoring_interfaces import QueryAnalysisRequest
        
        request = QueryAnalysisRequest(query=query, database="scaibu_default")
        result = await analyze_query(request)
        
        return result.get("data", {})
    except:
        return {"error": "MongoDB analysis not available"}


async def _analyze_neo4j_query(query: str) -> Dict[str, Any]:
    try:
        from infrastructure.database.neo4j.api.query_monitoring_api import analyze_query
        from infrastructure.database.shared.query_monitoring_interfaces import QueryAnalysisRequest
        
        request = QueryAnalysisRequest(query=query, database="neo4j")
        result = await analyze_query(request)
        
        return result.get("data", {})
    except:
        return {"error": "Neo4j analysis not available"}


async def _analyze_postgres_query(query: str) -> Dict[str, Any]:
    try:
        from infrastructure.database.postgres.api.query_monitoring_api import analyze_query
        from infrastructure.database.shared.query_monitoring_interfaces import QueryAnalysisRequest
        
        request = QueryAnalysisRequest(query=query, database="scaibu_default")
        result = await analyze_query(request)
        
        return result.get("data", {})
    except:
        return {"error": "PostgreSQL analysis not available"}


async def _analyze_cassandra_query(query: str) -> Dict[str, Any]:
    try:
        from infrastructure.database.cassandra.api.query_monitoring_api import analyze_query
        from infrastructure.database.shared.query_monitoring_interfaces import QueryAnalysisRequest
        
        request = QueryAnalysisRequest(query=query, database="cassandra")
        result = await analyze_query(request)
        
        return result.get("data", {})
    except:
        return {"error": "Cassandra analysis not available"}


async def _analyze_redis_query(query: str) -> Dict[str, Any]:
    try:
        from infrastructure.database.redis.api.query_monitoring_api import analyze_query
        from infrastructure.database.shared.query_monitoring_interfaces import QueryAnalysisRequest
        
        request = QueryAnalysisRequest(query=query, database="redis")
        result = await analyze_query(request)
        
        return result.get("data", {})
    except:
        return {"error": "Redis analysis not available"}


async def _analyze_qdrant_query(query: str) -> Dict[str, Any]:
    try:
        from infrastructure.database.qdrant.api.query_monitoring_api import analyze_query
        from infrastructure.database.shared.query_monitoring_interfaces import QueryAnalysisRequest
        
        request = QueryAnalysisRequest(query=query, database="qdrant")
        result = await analyze_query(request)
        
        return result.get("data", {})
    except:
        return {"error": "Qdrant analysis not available"}


async def _get_mongodb_performance_summary(period_hours: int) -> Dict[str, Any]:
    try:
        from infrastructure.database.mongodb.api.query_monitoring_api import get_query_performance
        
        period_minutes = period_hours * 60
        result = await get_query_performance(period_minutes=period_minutes)
        
        return result.get("data", {})
    except:
        return {"error": "MongoDB performance not available"}


async def _get_neo4j_performance_summary(period_hours: int) -> Dict[str, Any]:
    try:
        from infrastructure.database.neo4j.api.query_monitoring_api import get_query_performance
        
        period_minutes = period_hours * 60
        result = await get_query_performance(period_minutes=period_minutes)
        
        return result.get("data", {})
    except:
        return {"error": "Neo4j performance not available"}


async def _get_postgres_performance_summary(period_hours: int) -> Dict[str, Any]:
    try:
        from infrastructure.database.postgres.api.query_monitoring_api import get_query_performance
        
        period_minutes = period_hours * 60
        result = await get_query_performance(period_minutes=period_minutes)
        
        return result.get("data", {})
    except:
        return {"error": "PostgreSQL performance not available"}


async def _get_cassandra_performance_summary(period_hours: int) -> Dict[str, Any]:
    try:
        from infrastructure.database.cassandra.api.query_monitoring_api import get_query_performance
        
        period_minutes = period_hours * 60
        result = await get_query_performance(period_minutes=period_minutes)
        
        return result.get("data", {})
    except:
        return {"error": "Cassandra performance not available"}


async def _get_redis_performance_summary(period_hours: int) -> Dict[str, Any]:
    try:
        from infrastructure.database.redis.api.query_monitoring_api import get_query_performance
        
        period_minutes = period_hours * 60
        result = await get_query_performance(period_minutes=period_minutes)
        
        return result.get("data", {})
    except:
        return {"error": "Redis performance not available"}


async def _get_qdrant_performance_summary(period_hours: int) -> Dict[str, Any]:
    try:
        from infrastructure.database.qdrant.api.query_monitoring_api import get_query_performance
        
        period_minutes = period_hours * 60
        result = await get_query_performance(period_minutes=period_minutes)
        
        return result.get("data", {})
    except:
        return {"error": "Qdrant performance not available"}


async def _get_mongodb_optimization_report() -> Dict[str, Any]:
    try:
        from infrastructure.database.mongodb.api.query_monitoring_api import identify_performance_issues
        
        result = await identify_performance_issues()
        return result.get("data", {})
    except:
        return {"error": "MongoDB optimization report not available"}


async def _get_neo4j_optimization_report() -> Dict[str, Any]:
    try:
        from infrastructure.database.neo4j.api.query_monitoring_api import identify_performance_issues
        
        result = await identify_performance_issues()
        return result.get("data", {})
    except:
        return {"error": "Neo4j optimization report not available"}


async def _get_postgres_optimization_report() -> Dict[str, Any]:
    try:
        from infrastructure.database.postgres.api.query_monitoring_api import identify_performance_issues
        
        result = await identify_performance_issues()
        return result.get("data", {})
    except:
        return {"error": "PostgreSQL optimization report not available"}


async def _get_cassandra_optimization_report() -> Dict[str, Any]:
    try:
        from infrastructure.database.cassandra.api.query_monitoring_api import identify_performance_issues
        
        result = await identify_performance_issues()
        return result.get("data", {})
    except:
        return {"error": "Cassandra optimization report not available"}


async def _get_redis_optimization_report() -> Dict[str, Any]:
    try:
        from infrastructure.database.redis.api.query_monitoring_api import identify_performance_issues
        
        result = await identify_performance_issues()
        return result.get("data", {})
    except:
        return {"error": "Redis optimization report not available"}


async def _get_qdrant_optimization_report() -> Dict[str, Any]:
    try:
        from infrastructure.database.qdrant.api.query_monitoring_api import identify_performance_issues
        
        result = await identify_performance_issues()
        return result.get("data", {})
    except:
        return {"error": "Qdrant optimization report not available"}


async def _get_mongodb_health() -> Dict[str, Any]:
    try:
        from infrastructure.database.mongodb.api.query_monitoring_api import get_database_health_report
        
        result = await get_database_health_report()
        return result.get("data", {})
    except:
        return {"healthy": False, "error": "MongoDB health check not available"}


async def _get_neo4j_health() -> Dict[str, Any]:
    try:
        from infrastructure.database.neo4j.api.query_monitoring_api import get_database_health_report
        
        result = await get_database_health_report()
        return result.get("data", {})
    except:
        return {"healthy": False, "error": "Neo4j health check not available"}


async def _get_postgres_health() -> Dict[str, Any]:
    try:
        from infrastructure.database.postgres.api.query_monitoring_api import get_database_health_report
        
        result = await get_database_health_report()
        return result.get("data", {})
    except:
        return {"healthy": False, "error": "PostgreSQL health check not available"}


async def _get_cassandra_health() -> Dict[str, Any]:
    try:
        from infrastructure.database.cassandra.api.query_monitoring_api import get_database_health_report
        
        result = await get_database_health_report()
        return result.get("data", {})
    except:
        return {"healthy": False, "error": "Cassandra health check not available"}


async def _get_redis_health() -> Dict[str, Any]:
    try:
        from infrastructure.database.redis.api.query_monitoring_api import get_database_health_report
        
        result = await get_database_health_report()
        return result.get("data", {})
    except:
        return {"healthy": False, "error": "Redis health check not available"}


async def _get_qdrant_health() -> Dict[str, Any]:
    try:
        from infrastructure.database.qdrant.api.query_monitoring_api import get_database_health_report
        
        result = await get_database_health_report()
        return result.get("data", {})
    except:
        return {"healthy": False, "error": "Qdrant health check not available"}


async def _get_mongodb_metrics(period_minutes: int) -> Dict[str, Any]:
    try:
        from infrastructure.database.mongodb.api.query_monitoring_api import get_json_metrics
        
        result = await get_json_metrics()
        return result.get("data", {})
    except:
        return {"error": "MongoDB metrics not available"}


async def _get_neo4j_metrics(period_minutes: int) -> Dict[str, Any]:
    try:
        from infrastructure.database.neo4j.api.query_monitoring_api import get_json_metrics
        
        result = await get_json_metrics()
        return result.get("data", {})
    except:
        return {"error": "Neo4j metrics not available"}


async def _get_postgres_metrics(period_minutes: int) -> Dict[str, Any]:
    try:
        from infrastructure.database.postgres.api.query_monitoring_api import get_json_metrics
        
        result = await get_json_metrics()
        return result.get("data", {})
    except:
        return {"error": "PostgreSQL metrics not available"}


async def _get_cassandra_metrics(period_minutes: int) -> Dict[str, Any]:
    try:
        from infrastructure.database.cassandra.api.query_monitoring_api import get_json_metrics
        
        result = await get_json_metrics()
        return result.get("data", {})
    except:
        return {"error": "Cassandra metrics not available"}


async def _get_redis_metrics(period_minutes: int) -> Dict[str, Any]:
    try:
        from infrastructure.database.redis.api.query_monitoring_api import get_json_metrics
        
        result = await get_json_metrics()
        return result.get("data", {})
    except:
        return {"error": "Redis metrics not available"}


async def _get_qdrant_metrics(period_minutes: int) -> Dict[str, Any]:
    try:
        from infrastructure.database.qdrant.api.query_monitoring_api import get_json_metrics
        
        result = await get_json_metrics()
        return result.get("data", {})
    except:
        return {"error": "Qdrant metrics not available"}


def _compare_database_results(results: Dict[str, Any]) -> Dict[str, Any]:
    comparison = {
        "performance_scores": {},
        "recommendations": {},
        "optimization_potential": {}
    }
    
    for database, result in results.items():
        if "error" not in result:
            comparison["performance_scores"][database] = result.get("performance_score", 0)
            comparison["recommendations"][database] = result.get("recommendations", [])
            comparison["optimization_potential"][database] = result.get("optimization_potential", "unknown")
    
    return comparison


def _compare_performance_metrics(results: Dict[str, Any]) -> Dict[str, Any]:
    comparison = {
        "total_queries": {},
        "slow_queries": {},
        "avg_execution_time": {},
        "error_rates": {}
    }
    
    for database, result in results.items():
        if "error" not in result and "summary" in result:
            summary = result["summary"]
            comparison["total_queries"][database] = summary.get("total_queries", 0)
            comparison["slow_queries"][database] = summary.get("slow_query_count", 0)
            comparison["avg_execution_time"][database] = summary.get("avg_execution_time_ms", 0)
            comparison["error_rates"][database] = summary.get("error_rate", 0)
    
    return comparison


def _generate_overall_recommendations(results: Dict[str, Any]) -> List[str]:
    recommendations = []
    
    all_issues = []
    for database, result in results.items():
        if "error" not in result and "issues" in result:
            all_issues.extend(result["issues"])
    
    critical_count = len([i for i in all_issues if i.get("severity") == "critical"])
    high_count = len([i for i in all_issues if i.get("severity") == "high"])
    
    if critical_count > 0:
        recommendations.append(f"Address {critical_count} critical performance issues immediately")
    
    if high_count > 5:
        recommendations.append(f"Multiple high-priority issues detected across databases")
    
    slow_query_databases = len([db for db, result in results.items() 
                               if "error" not in result and result.get("summary", {}).get("slow_query_percentage", 0) > 10])
    
    if slow_query_databases > 1:
        recommendations.append("Multiple databases showing high slow query rates")
    
    return recommendations


def _generate_optimization_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    summary = {
        "total_issues": 0,
        "critical_issues": 0,
        "high_issues": 0,
        "databases_analyzed": len(results),
        "healthy_databases": 0
    }
    
    for database, result in results.items():
        if "error" not in result:
            if "issues" in result:
                issues = result["issues"]
                summary["total_issues"] += len(issues)
                summary["critical_issues"] += len([i for i in issues if i.get("severity") == "critical"])
                summary["high_issues"] += len([i for i in issues if i.get("severity") == "high"])
            
            if result.get("health", {}).get("healthy", False):
                summary["healthy_databases"] += 1
    
    return summary


def _calculate_overall_health(health_status: Dict[str, Any]) -> Dict[str, Any]:
    healthy_count = len([db for db, status in health_status.items() if status.get("healthy", False)])
    total_databases = len(health_status)
    
    if healthy_count == total_databases:
        overall_status = "healthy"
        score = 100
    elif healthy_count >= total_databases * 0.5:
        overall_status = "degraded"
        score = 60
    else:
        overall_status = "critical"
        score = 30
    
    return {
        "status": overall_status,
        "score": score,
        "healthy_databases": healthy_count,
        "total_databases": total_databases
    }


def _aggregate_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    aggregated = {
        "total_queries": 0,
        "total_slow_queries": 0,
        "avg_execution_time": 0,
        "total_errors": 0
    }
    
    total_execution_time = 0
    database_count = 0
    
    for database, db_metrics in metrics.items():
        if "error" not in db_metrics and "query_metrics" in db_metrics:
            query_metrics = db_metrics["query_metrics"]
            summary = query_metrics.get("summary", {})
            
            aggregated["total_queries"] += summary.get("total_queries", 0)
            aggregated["total_slow_queries"] += summary.get("slow_query_count", 0)
            aggregated["total_errors"] += summary.get("error_rate", 0) * summary.get("total_queries", 0) / 100
            
            if summary.get("avg_execution_time_ms", 0) > 0:
                total_execution_time += summary["avg_execution_time_ms"]
                database_count += 1
    
    if database_count > 0:
        aggregated["avg_execution_time"] = total_execution_time / database_count
    
    return aggregated

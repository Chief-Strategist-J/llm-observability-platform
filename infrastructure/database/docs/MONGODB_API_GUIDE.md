# MongoDB Query Monitoring API Guide

## 📊 Overview

MongoDB query monitoring provides comprehensive performance tracking, analysis, and optimization recommendations for MongoDB databases.

## 🏗️ Architecture Flow

```mermaid
graph TB
    Client[Client Application] --> API[MongoDB API]
    
    API --> Monitor[Monitoring Client]
    API --> Collector[Query Collector]
    API --> Analyzer[Query Analyzer]
    API --> Exporter[Metrics Exporter]
    
    Monitor --> MongoDB[MongoDB Database]
    Collector --> MongoDB
    Analyzer --> MongoDB
    Exporter --> MongoDB
    
    Collector --> Store[Metrics Store]
    Exporter --> Prometheus[Prometheus Metrics]
    Exporter --> JSON[JSON Export]
    
    API --> Response[API Response]
```

## 📋 Database Schema

### Query Metrics Collection
```javascript
// MongoDB Collections
db.query_metrics {
  _id: ObjectId,
  query_hash: String,           // Unique query identifier
  query_type: String,           // find, aggregate, update, etc.
  database: String,             // Database name
  collection: String,           // Collection name
  execution_time_ms: Number,    // Execution time in milliseconds
  status: String,               // success, error
  performance_level: String,    // fast, normal, slow, critical
  timestamp: Date,              // Query execution timestamp
  affected_rows: Number,        // Number of documents affected
  error_message: String,       // Error message if any
  plan_details: {              // Query execution plan
    explain: Object,
    indexes_used: Array,
    scan_type: String
  }
}

// Performance Reports
db.performance_reports {
  _id: ObjectId,
  database: String,
  period_start: Date,
  period_end: Date,
  total_queries: Number,
  slow_queries: Number,
  avg_execution_time_ms: Number,
  performance_distribution: {
    fast: Number,
    normal: Number,
    slow: Number,
    critical: Number
  },
  top_slow_queries: Array,
  recommendations: Array,
  created_at: Date
}

// Index Analysis
db.index_analysis {
  _id: ObjectId,
  collection: String,
  index_name: String,
  usage_count: Number,
  last_used: Date,
  efficiency_score: Number,
  recommendations: Array
}
```

## 🔗 API Endpoints (15 Total)

### 1. Query Execution with Monitoring
```http
POST /mongodb/queries/execute
Content-Type: application/json

{
  "query": "db.users.find({status: 'active'})",
  "collection": "users",
  "params": {}
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "result": [
      {"_id": "1", "name": "John", "status": "active"}
    ],
    "execution_time_ms": 45.5,
    "performance_level": "FAST",
    "query_hash": "abc123def456",
    "affected_rows": 1
  },
  "timestamp": "2026-05-06T16:13:00.000Z"
}
```

### 2. Get Slow Queries
```http
GET /mongodb/queries/slow?threshold_ms=1000&limit=50
```

**Response:**
```json
{
  "success": true,
  "data": {
    "slow_queries": [
      {
        "query_hash": "slow123",
        "query_type": "aggregate",
        "collection": "orders",
        "execution_time_ms": 1500.0,
        "performance_level": "SLOW",
        "timestamp": "2026-05-06T15:30:00.000Z",
        "plan_details": {
          "explain": {...},
          "indexes_used": [],
          "scan_type": "COLLSCAN"
        }
      }
    ],
    "count": 1,
    "threshold_ms": 1000
  }
}
```

### 3. Query Performance Summary
```http
GET /mongodb/queries/performance?period_minutes=60
```

**Response:**
```json
{
  "success": true,
  "data": {
    "period_minutes": 60,
    "summary": {
      "total_queries": 1250,
      "avg_execution_time_ms": 85.5,
      "slow_query_count": 25,
      "slow_query_percentage": 2.0,
      "error_rate": 0.8,
      "performance_distribution": {
        "fast": 950,
        "normal": 275,
        "slow": 25,
        "critical": 0
      }
    },
    "health": {
      "healthy": true,
      "health_score": 85
    },
    "recommendations": [
      "Consider adding index on status field for users collection"
    ]
  }
}
```

### 4. Query Analysis
```http
POST /mongodb/queries/analyze
Content-Type: application/json

{
  "query": "db.users.find({email: 'test@example.com'})",
  "database": "scaibu_default"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query_hash": "xyz789",
    "query_text": "db.users.find({email: 'test@example.com'})",
    "performance_score": 75.0,
    "recommendations": [
      "Consider adding index on email field",
      "Query uses equality match - good candidate for indexing"
    ],
    "suggested_indexes": [
      {
        "type": "btree",
        "collection": "users",
        "fields": ["email"],
        "reason": "Query uses email field for filtering"
      }
    ],
    "optimization_potential": "medium",
    "estimated_improvement_percent": 40.0
  }
}
```

### 5. Query Explanation
```http
GET /mongodb/queries/explain?query=db.users.find({status: 'active'})&database=scaibu_default
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "db.users.find({status: 'active'})",
    "database": "scaibu_default",
    "execution_plan": {
      "explain": {
        "queryPlanner": {
          "winningPlan": {
            "stage": "COLLSCAN",
            "filter": {"status": "active"},
            "direction": "forward"
          }
        },
        "executionStats": {
          "executionTimeMillis": 45,
          "totalDocsExamined": 1000,
          "totalDocsReturned": 250
        }
      }
    }
  }
}
```

### 6. Index Suggestions
```http
POST /mongodb/queries/indexes/suggest
Content-Type: application/json

{
  "query": "db.orders.find({user_id: 123, status: 'completed'})",
  "database": "scaibu_default"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "db.orders.find({user_id: 123, status: 'completed'})",
    "database": "scaibu_default",
    "suggested_indexes": [
      {
        "type": "compound",
        "collection": "orders",
        "fields": [
          {"user_id": 1},
          {"status": 1}
        ],
        "reason": "Query filters on multiple fields - compound index recommended"
      },
      {
        "type": "single",
        "collection": "orders", 
        "fields": ["user_id"],
        "reason": "High cardinality field - good for selectivity"
      }
    ]
  }
}
```

### 7. Performance Report
```http
POST /mongodb/queries/reports/performance
Content-Type: application/json

{
  "database": "scaibu_default",
  "period_hours": 24
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "database": "scaibu_default",
    "period_start": "2026-05-05T16:13:00.000Z",
    "period_end": "2026-05-06T16:13:00.000Z",
    "total_queries": 5000,
    "slow_queries": 75,
    "avg_execution_time_ms": 95.5,
    "performance_distribution": {
      "fast": 3500,
      "normal": 1375,
      "slow": 75,
      "critical": 0
    },
    "top_slow_queries": [
      {
        "query_hash": "slow123",
        "query_type": "aggregate",
        "execution_time_ms": 2500.0,
        "timestamp": "2026-05-06T14:30:00.000Z"
      }
    ],
    "recommendations": [
      "Optimize slow aggregation queries",
      "Add indexes for frequently queried fields",
      "Consider query result pagination"
    ]
  }
}
```

### 8. Performance Issues
```http
GET /mongodb/queries/issues
```

**Response:**
```json
{
  "success": true,
  "data": {
    "issues": [
      {
        "type": "slow_query",
        "severity": "high",
        "query_hash": "slow123",
        "query_type": "aggregate",
        "collection": "orders",
        "execution_time_ms": 2500.0,
        "timestamp": "2026-05-06T14:30:00.000Z",
        "recommendation": "Optimize aggregation pipeline or add appropriate indexes"
      },
      {
        "type": "index_gap",
        "severity": "medium",
        "collection": "users",
        "slow_query_count": 15,
        "avg_execution_time": 800.0,
        "recommendation": "Consider adding index on email field"
      }
    ],
    "count": 2,
    "severity_breakdown": {
      "critical": 0,
      "high": 1,
      "medium": 1,
      "low": 0
    }
  }
}
```

### 9. Slow Queries Analysis
```http
GET /mongodb/queries/analysis/slow?hours=24
```

**Response:**
```json
{
  "success": true,
  "data": {
    "period_hours": 24,
    "total_slow_queries": 75,
    "collection_breakdown": {
      "orders": {
        "count": 45,
        "avg_execution_time": 1200.0,
        "max_execution_time": 3000.0
      },
      "users": {
        "count": 20,
        "avg_execution_time": 800.0,
        "max_execution_time": 1500.0
      }
    },
    "top_slow_queries": [
      {
        "query_hash": "slow123",
        "execution_time_ms": 3000.0,
        "timestamp": "2026-05-06T14:30:00.000Z"
      }
    ],
    "trend": "stable"
  }
}
```

### 10. Database Health Report
```http
GET /mongodb/queries/health
```

**Response:**
```json
{
  "success": true,
  "data": {
    "overall_health_score": 85,
    "health_status": "healthy",
    "server_health": {
      "healthy": true,
      "health_score": 90
    },
    "performance_summary": {
      "avg_execution_time_ms": 95.5,
      "slow_query_percentage": 1.5
    },
    "issues": {
      "critical": [],
      "high": [],
      "total_count": 0
    }
  }
}
```

### 11. Prometheus Metrics
```http
GET /mongodb/queries/metrics
```

**Response (text/plain):**
```
# HELP mongodb_query_execution_time_ms MongoDB query execution time
# TYPE mongodb_query_execution_time_ms histogram
mongodb_query_execution_time_ms_bucket{le="10"} 100
mongodb_query_execution_time_ms_bucket{le="100"} 400
mongodb_query_execution_time_ms_bucket{le="1000"} 490
mongodb_query_execution_time_ms_bucket{le="+Inf"} 500
mongodb_query_execution_time_ms_sum 25000
mongodb_query_execution_time_ms_count 500

# HELP mongodb_queries_total Total MongoDB queries
# TYPE mongodb_queries_total counter
mongodb_queries_total{status="success"} 490
mongodb_queries_total{status="error"} 10

# HELP mongodb_slow_queries_total Total slow MongoDB queries
# TYPE mongodb_slow_queries_total counter
mongodb_slow_queries_total 25
```

### 12. JSON Metrics Export
```http
GET /mongodb/queries/metrics/json
```

**Response:**
```json
{
  "success": true,
  "data": {
    "timestamp": "2026-05-06T16:13:00.000Z",
    "database": "mongodb",
    "query_metrics": [
      {
        "query_hash": "abc123",
        "query_type": "find",
        "execution_time_ms": 45.5,
        "performance_level": "FAST",
        "timestamp": "2026-05-06T16:13:00.000Z"
      }
    ],
    "database_metrics": {
      "total_collections": 10,
      "total_indexes": 25,
      "avg_query_time_ms": 95.5
    },
    "health": {
      "healthy": true,
      "health_score": 85
    }
  }
}
```

### 13. Collection Performance
```http
GET /mongodb/queries/collections/{collection_name}/performance?period_minutes=60
```

**Response:**
```json
{
  "success": true,
  "data": {
    "collection": "users",
    "period_minutes": 60,
    "statistics": {
      "total_queries": 250,
      "avg_execution_time_ms": 65.5,
      "slow_query_count": 5,
      "index_usage": {
        "email_index": 150,
        "status_index": 100
      }
    },
    "recommendations": [
      "Consider optimizing queries on large result sets",
      "Review index usage patterns"
    ]
  }
}
```

### 14. Schema Analysis
```http
GET /mongodb/queries/schema/analysis
```

**Response:**
```json
{
  "success": true,
  "data": {
    "schema": {
      "collections": [
        {
          "name": "users",
          "document_count": 10000,
          "avg_document_size": 1024,
          "indexes": [
            {
              "name": "_id_",
              "type": "single",
              "fields": ["_id"]
            },
            {
              "name": "email_1",
              "type": "single",
              "fields": ["email"]
            }
          ]
        }
      ]
    },
    "recommendations": [
      "Consider adding compound index on frequently queried field combinations",
      "Review document size for large collections"
    ]
  }
}
```

### 15. Query Plan Analysis
```http
GET /mongodb/queries/plan/analysis?query=db.users.find({status: 'active'})&database=scaibu_default
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "db.users.find({status: 'active'})",
    "database": "scaibu_default",
    "explain": {
      "queryPlanner": {
        "winningPlan": {
          "stage": "COLLSCAN",
          "filter": {"status": "active"}
        }
      }
    },
    "analysis": {
      "plan_efficiency": {
        "efficiency_score": 60,
        "issues": ["Full collection scan detected"],
        "optimizations": ["Add index on status field"]
      },
      "performance_indicators": {
        "scan_type": "COLLSCAN",
        "indexes_used": [],
        "estimated_docs_examined": 10000
      }
    }
  }
}
```

## 🚀 Usage Examples

### Complete Monitoring Flow
```bash
# 1. Execute query with monitoring
curl -X POST "http://localhost:8000/mongodb/queries/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "db.users.find({status: \"active\"})",
    "collection": "users"
  }'

# 2. Get slow queries
curl "http://localhost:8000/mongodb/queries/slow?threshold_ms=1000&limit=10"

# 3. Analyze query performance
curl -X POST "http://localhost:8000/mongodb/queries/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "db.users.find({email: \"test@example.com\"})",
    "database": "scaibu_default"
  }'

# 4. Get performance report
curl -X POST "http://localhost:8000/mongodb/queries/reports/performance" \
  -H "Content-Type: application/json" \
  -d '{
    "database": "scaibu_default",
    "period_hours": 24
  }'
```

### Python Client Integration
```python
import requests

class MongoDBMonitoringClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def execute_query(self, query: str, collection: str, **kwargs):
        url = f"{self.base_url}/mongodb/queries/execute"
        payload = {"query": query, "collection": collection, **kwargs}
        
        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()
    
    def get_slow_queries(self, threshold_ms: float = 1000, limit: int = 50):
        url = f"{self.base_url}/mongodb/queries/slow"
        params = {"threshold_ms": threshold_ms, "limit": limit}
        
        response = requests.get(url, params=params, headers=self.headers)
        return response.json()
    
    def analyze_query(self, query: str, database: str = "scaibu_default"):
        url = f"{self.base_url}/mongodb/queries/analyze"
        payload = {"query": query, "database": database}
        
        response = requests.post(url, json=payload, headers=self.headers)
        return response.json()

# Usage
client = MongoDBMonitoringClient("http://localhost:8000", "your-api-key")

# Execute query
result = client.execute_query(
    "db.users.find({status: 'active'})",
    "users"
)

# Get slow queries
slow_queries = client.get_slow_queries(threshold_ms=1000, limit=10)

# Analyze query
analysis = client.analyze_query(
    "db.users.find({email: 'test@example.com'})"
)
```

### Real-time Monitoring
```javascript
// WebSocket connection for real-time metrics
const ws = new WebSocket('ws://localhost:8000/mongodb/queries/metrics/stream');

ws.onmessage = function(event) {
    const metrics = JSON.parse(event.data);
    
    // Update dashboard
    updateDashboard(metrics);
    
    // Check for alerts
    if (metrics.slow_query_rate > 0.05) {
        showAlert('High slow query rate detected');
    }
};

function updateDashboard(metrics) {
    document.getElementById('query-count').textContent = metrics.total_queries;
    document.getElementById('avg-time').textContent = metrics.avg_execution_time_ms.toFixed(2);
    document.getElementById('slow-count').textContent = metrics.slow_queries;
}
```

## 📊 Monitoring Dashboard

### Grafana Panel Configuration
```json
{
  "dashboard": {
    "title": "MongoDB Query Monitoring",
    "panels": [
      {
        "title": "Query Execution Time",
        "type": "graph",
        "targets": [
          {
            "expr": "mongodb_query_execution_time_ms_sum",
            "legendFormat": "Execution Time"
          }
        ],
        "yAxes": [
          {
            "label": "Time (ms)",
            "min": 0
          }
        ]
      },
      {
        "title": "Slow Queries Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "mongodb_slow_queries_total / mongodb_queries_total"
          }
        ]
      },
      {
        "title": "Query Distribution",
        "type": "piechart",
        "targets": [
          {
            "expr": "mongodb_queries_total",
            "format": "time_series"
          }
        ]
      },
      {
        "title": "Collection Performance",
        "type": "table",
        "targets": [
          {
            "expr": "mongodb_collection_query_time_ms"
          }
        ]
      }
    ]
  }
}
```

## 🔧 Configuration

### Environment Variables
```bash
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=scaibu_default
MONGODB_USERNAME=admin
MONGODB_PASSWORD=password

# Monitoring Configuration
MONGODB_SLOW_QUERY_THRESHOLD_MS=1000
MONGODB_QUERY_HISTORY_SIZE=10000
MONGODB_METRICS_EXPORT_INTERVAL_SECONDS=30
```

### Docker Setup
```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:6.0
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
      MONGO_INITDB_DATABASE: scaibu_default
    volumes:
      - mongodb_data:/data/db
      - ./init-scripts:/docker-entrypoint-initdb.d

  mongodb-monitoring:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=mongodb://admin:password@mongodb:27017
      - API_KEY=your-secret-api-key
    depends_on:
      - mongodb
    volumes:
      - ./logs:/app/logs

volumes:
  mongodb_data:
```

## 🛡️ Security & Best Practices

### API Security
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

async def verify_api_key(api_key: str = Depends(security)):
    try:
        # Verify JWT token
        payload = jwt.decode(api_key.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@router.post("/execute", dependencies=[Depends(verify_api_key)])
async def execute_query(request: QueryExecutionRequest):
    # Implementation
    pass
```

### Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/slow", dependencies=[limiter.limit("100/minute")])
async def get_slow_queries():
    # Implementation
    pass

@router.post("/execute", dependencies=[limiter.limit("50/minute")])
async def execute_query():
    # Implementation
    pass
```

### Query Validation
```python
from pydantic import BaseModel, validator
import re

class QueryExecutionRequest(BaseModel):
    query: str
    collection: str
    params: Dict[str, Any] = {}
    
    @validator('query')
    def validate_query(cls, v):
        # Basic SQL injection prevention
        dangerous_patterns = [
            r'\$where',
            r'\$eval',
            r'\mapReduce',
            r'\$function'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Query contains potentially dangerous operation: {pattern}")
        
        return v
    
    @validator('collection')
    def validate_collection(cls, v):
        # Collection name validation
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', v):
            raise ValueError("Invalid collection name")
        return v
```

## 📈 Performance Optimization

### Connection Pooling
```python
from pymongo import MongoClient
from pymongo.pool import PoolOptions

# Configure connection pool
pool_options = PoolOptions(
    max_pool_size=50,
    min_pool_size=5,
    max_idle_time_ms=30000,
    wait_queue_timeout_ms=5000,
    connect_timeout_ms=10000
)

client = MongoClient(
    mongodb_uri,
    pool_options=pool_options,
    retryWrites=True,
    w="majority"
)
```

### Query Optimization
```python
# Use aggregation pipeline for complex queries
optimized_query = [
    {"$match": {"status": "active"}},
    {"$project": {"name": 1, "email": 1}},
    {"$sort": {"created_at": -1}},
    {"$limit": 100}
]

# Use indexes effectively
def get_optimized_query(collection: str, filters: Dict[str, Any]):
    # Ensure filters use indexed fields
    indexed_fields = ["_id", "email", "status"]
    optimized_filters = {
        k: v for k, v in filters.items() 
        if k in indexed_fields
    }
    
    return {"$match": optimized_filters}
```

### Caching Strategy
```python
from functools import lru_cache
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

@lru_cache(maxsize=1000)
def get_query_analysis(query_hash: str):
    # Check cache first
    cached_result = redis_client.get(f"query_analysis:{query_hash}")
    if cached_result:
        return json.loads(cached_result)
    
    # Perform analysis
    result = perform_query_analysis(query_hash)
    
    # Cache result
    redis_client.setex(
        f"query_analysis:{query_hash}",
        3600,  # 1 hour TTL
        json.dumps(result)
    )
    
    return result
```

This comprehensive MongoDB API guide provides complete documentation for all 15 endpoints with detailed examples, security considerations, and best practices for production deployment.

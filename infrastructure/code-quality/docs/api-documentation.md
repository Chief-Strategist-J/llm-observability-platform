# SonarQube Quality API Documentation

This API provides comprehensive code quality management capabilities including project management, analysis triggering, status monitoring, and reporting.

## Base URL

```
http://localhost:5000/api/v1
```

## Authentication

The API uses Bearer token authentication for secure access:

```bash
Authorization: Bearer your-api-token
```

## Response Format

All responses follow the standard JSON format:

```json
{
  "data": { ... },
  "error": "Error message (if applicable)",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Endpoints

### Health Checks

#### GET /health
Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "quality-api",
  "version": "1.0.0"
}
```

#### GET /ready
Readiness check including database and SonarQube connectivity.

**Response:**
```json
{
  "status": "ready",
  "database": "connected",
  "sonarqube": "connected"
}
```

### Project Management

#### POST /projects
Create a new project for code quality analysis.

**Request Body:**
```json
{
  "project_key": "my-project",
  "name": "My Project",
  "description": "A sample project",
  "languages": ["python", "javascript", "go"]
}
```

**Response:**
```json
{
  "message": "Project created successfully",
  "project": {
    "key": "my-project",
    "name": "My Project",
    "description": "A sample project",
    "status": "active",
    "languages": ["python", "javascript", "go"],
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

**Error Responses:**
- `400`: Validation failed
- `409`: Project already exists
- `500`: Internal server error

#### GET /projects
List all projects.

**Response:**
```json
{
  "projects": [
    {
      "key": "my-project",
      "name": "My Project",
      "description": "A sample project",
      "status": "active",
      "languages": ["python", "javascript"],
      "created_at": "2024-01-01T00:00:00Z",
      "last_analysis_at": "2024-01-01T12:00:00Z",
      "quality_gate_status": "passed"
    }
  ]
}
```

#### GET /projects/{project_key}
Get details of a specific project.

**Path Parameters:**
- `project_key`: Unique project identifier

**Response:**
```json
{
  "project": {
    "key": "my-project",
    "name": "My Project",
    "description": "A sample project",
    "status": "active",
    "languages": ["python", "javascript"],
    "created_at": "2024-01-01T00:00:00Z",
    "last_analysis_at": "2024-01-01T12:00:00Z",
    "quality_gate_status": "passed"
  }
}
```

**Error Responses:**
- `404`: Project not found

#### GET /projects/{project_key}/report
Generate comprehensive quality report for a project.

**Path Parameters:**
- `project_key`: Unique project identifier

**Query Parameters:**
- `days` (optional): Number of days for report (default: 30, max: 365)

**Response:**
```json
{
  "report": {
    "project": {
      "key": "my-project",
      "name": "My Project",
      "languages": ["python", "javascript"]
    },
    "period": {
      "start": "2023-12-01T00:00:00Z",
      "end": "2024-01-01T00:00:00Z",
      "days": 30
    },
    "summary": {
      "total_analyses": 45,
      "successful_analyses": 42,
      "failed_analyses": 3,
      "average_quality_score": 87.5
    },
    "trends": {
      "trend": "improving",
      "score_change": +5.2,
      "first_score": 82.3,
      "last_score": 87.5
    },
    "quality_metrics": {
      "total_issues": 156,
      "critical_issues": 2,
      "security_issues": 5,
      "average_coverage": 85.2
    },
    "security_analysis": {
      "vulnerabilities": 3,
      "security_hotspots": 2,
      "requires_immediate_attention": false
    },
    "recommendations": [
      "Address 2 critical issues to improve reliability",
      "Continue maintaining current test coverage"
    ]
  }
}
```

### Analysis Management

#### POST /analysis/trigger
Trigger code analysis for a project.

**Request Body:**
```json
{
  "project_key": "my-project",
  "branch": "main",
  "commit_hash": "abc123def456789012345678901234567890abcd"
}
```

**Response:**
```json
{
  "message": "Analysis triggered successfully",
  "analysis_id": "my-project_abc123_20240101_120000",
  "project_key": "my-project",
  "branch": "main",
  "commit_hash": "abc123def456789012345678901234567890abcd"
}
```

**Error Responses:**
- `400`: Validation failed
- `404`: Project not found
- `500`: Internal server error

#### GET /analysis/{analysis_id}/status
Check the status of an analysis.

**Path Parameters:**
- `analysis_id`: Unique analysis identifier

**Response:**
```json
{
  "analysis_id": "my-project_abc123_20240101_120000",
  "project_key": "my-project",
  "branch": "main",
  "commit_hash": "abc123def456789012345678901234567890abcd",
  "status": "completed",
  "created_at": "2024-01-01T12:00:00Z",
  "completed_at": "2024-01-01T12:05:00Z",
  "summary": "Found 15 issues, 85.2% coverage, Quality Score: 87.5/100",
  "quality_score": 87.5,
  "ready_for_merge": true
}
```

**Error Responses:**
- `404`: Analysis not found

#### GET /analysis/{analysis_id}/metrics
Get detailed metrics from an analysis.

**Path Parameters:**
- `analysis_id`: Unique analysis identifier

**Response:**
```json
{
  "analysis_id": "my-project_abc123_20240101_120000",
  "metrics": [
    {
      "name": "coverage",
      "value": 85.2,
      "formatted_value": "85.2%"
    },
    {
      "name": "duplicated_lines_density",
      "value": 3.1,
      "formatted_value": "3.1%"
    },
    {
      "name": "maintainability_rating",
      "value": 1.0,
      "formatted_value": "A"
    },
    {
      "name": "reliability_rating",
      "value": 1.0,
      "formatted_value": "A"
    }
  ]
}
```

#### GET /analysis/{analysis_id}/issues
Get issues from an analysis.

**Path Parameters:**
- `analysis_id`: Unique analysis identifier

**Response:**
```json
{
  "analysis_id": "my-project_abc123_20240101_120000",
  "issues": [
    {
      "key": "ABC123",
      "type": "bug",
      "severity": "major",
      "message": "Potential null pointer dereference",
      "file_path": "src/main.py",
      "line_number": 45,
      "rule": "python:S2259",
      "status": "OPEN",
      "is_blocking": false,
      "is_security_related": false
    },
    {
      "key": "DEF456",
      "type": "vulnerability",
      "severity": "critical",
      "message": "SQL injection vulnerability",
      "file_path": "src/database.py",
      "line_number": 23,
      "rule": "python:S2077",
      "status": "OPEN",
      "is_blocking": true,
      "is_security_related": true
    }
  ],
  "total_issues": 15,
  "blocking_issues": 2,
  "security_issues": 3
}
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Standard endpoints**: 100 requests per minute
- **Analysis endpoints**: 10 requests per minute
- **Report endpoints**: 5 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Error Handling

### Standard Error Response Format

```json
{
  "error": "Error description",
  "details": {
    "field": "validation error details"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### HTTP Status Codes

- `200`: Success
- `201`: Created
- `202`: Accepted (for async operations)
- `400`: Bad Request (validation error)
- `401`: Unauthorized (authentication required)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `409`: Conflict (resource already exists)
- `429`: Too Many Requests (rate limit exceeded)
- `500`: Internal Server Error
- `503`: Service Unavailable

## SDK and Client Libraries

### Python Client

```python
from api.client.sonarqube_client import SonarQubeClient, ProjectRequest, AnalysisRequest

# Initialize client
client = SonarQubeClient("http://localhost:5000", "your-api-token")

# Create project
project = client.create_project(ProjectRequest(
    project_key="my-project",
    name="My Project",
    description="A sample project",
    languages=["python", "javascript"]
))

# Trigger analysis
analysis = client.trigger_analysis(AnalysisRequest(
    project_key="my-project",
    branch="main",
    commit_hash="abc123def456"
))

# Wait for completion
result = client.wait_for_analysis_completion(analysis['analysis_id'])
```

### JavaScript Client

```javascript
class SonarQubeClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl;
        this.apiKey = apiKey;
    }

    async triggerAnalysis(projectKey, branch, commitHash) {
        const response = await fetch(`${this.baseUrl}/analysis/trigger`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify({
                project_key: projectKey,
                branch: branch,
                commit_hash: commitHash
            })
        });
        return response.json();
    }
}
```

## Webhooks

The API supports webhooks for real-time notifications:

### Configure Webhook

```bash
curl -X POST http://localhost:5000/api/v1/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-service.com/webhook",
    "events": ["analysis.completed", "analysis.failed"],
    "secret": "your-webhook-secret"
  }'
```

### Webhook Payload

```json
{
  "event": "analysis.completed",
  "analysis_id": "my-project_abc123_20240101_120000",
  "project_key": "my-project",
  "timestamp": "2024-01-01T12:05:00Z",
  "data": {
    "status": "completed",
    "quality_score": 87.5,
    "ready_for_merge": true
  }
}
```

## Examples

### Complete Analysis Workflow

```bash
# 1. Create project
curl -X POST http://localhost:5000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "my-app",
    "name": "My Application",
    "languages": ["python"]
  }'

# 2. Trigger analysis
curl -X POST http://localhost:5000/api/v1/analysis/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "my-app",
    "branch": "main",
    "commit_hash": "abc123def456"
  }'

# 3. Check status
curl http://localhost:5000/api/v1/analysis/my-app_abc123_20240101_120000/status

# 4. Get report
curl "http://localhost:5000/api/v1/projects/my-app/report?days=7"
```

### Batch Project Analysis

```bash
# Get all projects
curl http://localhost:5000/api/v1/projects | jq -r '.projects[].key' | while read project; do
  echo "Analyzing $project..."
  curl -X POST http://localhost:5000/api/v1/analysis/trigger \
    -H "Content-Type: application/json" \
    -d "{
      \"project_key\": \"$project\",
      \"branch\": \"main\",
      \"commit_hash\": \"latest\"
    }"
done
```

## Support

For API support:
- Check the [Setup Guide](setup-guide.md) for configuration issues
- Review error messages for specific problems
- Consult the troubleshooting section in the documentation

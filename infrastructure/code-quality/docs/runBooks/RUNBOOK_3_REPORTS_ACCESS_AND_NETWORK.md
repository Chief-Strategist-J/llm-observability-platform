# Runbook 3: Reports Access and Network Information

## Overview
This runbook covers how to access SonarQube reports, understand network configuration, and navigate all access points and endpoints for the DTAE SonarQube setup.

## Access Points and URLs

### Primary Access URLs

#### SonarQube Dashboard
- **URL**: http://localhost:9000
- **Purpose**: Main web interface for viewing reports
- **Login**: admin / admin (default)
- **Access**: Web browser

#### Project Dashboard
- **URL**: http://localhost:9000/dashboard?id=distributed-trace-analysis-engine
- **Purpose**: Project-specific analysis results
- **Access**: Web browser (requires login)

#### API Endpoints
- **Base URL**: http://localhost:9000/api
- **Purpose**: Programmatic access to data
- **Authentication**: Token-based

### Network Configuration

#### Docker Network Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Host Machine  │    │ Docker Network   │    │  SonarQube       │
│   localhost:9000│────│ docker_sonarqube │────│  sonarqube:9000  │
│                 │    │     Network      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

#### Network Details
- **Network Name**: `docker_sonarqube_network`
- **Scanner URL**: `http://sonarqube:9000` (internal Docker)
- **Browser URL**: `http://localhost:9000` (host machine)
- **Container Name**: `sonarqube`

#### Port Mapping
- **Host Port**: 9000
- **Container Port**: 9000
- **Protocol**: HTTP

## Dashboard Navigation

### Login Process
1. Open browser to http://localhost:9000
2. Enter credentials:
   - Username: `admin`
   - Password: `admin`
3. Click "Log in"

### Main Dashboard Features

#### 1. Projects Overview
- **Location**: Home page after login
- **Shows**: All projects list with quality gate status
- **Actions**: Click project name to view details

#### 2. Project Dashboard
- **URL**: http://localhost:9000/dashboard?id=distributed-trace-analysis-engine
- **Sections**:
  - **Overview**: Key metrics and quality gate status
  - **Code**: File-by-file analysis results
  - **Issues**: Bugs, vulnerabilities, code smells
  - **Measures**: Detailed metrics and trends

#### 3. Quality Gate Status
- **Indicators**: 
  - ✅ Green: Passed
  - ⚠️ Yellow: Warning
  - ❌ Red: Failed
- **Criteria**: Coverage, reliability, security, maintainability

### Report Sections Explained

#### Overview Tab
```
┌─────────────────────────────────────────────────────────┐
│ Distributed Trace Analysis Engine                        │
│ Quality Gate: PASSED ✅                                 │
├─────────────────┬─────────────────┬─────────────────────┤
│ Coverage        │ 58.27%          │ 581/997 lines       │
│ Bugs            │ 0               │ Best Value ✅        │
│ Vulnerabilities │ 0               │ Best Value ✅        │
│ Code Smells     │ 1               │ Needs Attention ⚠️   │
└─────────────────┴─────────────────┴─────────────────────┘
```

#### Code Tab
- **File Tree**: Navigate source code structure
- **Hotspots**: Security-sensitive code areas
- **Duplication**: Code duplication analysis
- **Coverage**: Line-by-line coverage visualization

#### Issues Tab
- **Bugs**: Critical defects requiring immediate attention
- **Vulnerabilities**: Security issues
- **Code Smells**: Maintainability issues
- **Filtering**: By severity, type, status

#### Measures Tab
- **Metrics**: Lines of code, complexity, coverage
- **Trends**: Historical data and evolution
- **Technical Debt**: Estimated effort to fix issues

## API Access

### Authentication Methods

#### Token Authentication (Recommended)
```bash
# Using token in header
TOKEN="squ_44characterlongtoken..."
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:9000/api/projects/search"

# Using basic auth with token
curl -u "$TOKEN:" "http://localhost:9000/api/projects/search"
```

#### Admin Authentication
```bash
# Using admin credentials
curl -u admin:admin "http://localhost:9000/api/projects/search"
```

### Key API Endpoints

#### Project Management
```bash
# List all projects
curl -u "$TOKEN:" "http://localhost:9000/api/projects/search"

# Get project details
curl -u "$TOKEN:" "http://localhost:9000/api/components/tree?component=distributed-trace-analysis-engine"

# Create project
curl -X POST -u admin:admin \
  "http://localhost:9000/api/projects/create?project=new-project&name=New%20Project"
```

#### Analysis Results
```bash
# Get project measures
curl -u "$TOKEN:" \
  "http://localhost:9000/api/measures/component?component=distributed-trace-analysis-engine&metricKeys=ncloc,complexity,coverage,violations"

# Get issues
curl -u "$TOKEN:" \
  "http://localhost:9000/api/issues/search?componentKeys=distributed-trace-analysis-engine"

# Get analysis status
curl -u "$TOKEN:" \
  "http://localhost:9000/api/ce/task?id=analysis-task-id"
```

#### Quality Gates
```bash
# Get quality gate status
curl -u "$TOKEN:" \
  "http://localhost:9000/api/qualitygates/project_status?projectKey=distributed-trace-analysis-engine"
```

### API Response Examples

#### Project Search Response
```json
{
  "paging": {"pageIndex": 1, "pageSize": 50, "total": 1},
  "components": [
    {
      "key": "distributed-trace-analysis-engine",
      "name": "Distributed Trace Analysis Engine",
      "qualifier": "TRK",
      "measures": [
        {"metric": "coverage", "value": "58.27"},
        {"metric": "violations", "value": "1"}
      ]
    }
  ]
}
```

#### Measures Response
```json
{
  "component": {
    "key": "distributed-trace-analysis-engine",
    "name": "Distributed Trace Analysis Engine",
    "qualifier": "TRK",
    "measures": [
      {"metric": "ncloc", "value": "2184"},
      {"metric": "complexity", "value": "439"},
      {"metric": "coverage", "value": "58.27"},
      {"metric": "bugs", "value": "0", "bestValue": true},
      {"metric": "vulnerabilities", "value": "0", "bestValue": true},
      {"metric": "code_smells", "value": "1"},
      {"metric": "violations", "value": "1"}
    ]
  }
}
```

## Network Troubleshooting

### Connectivity Tests

#### Test Server Availability
```bash
# Test from host
curl -I "http://localhost:9000/api/system/status"

# Expected: HTTP/1.1 200 OK

# Test from Docker container
docker run --rm --network docker_sonarqube_network \
  alpine/curl "http://sonarqube:9000/api/system/status"

# Expected: {"status":"UP"}
```

#### Test Network Configuration
```bash
# List Docker networks
docker network ls | grep sonarqube

# Inspect network
docker network inspect docker_sonarqube_network

# Check container connectivity
docker exec sonarqube netstat -tlnp | grep :9000
```

#### Test Scanner Connectivity
```bash
# Test scanner can reach server
docker run --rm --network docker_sonarqube_network \
  -e SONAR_HOST_URL="http://sonarqube:9000" \
  -e SONAR_TOKEN="$TOKEN" \
  sonarsource/sonar-scanner-cli \
  -Dsonar.projectBaseDir=/tmp \
  -Dsonar.host.url=http://sonarqube:9000
```

### Common Network Issues

#### Issue 1: Scanner Cannot Reach Server
**Symptoms**: 401 Unauthorized or connection refused
**Causes**: Wrong URL, network misconfiguration
**Solutions**:
```bash
# Use correct Docker network URL
SONAR_HOST_URL="http://sonarqube:9000"  # Not localhost:9000

# Ensure scanner is on correct network
docker run --network docker_sonarqube_network ...

# Check network exists
docker network ls | grep sonarqube
```

#### Issue 2: Browser Cannot Access Dashboard
**Symptoms**: Connection refused in browser
**Causes**: Server not running, port blocked
**Solutions**:
```bash
# Check if server is running
docker ps | grep sonarqube

# Check port mapping
docker port sonarqube

# Restart server
make sonar-stop && make sonar-start
```

#### Issue 3: API Returns 401 Unauthorized
**Symptoms**: API calls fail with authentication error
**Causes**: Invalid token, wrong auth method
**Solutions**:
```bash
# Test token validity
curl -u "$TOKEN:" "http://localhost:9000/api/authentication/validate"

# Generate new token
curl -X POST -u admin:admin \
  "http://localhost:9000/api/user_tokens/generate?name=new-token"
```

## Report Generation Workflow

### Real-time Report Updates
```bash
# 1. Run analysis
make sonar-analyze

# 2. Check analysis status
TASK_ID=$(curl -u "$TOKEN:" "http://localhost:9000/api/ce/activity?component=distributed-trace-analysis-engine" | jq -r '.tasks[0].id')

# 3. Monitor processing
curl -u "$TOKEN:" "http://localhost:9000/api/ce/task?id=$TASK_ID"

# 4. Wait for SUCCESS status
# 5. Refresh dashboard
```

### Automated Report Monitoring
```bash
#!/bin/bash
# monitor_analysis.sh

TOKEN="squ_44characterlongtoken..."
PROJECT_KEY="distributed-trace-analysis-engine"

echo "Monitoring analysis for $PROJECT_KEY..."

while true; do
    # Get latest task
    TASK=$(curl -s -u "$TOKEN:" \
        "http://localhost:9000/api/ce/activity?component=$PROJECT_KEY" | \
        jq -r '.tasks[0]')

    STATUS=$(echo $TASK | jq -r '.status')
    EXECUTION_TIME=$(echo $TASK | jq -r '.executionTimeMs')

    echo "Status: $STATUS | Time: ${EXECUTION_TIME}ms"

    if [[ "$STATUS" == "SUCCESS" || "$STATUS" == "FAILED" ]]; then
        echo "Analysis completed with status: $STATUS"
        break
    fi

    sleep 5
done
```

## Access Control and Security

### User Management
```bash
# List users
curl -u admin:admin "http://localhost:9000/api/users/search"

# Create user
curl -X POST -u admin:admin \
  "http://localhost:9000/api/users/create?login=newuser&name=New%20User&password=password123"

# Deactivate user
curl -X POST -u admin:admin \
  "http://localhost:9000/api/users/deactivate?login=newuser"
```

### Permission Management
```bash
# Get project permissions
curl -u admin:admin \
  "http://localhost:9000/api/permissions/search_project_permissions?project=distributed-trace-analysis-engine"

# Grant permission
curl -X POST -u admin:admin \
  "http://localhost:9000/api/permissions/add_user?project=distributed-trace-analysis-engine&login=newuser&permission=user"

# Revoke permission
curl -X POST -u admin:admin \
  "http://localhost:9000/api/permissions/remove_user?project=distributed-trace-analysis-engine&login=newuser"
```

### Token Security
```bash
# List tokens
curl -u admin:admin "http://localhost:9000/api/user_tokens/search"

# Revoke token
curl -X POST -u admin:admin \
  "http://localhost:9000/api/user_tokens/revoke?name=old-token"

# Generate new token
curl -X POST -u admin:admin \
  "http://localhost:9000/api/user_tokens/generate?name=new-token"
```

## Integration Examples

### CI/CD Pipeline Integration
```bash
#!/bin/bash
# ci_sonarqube_integration.sh

# Environment variables
SONAR_HOST_URL="http://sonarqube:9000"
SONAR_TOKEN="$SONAR_TOKEN"
PROJECT_KEY="$CI_PROJECT_NAME"

# Run analysis
make sonar-analyze

# Get quality gate status
QUALITY_GATE=$(curl -u "$SONAR_TOKEN:" \
  "$SONAR_HOST_URL/api/qualitygates/project_status?projectKey=$PROJECT_KEY")

# Check status
STATUS=$(echo $QUALITY_GATE | jq -r '.projectStatus.status')

if [[ "$STATUS" == "ERROR" ]]; then
    echo "Quality gate failed!"
    echo $QUALITY_GATE | jq '.projectStatus.conditions[] | select(.status == "ERROR")'
    exit 1
else
    echo "Quality gate passed: $STATUS"
fi
```

### Slack Notification Integration
```bash
#!/bin/bash
# slack_notification.sh

WEBHOOK_URL="$SLACK_WEBHOOK_URL"
PROJECT_KEY="distributed-trace-analysis-engine"
TOKEN="$SONAR_TOKEN"

# Get analysis results
MEASURES=$(curl -u "$TOKEN:" \
  "http://localhost:9000/api/measures/component?component=$PROJECT_KEY&metricKeys=coverage,violations,bugs,vulnerabilities")

# Extract metrics
COVERAGE=$(echo $MEASURES | jq -r '.component.measures[] | select(.metric=="coverage") | .value')
VIOLATIONS=$(echo $MEASURES | jq -r '.component.measures[] | select(.metric=="violations") | .value')

# Send to Slack
curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"SonarQube Analysis Results for $PROJECT_KEY\\nCoverage: $COVERAGE%\\nViolations: $VIOLATIONS\\n<http://localhost:9000/dashboard?id=$PROJECT_KEY|View Details>\"}" \
  "$WEBHOOK_URL"
```

## Performance Monitoring

### Server Performance Metrics
```bash
# Check server resources
docker stats sonarqube

# Monitor server logs
docker logs -f sonarqube | grep -E "(ERROR|WARN|INFO)"

# Check database connections
docker exec sonarqube curl -s "http://localhost:9000/api/system/health"
```

### Analysis Performance
```bash
# Get analysis duration
curl -u "$TOKEN:" \
  "http://localhost:9000/api/ce/activity?component=distributed-trace-analysis-engine" | \
  jq '.tasks[0] | {status: .status, executionTimeMs: .executionTimeMs}'

# Monitor queue status
curl -u "$TOKEN:" "http://localhost:9000/api/ce/queue"
```

## Quick Reference URLs

### Web Interface
- **Main Dashboard**: http://localhost:9000
- **Project Dashboard**: http://localhost:9000/dashboard?id=distributed-trace-analysis-engine
- **Admin Area**: http://localhost:9000/admin
- **My Account**: http://localhost:9000/account

### API Endpoints
- **Base API**: http://localhost:9000/api
- **Projects**: http://localhost:9000/api/projects/search
- **Measures**: http://localhost:9000/api/measures/component
- **Issues**: http://localhost:9000/api/issues/search
- **Quality Gates**: http://localhost:9000/api/qualitygates

### Network Configuration
- **Docker Network**: docker_sonarqube_network
- **Scanner URL**: http://sonarqube:9000
- **Browser URL**: http://localhost:9000
- **Port**: 9000

## Troubleshooting Checklist

### Before Analysis
- [ ] SonarQube server running (`docker ps | grep sonarqube`)
- [ ] Network accessible (`curl http://localhost:9000/api/system/status`)
- [ ] Token valid (`curl -u "$TOKEN:" http://localhost:9000/api/authentication/validate`)
- [ ] Project exists (`curl -u admin:admin http://localhost:9000/api/projects/search`)

### During Analysis
- [ ] Coverage generated (`ls coverage/cobertura.xml`)
- [ ] Scanner running (`docker ps | grep sonar-scanner`)
- [ ] Network connectivity (`docker network ls | grep sonarqube`)

### After Analysis
- [ ] Results in dashboard (refresh browser)
- [ ] API returns data (`curl -u "$TOKEN:" http://localhost:9000/api/measures/component...`)
- [ ] Quality gate status (`curl -u "$TOKEN:" http://localhost:9000/api/qualitygates/project_status...`)

## Next Steps

After mastering this runbook:
1. 📖 Read **Runbook 4** for dependencies and tools
2. 📖 Read **Runbook 5** for configuration management
3. 📖 Read **Runbook 6** for troubleshooting
4. 🚀 Set up automated monitoring and notifications

## Support

For access and network issues:
1. Check Docker network configuration
2. Verify SonarQube server status
3. Test token authentication
4. Review firewall settings
5. Consult SonarQube server logs

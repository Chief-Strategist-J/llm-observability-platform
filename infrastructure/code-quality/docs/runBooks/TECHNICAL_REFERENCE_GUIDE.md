# SonarQube DTAE - In-Depth Technical Reference Guide

## Overview
This document provides comprehensive technical details, deep-dive explanations, and advanced configurations for the SonarQube DTAE setup. It serves as a complete reference for advanced users, system administrators, and troubleshooting experts.

## Architecture Deep Dive

### System Architecture Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                    Host System (Linux/macOS/WSL2)              │
├─────────────────────────────────────────────────────────────────┤
│  Docker Engine (24.0+)                                         │
│  ├── Docker Network: docker_sonarqube_network                   │
│  ├── Volume Management: Persistent data storage                 │
│  └── Container Orchestration: Docker Compose V2                │
├─────────────────────────────────────────────────────────────────┤
│  SonarQube Ecosystem                                           │
│  ├── SonarQube Server (26.4.0.121862)                        │
│  │   ├── Web Interface (Port 9000)                             │
│  │   ├── REST API v2                                           │
│  │   ├── Analysis Engine                                       │
│  │   └── Quality Gate Engine                                   │
│  ├── PostgreSQL Database (13.x)                                 │
│  │   ├── Project Metadata                                       │
│  │   ├── Analysis Results                                      │
│  │   ├── User Management                                       │
│  │   └── Configuration Store                                   │
│  └── SonarScanner CLI (8.0.1.6346)                            │
│      ├── Analysis Engine                                       │
│      ├── Coverage Integration                                  │
│      ├── Language Sensors                                      │
│      └── Report Generation                                      │
├─────────────────────────────────────────────────────────────────┤
│  Project Analysis Pipeline                                      │
│  ├── Source Code Analysis                                      │
│  ├── Coverage Report Generation                                │
│  ├── Quality Assessment                                         │
│  ├── Rule Evaluation                                           │
│  └── Dashboard Generation                                       │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture
```
1. Source Code → Language Tool → Coverage Report (XML/LCOV)
2. Coverage Report → SonarScanner → Analysis Engine
3. Analysis Engine → Quality Rules → Violations/Issues
4. Violations → Quality Gate → Pass/Fail Decision
5. Results → Database → Dashboard Display
```

## Network Architecture Details

### Docker Network Configuration
```yaml
# Docker Network Specifications
Network Name: docker_sonarqube_network
Driver: bridge
Subnet: 172.18.0.0/16 (auto-assigned)
Gateway: 172.18.0.1 (auto-assigned)

# Container Network Configuration
Container: sonarqube
Network IP: 172.18.0.x (auto-assigned)
Exposed Ports: 9000 (host) → 9000 (container)
Internal DNS: sonarqube (resolves to container IP)

Container: sonarqube_db  
Network IP: 172.18.0.y (auto-assigned)
Exposed Ports: None (internal only)
Internal DNS: sonarqube_db (resolves to container IP)
```

### Port Mapping and Access
```bash
# Port Mapping Table
Host Port    Container Port    Protocol    Purpose
9000        9000              TCP         SonarQube Web UI
5432        5432              TCP         PostgreSQL (internal only)

# Access Patterns
1. Host Browser → http://localhost:9000 → SonarQube Container
2. Scanner Container → http://sonarqube:9000 → SonarQube Container  
3. SonarQube Container → jdbc:postgresql://sonarqube_db:5432 → PostgreSQL Container
```

### Security Zones
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   External      │    │   Docker         │    │   Internal      │
│   Zone          │    │   Network Zone   │    │   Zone          │
│                 │    │                  │    │                 │
│ Host Browser    │───▶│ Port 9000       │───▶│ SonarQube UI    │
│ Scanner CLI     │───▶│ Port 9000       │───▶│ SonarQube API   │
│                 │    │                  │    │                 │
│                 │    │                  │    │ PostgreSQL DB   │
│                 │    │ (No direct       │    │ (Internal only) │
│                 │    │  external access) │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Database Architecture

### PostgreSQL Configuration
```sql
-- Database Configuration
Database Name: sonar
Username: sonar
Password: sonar
Port: 5432
Character Set: UTF8
Collation: en_US.UTF-8

-- Key Tables
projects          -- Project metadata and configuration
project_measures   -- Analysis results and metrics
issues            -- Code quality issues
rules             -- Quality rules definitions
quality_gates     -- Quality gate configurations
users             -- User accounts and permissions
user_tokens       -- Authentication tokens
```

### Data Retention Policies
```sql
-- Analysis Data Retention
Project History: 90 days (default)
Issue History: 30 days (default)
User Activity: 90 days (default)
System Logs: 30 days (default)

-- Storage Estimates per Project
Small Project (<10K LOC): ~50MB/year
Medium Project (10-100K LOC): ~500MB/year  
Large Project (>100K LOC): ~5GB/year
```

## Authentication and Security Architecture

### Token-Based Authentication System
```
Token Generation Flow:
1. Admin Credentials → SonarQube API
2. Token Request → Token Generation Service
3. Token Response → 44-character string
4. Token Storage → Secure configuration

Token Format: squ_[40_random_characters]
Example: squ_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0

Token Security:
- Length: 44 characters (cryptographically secure)
- Prefix: squ_ (user tokens) or sqp_ (project tokens)
- Charset: Alphanumeric only
- Expiration: No expiration (manual revocation required)
- Scope: Project-specific or global based on token type
```

### Permission Model
```
Permission Hierarchy:
1. System Administrator (admin)
   - Global system access
   - User management
   - Quality gate management
   - System configuration

2. Project Administrator
   - Project creation/deletion
   - Project member management
   - Project-specific settings
   - Quality gate assignment

3. Project User
   - View project dashboards
   - Run analysis scans
   - View issues and metrics
   - Basic project operations

4. Scanner Token (squ_)
   - Analysis execution only
   - No UI access
   - Project-scoped permissions
   - API access limited to analysis endpoints
```

## Analysis Engine Deep Dive

### SonarScanner CLI Architecture
```
Scanner Execution Flow:
1. Configuration Loading (sonar-project.properties)
2. Source File Discovery and Indexing
3. Language Sensor Execution
   - Rust Sensor (rust-analyzer integration)
   - Python Sensor (AST analysis)
   - JavaScript Sensor (ESLint integration)
   - Java Sensor (javac integration)
4. Coverage Report Integration
5. Rule Engine Processing
6. Issue Generation
7. Metric Calculation
8. Report Upload to Server
```

### Language Sensor Details

#### Rust Analysis Sensor
```rust
// Rust Sensor Capabilities
- Syntax Analysis: rustc parser integration
- Dependency Analysis: Cargo.toml parsing
- Code Metrics: Cyclomatic complexity, lines of code
- Structural Analysis: Module structure, trait implementations
- Test Coverage Integration: cargo-tarpaulin XML reports
- Clippy Integration: Lint rule integration (when available)

// Analysis Limitations
- No full compiler integration (uses rust-analyzer when available)
- Limited macro expansion analysis
- External crate analysis limited to direct dependencies
```

#### Python Analysis Sensor
```python
# Python Sensor Capabilities
- AST Parsing: Built-in ast module
- Import Analysis: Dependency graph generation
- Code Metrics: Complexity, maintainability index
- Type Checking: Basic type inference
- Test Coverage: pytest-cov XML integration
- Security Analysis: Bandit integration (when available)

# Analysis Limitations  
- Dynamic feature analysis limited
- Type checking requires type hints
- Runtime behavior analysis not available
```

### Coverage Integration Architecture

#### Coverage Report Formats
```
XML Format (Cobertura):
- Standard XML schema
- Line-level coverage data
- Branch coverage (when available)
- Method coverage (when available)
- File and package aggregation

LCOV Format:
- Text-based format
- Line coverage only
- Branch coverage extensions
- Tool-specific extensions

JaCoCo Format:
- XML and binary formats
- Line and branch coverage
- Method and class coverage
- Package aggregation
```

#### Coverage Processing Pipeline
```
1. Coverage Tool Execution (cargo-tarpaulin, pytest-cov, etc.)
2. Report Generation (XML/LCOV format)
3. Scanner Coverage Parser
4. Data Normalization
5. Metric Calculation
6. Integration with Analysis Results
7. Dashboard Display
```

## Performance Optimization

### Scanner Performance Tuning
```bash
# Memory Configuration
SONAR_SCANNER_JAVA_OPTS="-Xmx4g -Xms2g -XX:+UseG1GC"

# Parallel Processing
sonar.scanner.scanAll=false  # Scan changed files only
sonar.issuesReport.html.enable=false  # Disable HTML report generation

# Network Optimization
sonar.ws.timeout=60000  # 60 seconds timeout
sonar.http.timeout=60000  # HTTP timeout

# Cache Configuration
sonar.scm.cache.timeout=1h  # SCM cache timeout
sonar.cpd.cache.timeout=1h  # Duplication cache timeout
```

### Server Performance Tuning
```yaml
# Docker Compose Performance Tuning
services:
  sonarqube:
    environment:
      # JVM Memory Settings
      - SONAR_WEB_JVMOPTS=-Xmx4g -Xms2g -XX:+UseG1GC
      - SONAR_CE_JVMOPTS=-Xmx2g -Xms1g -XX:+UseG1GC
      
      # Database Connection Pool
      - SONAR_JDBC_MAXACTIVE=20
      - SONAR_JDBC_MAXIDLE=10
      - SONAR_JDBC_MINIDLE=5
      
      # Performance Settings
      - SONAR_SEARCH_TIMEOUT=30000
      - SONAR_WEB_TIMEOUT=60000
      
    deploy:
      resources:
        limits:
          memory: 6g
          cpus: '2.0'
        reservations:
          memory: 4g
          cpus: '1.0'
```

### Database Performance Optimization
```sql
-- PostgreSQL Performance Tuning
-- Connection Pooling
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

-- Index Optimization
CREATE INDEX CONCURRENTLY idx_project_measures_project_id ON project_measures(project_id);
CREATE INDEX CONCURRENTLY idx_issues_component_uuid ON issues(component_uuid);
CREATE INDEX CONCURRENTLY idx_snapshots_project_uuid ON snapshots(project_uuid);

-- Vacuum and Analyze Schedule
-- Run weekly: VACUUM ANALYZE;
```

## Advanced Configuration

### Custom Quality Gates
```json
{
  "name": "Custom High-Quality Gate",
  "conditions": [
    {
      "metric": "coverage",
      "op": "LT",
      "error": "80"
    },
    {
      "metric": "reliability_rating", 
      "op": "GT",
      "error": "1"
    },
    {
      "metric": "security_rating",
      "op": "GT", 
      "error": "1"
    },
    {
      "metric": "maintainability_rating",
      "op": "GT",
      "error": "1"
    },
    {
      "metric": "duplicated_lines_density",
      "op": "GT",
      "error": "3"
    },
    {
      "metric": "new_coverage",
      "op": "LT",
      "error": "85"
    }
  ]
}
```

### Custom Quality Profiles
```json
{
  "name": "Custom Rust Profile",
  "language": "rust",
  "rules": [
    {
      "key": "rust:S112",
      "severity": "BLOCKER",
      "params": {
        "format": "^[A-Z][a-zA-Z0-9]*$"
      }
    },
    {
      "key": "rust:S106", 
      "severity": "CRITICAL",
      "params": {
        "format": "^[a-z][a-z0-9_]*$"
      }
    }
  ]
}
```

### Multi-Module Project Configuration
```json
{
  "projectKey": "multi-module-project",
  "projectName": "Multi Module Project",
  "modules": [
    {
      "key": "module1",
      "name": "Module 1",
      "baseDir": "module1",
      "sources": ["src"],
      "tests": ["tests"]
    },
    {
      "key": "module2",
      "name": "Module 2", 
      "baseDir": "module2",
      "sources": ["src"],
      "tests": ["tests"]
    }
  ],
  "sources": ["module1/src", "module2/src"],
  "tests": ["module1/tests", "module2/tests"]
}
```

## Monitoring and Observability

### System Metrics Collection
```bash
# Docker Container Metrics
docker stats sonarqube --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Database Metrics
docker exec sonarqube_db psql -U sonar -d sonar -c "
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_tuples,
    n_dead_tup as dead_tuples
FROM pg_stat_user_tables;
"

# SonarQube Application Metrics
curl -u admin:admin "http://localhost:9000/api/system/health" | jq .
```

### Log Analysis and Monitoring
```bash
# SonarQube Server Logs
docker logs sonarqube --tail 100 | grep -E "(ERROR|WARN|INFO)"

# Database Logs  
docker logs sonarqube_db --tail 100 | grep -E "(ERROR|FATAL)"

# Scanner Execution Logs
# Scanner logs are captured in the orchestrator output
bash scripts/sonar/orchestrator.sh 2>&1 | tee scanner.log
```

### Performance Monitoring Dashboard
```bash
# Create performance monitoring script
#!/bin/bash
# monitor_performance.sh

echo "=== SonarQube Performance Monitor ==="

# Server Resources
echo "Server CPU and Memory:"
docker stats sonarqube --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Database Connections
echo "Database Connections:"
DB_CONNECTIONS=$(docker exec sonarqube_db psql -U sonar -d sonar -t -c "SELECT count(*) as connections FROM pg_stat_activity;")
echo "Active connections: $DB_CONNECTIONS"

# Disk Usage
echo "Disk Usage:"
df -h | grep -E "(Filesystem|/dev/)"

# Recent Analysis Performance
echo "Recent Analysis Performance:"
curl -s -u admin:admin "http://localhost:9000/api/ce/activity?component=distributed-trace-analysis-engine" | \
jq '.tasks[0:3] | .[] | {status: .status, executionTimeMs: .executionTimeMs, submittedAt: .submittedAt}'

echo "=== Monitoring Complete ==="
```

## Integration Patterns

### CI/CD Pipeline Integration
```yaml
# GitHub Actions Example
name: SonarQube Analysis
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  sonarqube:
    runs-on: ubuntu-latest
    services:
      sonarqube:
        image: sonarqube:community
        ports:
          - 9000:9000
        env:
          SONAR_JDBC_URL: jdbc:postgresql://localhost:5432/sonar
          SONAR_JDBC_USERNAME: sonar
          SONAR_JDBC_PASSWORD: sonar
        options: >-
          --health-cmd "curl -f http://localhost:9000/api/system/status || exit 1"
          --health-interval 30s
          --health-timeout 10s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 0  # Required for analysis history

    - name: Setup Rust
      uses: actions-rs/toolchain@v1
      with:
        toolchain: stable
        components: rustfmt, clippy

    - name: Cache cargo registry
      uses: actions/cache@v3
      with:
        path: ~/.cargo/registry
        key: ${{ runner.os }}-cargo-registry-${{ hashFiles('**/Cargo.lock') }}

    - name: Install cargo-tarpaulin
      run: cargo install cargo-tarpaulin

    - name: Generate coverage
      run: cargo tarpaulin --output-dir coverage --output-format xml --skip-clean

    - name: Run SonarQube scan
      env:
        SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      run: |
        docker run --rm --network ${{ job.services.sonarqube.network }} \
          -e SONAR_HOST_URL="http://sonarqube:9000" \
          -e SONAR_TOKEN="$SONAR_TOKEN" \
          -e GITHUB_TOKEN="$GITHUB_TOKEN" \
          -v "$(pwd):/project" \
          sonarsource/sonar-scanner-cli \
          -Dproject.settings=/project/sonar-project.properties \
          -Dsonar.pullrequest.key=${{ github.event.number }} \
          -Dsonar.pullrequest.branch=${{ github.head_ref }} \
          -Dsonar.pullrequest.base=${{ github.base_ref }}

    - name: Quality Gate check
      env:
        SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
      run: |
        QUALITY_GATE=$(curl -s -u "$SONAR_TOKEN:" \
          "http://localhost:9000/api/qualitygates/project_status?projectKey=distributed-trace-analysis-engine&pullRequest=${{ github.event.number }}")
        
        STATUS=$(echo $QUALITY_GATE | jq -r '.projectStatus.status')
        
        if [[ "$STATUS" == "ERROR" ]]; then
          echo "Quality gate failed!"
          echo $QUALITY_GATE | jq '.projectStatus.conditions[] | select(.status == "ERROR")'
          exit 1
        else
          echo "Quality gate passed: $STATUS"
        fi
```

### Jenkins Pipeline Integration
```groovy
pipeline {
    agent any
    
    environment {
        SONAR_TOKEN = credentials('sonarqube-token')
        SONAR_HOST_URL = 'http://localhost:9000'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup') {
            steps {
                sh 'cargo install cargo-tarpaulin'
            }
        }
        
        stage('Coverage') {
            steps {
                sh 'cargo tarpaulin --output-dir coverage --output-format xml --skip-clean'
            }
        }
        
        stage('SonarQube Analysis') {
            steps {
                script {
                    docker.image('sonarsource/sonar-scanner-cli').inside('--network sonarqube_network') {
                        sh '''
                            sonar-scanner \
                                -Dsonar.projectKey=distributed-trace-analysis-engine \
                                -Dsonar.sources=src \
                                -Dsonar.host.url=${SONAR_HOST_URL} \
                                -Dsonar.token=${SONAR_TOKEN} \
                                -Dsonar.coverageReportPaths=coverage/cobertura.xml
                        '''
                    }
                }
            }
        }
        
        stage('Quality Gate') {
            steps {
                script {
                    def qg = sh(
                        script: "curl -u '${SONAR_TOKEN}:' '${SONAR_HOST_URL}/api/qualitygates/project_status?projectKey=distributed-trace-analysis-engine'",
                        returnStdout: true
                    ).trim()
                    
                    def status = readJSON(text: qg).projectStatus.status
                    
                    if (status == 'ERROR') {
                        error "Quality gate failed!"
                    } else {
                        echo "Quality gate passed: ${status}"
                    }
                }
            }
        }
    }
}
```

## Troubleshooting Deep Dive

### Advanced Diagnostic Tools
```bash
#!/bin/bash
# advanced_diagnostics.sh

echo "=== Advanced SonarQube Diagnostics ==="

# 1. System Health Check
echo "1. System Health Check"
echo "Server Status:"
curl -s -u admin:admin "http://localhost:9000/api/system/health" | jq '.'

echo "Database Status:"
docker exec sonarqube_db pg_isready -U sonar

# 2. Network Connectivity Test
echo "2. Network Connectivity Test"
echo "Container Network:"
docker network inspect docker_sonarqube_network | jq '.[0].Containers | keys'

echo "Port Accessibility:"
netstat -tlnp | grep :9000

# 3. Resource Usage Analysis
echo "3. Resource Usage Analysis"
echo "Container Resources:"
docker stats sonarqube --no-stream --format json | jq '.[0] | {cpu: .CPUPerc, memory: .MemUsage, network: .NetIO}'

echo "Disk Usage:"
docker exec sonarqube du -sh /opt/sonarqube

# 4. Database Performance
echo "4. Database Performance"
docker exec sonarqube_db psql -U sonar -d sonar -c "
SELECT 
    datname as database,
    numbackends as connections,
    xact_commit as commits,
    xact_rollback as rollbacks,
    blks_read as blocks_read,
    tup_returned as tuples_returned
FROM pg_stat_database 
WHERE datname = 'sonar';
"

# 5. Recent Analysis History
echo "5. Recent Analysis History"
curl -s -u admin:admin "http://localhost:9000/api/ce/activity?component=distributed-trace-analysis-engine&ps=5" | \
jq '.tasks[] | {id: .id, status: .status, executionTimeMs: .executionTimeMs, submittedAt: .submittedAt}'

# 6. Error Log Analysis
echo "6. Error Log Analysis"
echo "Recent Errors:"
docker logs sonarqube --since 1h | grep -i error | tail -10

echo "Recent Warnings:"
docker logs sonarqube --since 1h | grep -i warning | tail -10

echo "=== Diagnostics Complete ==="
```

### Performance Profiling
```bash
# Scanner Performance Profiling
#!/bin/bash
# profile_scanner.sh

echo "=== Scanner Performance Profile ==="

# Run scanner with profiling
SCANNER_START=$(date +%s%N)

docker run --rm --network docker_sonarqube_network \
  -e SONAR_HOST_URL="http://sonarqube:9000" \
  -e SONAR_TOKEN="$SONAR_TOKEN" \
  -e SONAR_SCANNER_JAVA_OPTS="-Xmx4g -XX:+PrintGCDetails -XX:+PrintGCTimeStamps" \
  -v "$(pwd):/project" \
  sonarsource/sonar-scanner-cli \
  -X -Dproject.settings=/project/sonar-project.properties \
  -Dsonar.verbose=true

SCANNER_END=$(date +%s%N)
SCANNER_DURATION=$(( (SCANNER_END - SCANNER_START) / 1000000 ))

echo "Scanner execution time: ${SCANNER_DURATION}ms"

# Analyze scanner logs for bottlenecks
echo "Scanner Performance Analysis:"
docker logs $(docker ps -aq --filter "ancestor=sonarsource/sonar-scanner-cli") | \
  grep -E "(INFO|WARN|ERROR)" | \
  tail -20
```

## Future Reference and Maintenance

### Version Upgrade Planning
```bash
# Upgrade Planning Checklist
#!/bin/bash
# upgrade_planning.sh

echo "=== SonarQube Upgrade Planning ==="

# Current Version Check
CURRENT_VERSION=$(curl -s -u admin:admin "http://localhost:9000/api/system/status" | jq -r '.version')
echo "Current SonarQube Version: $CURRENT_VERSION"

# Latest Version Check
LATEST_VERSION=$(curl -s https://api.github.com/repos/SonarSource/sonarqube/releases/latest | jq -r '.tag_name')
echo "Latest SonarQube Version: $LATEST_VERSION"

# Compatibility Check
echo "Compatibility Check:"
echo "Docker Version: $(docker --version)"
echo "Scanner Version: $(docker run --rm sonarsource/sonar-scanner-cli --version)"

# Backup Planning
echo "Backup Requirements:"
echo "1. Database backup: docker exec sonarqube_db pg_dump -U sonar sonar > backup.sql"
echo "2. Configuration backup: tar -czf config_backup.tar.gz /opt/sonarqube/conf"
echo "3. Data backup: tar -czf data_backup.tar.gz /opt/sonarqube/data"

echo "=== Upgrade Planning Complete ==="
```

### Maintenance Schedule
```bash
# Monthly Maintenance Tasks
#!/bin/bash
# monthly_maintenance.sh

echo "=== Monthly SonarQube Maintenance ==="

# 1. Database Maintenance
echo "1. Database Maintenance"
docker exec sonarqube_db psql -U sonar -d sonar -c "VACUUM ANALYZE;"

# 2. Log Cleanup
echo "2. Log Cleanup"
docker exec sonarqube find /opt/sonarqube/logs -name "*.log.*" -mtime +30 -delete

# 3. Token Audit
echo "3. Token Audit"
curl -s -u admin:admin "http://localhost:9000/api/user_tokens/search" | \
  jq '.userTokens[] | {name: .name, createdAt: .createdAt}'

# 4. Performance Review
echo "4. Performance Review"
docker stats sonarqube --no-stream
df -h | grep sonarqube

# 5. Security Review
echo "5. Security Review"
curl -s -u admin:admin "http://localhost:9000/api/users/search" | jq '.users | length'

echo "=== Monthly Maintenance Complete ==="
```

## Conclusion

This technical reference guide provides comprehensive coverage of the SonarQube DTAE setup architecture, performance optimization, advanced configuration, and maintenance procedures. It serves as the definitive technical resource for system administrators and advanced users requiring deep technical understanding of the system.

For day-to-day operations, refer to the runbooks. For troubleshooting, consult the troubleshooting guide. For quick setup, use the automated setup script.

This document will be updated as the system evolves and new features are added.

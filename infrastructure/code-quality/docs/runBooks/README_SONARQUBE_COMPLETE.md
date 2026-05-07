# SonarQube DTAE - Complete Documentation and Setup

## Overview
This is the complete SonarQube setup and documentation package for the Distributed Trace Analysis Engine (DTAE) project. It includes automated setup scripts and comprehensive runbooks for team members to easily configure, operate, and troubleshoot the code analysis infrastructure.

## Quick Start

### For New Team Members
1. **Run the automated setup script**:
   ```bash
   cd /path/to/your/project
   ./setup-sonarqube.sh "Your Project Name" "your-project-key" "1.0.0" rust "http://sonarqube:9000"
   ```

2. **Run your first analysis**:
   ```bash
   make sonar-analyze
   ```

3. **View results**:
   - Open http://localhost:9000
   - Login: admin / admin
   - Navigate to your project dashboard

## What's Included

### 🚀 Enhanced Setup Script
- **`setup-sonarqube.sh`**: Comprehensive automated setup for new projects
- **Features**: 
  - Advanced dependency checking with detailed diagnostics
  - Robust token generation with retry logic and validation
  - Intelligent project creation with conflict resolution
  - Language-specific configuration templates
  - Comprehensive error handling and troubleshooting guidance
  - Network connectivity verification
  - Resource requirement validation
- **Usage**: One-command setup for any project type with extensive error handling

### 📚 6 Comprehensive Runbooks (Enhanced with In-Depth Details)

#### Runbook 1: New Project Configuration and Token Creation
- **Enhanced token management**: Comprehensive token verification, copy-paste issue resolution
- **Advanced project setup**: Multi-language support, validation, conflict handling
- **Security best practices**: Token rotation, access control, audit procedures
- **Real-world scenarios**: All issues we encountered with detailed solutions
- **Edge cases**: Network issues, permission problems, version conflicts

#### Runbook 2: Complete Operation Guide  
- **Detailed command reference**: Every command with explanations and expected outputs
- **Advanced configuration**: Custom properties, quality gates, performance tuning
- **Production workflows**: CI/CD integration, automation, monitoring
- **Troubleshooting procedures**: Step-by-step diagnostic commands
- **Performance optimization**: Memory tuning, parallel processing, caching

#### Runbook 3: Reports Access and Network Information
- **Complete API documentation**: All endpoints with examples and response formats
- **Network architecture diagrams**: Docker networking, security zones, access patterns
- **Advanced dashboard usage**: Custom views, filters, export options
- **Integration examples**: Slack notifications, webhooks, custom reporting
- **Security configurations**: Authentication, authorization, audit trails

#### Runbook 4: Dependencies and Required Tools
- **Detailed hardware requirements**: CPU, memory, storage analysis by project size
- **Complete version compatibility matrix**: Minimum, recommended, latest tested versions
- **Language-specific toolchains**: Rust, Python, JavaScript, Java with exact versions
- **System library dependencies**: Linux, macOS, Windows (WSL2) requirements
- **Advanced installation procedures**: Custom configurations, optimization settings

#### Runbook 5: Configuration Management and JSON Structure
- **Complete JSON schema**: Every field documented with examples and constraints
- **Advanced configuration patterns**: Multi-module projects, custom quality gates
- **Environment-specific configurations**: Development, staging, production setups
- **Validation and management scripts**: Automated validation, migration tools
- **Template library**: Comprehensive templates for all project types

#### Runbook 6: Issues and Troubleshooting Guide
- **Comprehensive error analysis**: Deep technical analysis of every error type
- **Advanced diagnostic tools**: Performance profiling, system health monitoring
- **Real-world troubleshooting scripts**: Production-ready diagnostic utilities
- **Prevention strategies**: Proactive monitoring, maintenance procedures
- **Support escalation**: When and how to seek additional help

### 📖 In-Depth Technical Reference Guide
- **Complete architecture documentation**: System design, data flow, security models
- **Performance optimization**: Advanced tuning, monitoring, capacity planning
- **Integration patterns**: CI/CD pipelines, monitoring, alerting
- **Maintenance procedures**: Backup, recovery, upgrade planning
- **Advanced troubleshooting**: Deep diagnostic tools, performance profiling

## File Structure

```
distributed-trace-analysis-engine/
├── setup-sonarqube.sh                          # Automated setup script
├── README_SONARQUBE_COMPLETE.md                # This file
├── sonar-config.json                           # Main configuration
├── sonar-project.properties                    # Generated scanner config
├── Makefile                                    # Command interface
├── scripts/sonar/                             # Analysis scripts
│   ├── utils.sh                               # Utility functions
│   ├── config_loader.sh                       # Configuration loader
│   ├── server_manager.sh                      # Server management
│   ├── coverage_generator.sh                  # Coverage generation
│   ├── sonar_scanner.sh                       # Scanner execution
│   └── orchestrator.sh                        # Workflow coordinator
├── coverage/                                  # Coverage reports
└── ../observability/                          # Documentation
    ├── RUNBOOK_1_NEW_PROJECT_SETUP.md
    ├── RUNBOOK_2_COMPLETE_OPERATION_GUIDE.md
    ├── RUNBOOK_3_REPORTS_ACCESS_AND_NETWORK.md
    ├── RUNBOOK_4_DEPENDENCIES_AND_TOOLS.md
    ├── RUNBOOK_5_CONFIGURATION_MANAGEMENT.md
    └── RUNBOOK_6_TROUBLESHOOTING_GUIDE.md
```

## Key Features

### ✅ Automated Setup
- One-command project configuration
- Automatic token generation
- Script creation and setup
- Dependency installation

### ✅ Multi-Language Support
- Rust (cargo-tarpaulin)
- Python (pytest-cov)
- JavaScript/TypeScript (Jest)
- Java (JaCoCo)
- Multi-language projects

### ✅ Docker Integration
- Containerized SonarQube server
- Scanner running in Docker
- Network configuration handled
- Volume management

### ✅ Comprehensive Documentation
- 6 detailed runbooks
- Real-world examples
- Troubleshooting scenarios
- Best practices

### ✅ Production Ready
- Security considerations
- Performance optimization
- Monitoring and health checks
- CI/CD integration examples

## Quick Reference Commands

### Essential Commands
```bash
# Complete analysis
make sonar-analyze

# Server management
make sonar-start
make sonar-stop

# Dependencies
make sonar-setup

# Individual steps
make sonar-coverage
make sonar-scan
```

### Setup Commands
```bash
# Automated setup
./setup-sonarqube.sh "Project Name" "project-key" "1.0.0" rust

# Manual token generation
curl -X POST -u admin:admin "http://localhost:9000/api/user_tokens/generate?name=token-name"

# Project creation
curl -X POST -u admin:admin "http://localhost:9000/api/projects/create?project=key&name=Name"
```

### Troubleshooting Commands
```bash
# Health check
bash health_check.sh

# Validate setup
bash validate_setup.sh

# Server status
curl http://localhost:9000/api/system/status

# Token validation
curl -u "token:" "http://localhost:9000/api/authentication/validate"
```

## Access Points

### Web Interface
- **Main Dashboard**: http://localhost:9000
- **Project Dashboard**: http://localhost:9000/dashboard?id=project-key
- **Admin Area**: http://localhost:9000/admin
- **API Documentation**: http://localhost:9000/api/documentation

### API Endpoints
- **Projects**: http://localhost:9000/api/projects/search
- **Measures**: http://localhost:9000/api/measures/component
- **Issues**: http://localhost:9000/api/issues/search
- **Quality Gates**: http://localhost:9000/api/qualitygates

## Configuration Examples

### Rust Project Configuration
```json
{
  "projectKey": "rust-project",
  "projectName": "Rust Project",
  "projectVersion": "1.0.0",
  "language": "rust",
  "sourceDirs": ["src"],
  "testDirs": ["tests"],
  "exclusions": ["target/**"],
  "sonarHostUrl": "http://sonarqube:9000",
  "sonarToken": "squ_44characterlongtoken...",
  "coverage": {
    "tool": "cargo-tarpaulin",
    "outputFormat": "xml",
    "outputDir": "coverage"
  }
}
```

### Python Project Configuration
```json
{
  "projectKey": "python-project",
  "projectName": "Python Project",
  "projectVersion": "1.0.0",
  "language": "py",
  "sourceDirs": ["src", "lib"],
  "testDirs": ["tests", "test"],
  "exclusions": ["venv/**", "__pycache__/**"],
  "sonarHostUrl": "http://sonarqube:9000",
  "sonarToken": "squ_44characterlongtoken...",
  "coverage": {
    "tool": "pytest-cov",
    "outputFormat": "xml",
    "outputDir": "coverage"
  }
}
```

## Common Workflows

### Daily Development Workflow
```bash
# 1. Make code changes
# 2. Run tests
cargo test

# 3. Run analysis
make sonar-analyze

# 4. Check results
# Open http://localhost:9000
```

### New Project Setup Workflow
```bash
# 1. Run setup script
./setup-sonarqube.sh "New Project" "new-project" "1.0.0" rust

# 2. Install dependencies
make sonar-setup

# 3. Run first analysis
make sonar-analyze

# 4. Review configuration
cat sonar-config.json
```

### CI/CD Integration Workflow
```bash
# In CI pipeline:
# 1. Start SonarQube
make sonar-start

# 2. Wait for readiness
sleep 60

# 3. Run analysis
make sonar-analyze

# 4. Check quality gate
curl -u "$SONAR_TOKEN:" "http://localhost:9000/api/qualitygates/project_status?projectKey=$PROJECT_KEY"
```

## Security Best Practices

### Token Management
- ✅ Generate tokens via API (not UI copy-paste)
- ✅ Use descriptive token names
- ✅ Generate separate tokens per project
- ✅ Store tokens in environment variables
- ✅ Rotate tokens regularly

### Access Control
- ✅ Use project-specific permissions
- ✅ Limit admin access
- ✅ Monitor token usage
- ✅ Revoke unused tokens

### Network Security
- ✅ Use Docker network isolation
- ✅ Expose only necessary ports
- ✅ Use HTTPS in production
- ✅ Monitor network access

## Performance Optimization

### Server Configuration
```yaml
# Add to docker-compose.yml for production
services:
  sonarqube:
    environment:
      - SONAR_WEB_JVMOPTS=-Xmx4g -Xms2g -XX:+UseG1GC
      - SONAR_CE_JVMOPTS=-Xmx2g -Xms1g -XX:+UseG1GC
    deploy:
      resources:
        limits:
          memory: 6g
          cpus: '2.0'
```

### Scanner Optimization
```bash
# Increase scanner memory
export SONAR_SCANNER_JAVA_OPTS="-Xmx4g"

# Run with verbose output for debugging
docker run --rm --network docker_sonarqube_network \
  -e SONAR_SCANNER_JAVA_OPTS="-Xmx4g" \
  -e SONAR_HOST_URL="http://sonarqube:9000" \
  -e SONAR_TOKEN="$TOKEN" \
  -v "$(pwd):/project" \
  sonarsource/sonar-scanner-cli \
  -X -Dproject.settings=/project/sonar-project.properties
```

## Monitoring and Health Checks

### Health Check Script
```bash
#!/bin/bash
# health_check.sh

# Check server
if curl -s http://localhost:9000/api/system/status | grep -q "UP"; then
    echo "✅ Server healthy"
else
    echo "❌ Server unhealthy"
    exit 1
fi

# Check token
TOKEN=$(jq -r '.sonarToken' sonar-config.json)
if curl -u "$TOKEN:" http://localhost:9000/api/authentication/validate > /dev/null; then
    echo "✅ Token valid"
else
    echo "❌ Token invalid"
    exit 1
fi

echo "✅ All checks passed"
```

### Monitoring Commands
```bash
# Server resources
docker stats sonarqube

# Disk usage
df -h

# Memory usage
free -h

# Error logs
docker logs sonarqube 2>&1 | grep -i error | tail -5
```

## Integration Examples

### Slack Notifications
```bash
#!/bin/bash
# slack_notification.sh

WEBHOOK_URL="$SLACK_WEBHOOK_URL"
PROJECT_KEY="distributed-trace-analysis-engine"
TOKEN="$SONAR_TOKEN"

# Get analysis results
MEASURES=$(curl -u "$TOKEN:" \
  "http://localhost:9000/api/measures/component?component=$PROJECT_KEY&metricKeys=coverage,violations")

# Extract metrics
COVERAGE=$(echo $MEASURES | jq -r '.component.measures[] | select(.metric=="coverage") | .value')
VIOLATIONS=$(echo $MEASURES | jq -r '.component.measures[] | select(.metric=="violations") | .value')

# Send to Slack
curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"SonarQube Analysis Results\\nCoverage: $COVERAGE%\\nViolations: $VIOLATIONS\\n<http://localhost:9000/dashboard?id=$PROJECT_KEY|View Details>\"}" \
  "$WEBHOOK_URL"
```

### GitHub Actions Integration
```yaml
# .github/workflows/sonarqube.yml
name: SonarQube Analysis

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

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
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Rust
      uses: actions-rs/toolchain@v1
      with:
        toolchain: stable
    
    - name: Install cargo-tarpaulin
      run: cargo install cargo-tarpaulin
    
    - name: Generate coverage
      run: cargo tarpaulin --output-dir coverage --output-format xml --skip-clean
    
    - name: Run SonarQube scan
      env:
        SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
      run: |
        docker run --rm --network ${{ job.services.sonarqube.network }} \
          -e SONAR_HOST_URL="http://sonarqube:9000" \
          -e SONAR_TOKEN="$SONAR_TOKEN" \
          -v "$(pwd):/project" \
          sonarsource/sonar-scanner-cli \
          -Dproject.settings=/project/sonar-project.properties
```

## Support and Troubleshooting

### Common Issues and Solutions
1. **401 Unauthorized**: Token truncated or invalid → Regenerate token via API
2. **Connection refused**: Server not running → Start SonarQube server
3. **Coverage parsing error**: XML format incompatible → Exclude coverage temporarily
4. **Out of memory**: Insufficient resources → Increase memory allocation
5. **Network issues**: Docker network problems → Recreate network

### Getting Help
1. **Read the runbooks**: Each runbook covers specific topics in detail
2. **Check logs**: Docker logs contain valuable diagnostic information
3. **Validate configuration**: Use provided validation scripts
4. **Community support**: SonarQube Community forums
5. **Team support**: Create issue in project repository

### Information to Collect for Support
```bash
# System information
uname -a
docker --version
docker-compose --version

# Configuration
cat sonar-config.json

# Logs
docker logs sonarqube | tail -50

# Error details
# Full error message, command run, timestamp
```

## Version History

### v1.0.0 (Current)
- Automated setup script
- 6 comprehensive runbooks
- Multi-language support
- Docker integration
- Complete documentation
- Troubleshooting guide
- CI/CD integration examples

## Future Enhancements

### Planned Features
- [ ] Kubernetes deployment templates
- [ ] Advanced quality gate configurations
- [ ] Automated report generation
- [ ] Performance monitoring dashboard
- [ ] Multi-tenant support
- [ ] Advanced security configurations

### Community Contributions
- Contributions welcome via pull requests
- Documentation improvements
- New language support
- Bug fixes and enhancements
- Integration examples

## License and Credits

This SonarQube setup and documentation package is maintained by the DTAE development team.

### Credits
- SonarSource for SonarQube Community Edition
- Docker for containerization
- Contributors and maintainers
- Community feedback and suggestions

---

## Quick Start Summary

For immediate use:
1. **Run setup**: `./setup-sonarqube.sh "My Project" "my-project" "1.0.0" rust`
2. **Analyze**: `make sonar-analyze`
3. **View**: http://localhost:9000

For detailed guidance: Read the 6 runbooks in order.

For troubleshooting: Consult Runbook 6 and the health check scripts.

For advanced usage: Review the integration examples and configuration templates.

**Happy code analysis!** 🚀

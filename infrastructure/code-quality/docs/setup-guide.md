# SonarQube Code Quality Infrastructure Setup Guide

This guide provides comprehensive instructions for setting up the SonarQube code quality infrastructure with PostgreSQL, supporting both local Docker and Kubernetes deployments.

## Prerequisites

- Docker and Docker Compose (for local deployment)
- Kubernetes cluster with kubectl (for production deployment)
- PostgreSQL 17 (or managed PostgreSQL service)
- Python 3.11+
- Go 1.21+
- Rust stable toolchain

## Quick Start (Docker)

### 1. Clone and Setup

```bash
cd infrastructure/code-quality
```

### 2. Configure Environment

Create `.env` file:
```bash
# PostgreSQL Configuration
POSTGRES_USER=sonar
POSTGRES_PASSWORD=sonar
POSTGRES_DB=sonar

# SonarQube Configuration
SONARQUBE_TOKEN=your-sonarqube-token-here

# API Configuration
DATABASE_URL=postgresql://sonar:sonar@localhost:5432/sonar
SONARQUBE_URL=http://localhost:9000
FLASK_ENV=development
```

### 3. Start Services

```bash
cd deployment/docker
docker-compose up -d
```

### 4. Initialize Database

```bash
# Wait for PostgreSQL to be ready
docker-compose exec db psql -U sonar -d sonar -f /docker-entrypoint-initdb.d/init.sql
```

### 5. Access Services

- **SonarQube UI**: http://localhost:9000
- **Quality API**: http://localhost:5000
- **API Health Check**: http://localhost:5000/health

## Production Deployment (Kubernetes)

### 1. Create Namespace

```bash
kubectl apply -f deployment/kubernetes/namespace.yaml
```

### 2. Deploy PostgreSQL

```bash
kubectl apply -f deployment/kubernetes/postgresql.yaml
```

### 3. Deploy SonarQube

```bash
kubectl apply -f deployment/kubernetes/sonarqube.yaml
```

### 4. Deploy Quality API

```bash
# Update secrets first
kubectl apply -f deployment/kubernetes/quality-api.yaml
```

### 5. Configure Ingress

```bash
# Update hostnames in ingress.yaml first
kubectl apply -f deployment/kubernetes/ingress.yaml
```

## Configuration

### SonarQube Token Generation

1. Access SonarQube UI at http://localhost:9000
2. Login as administrator
3. Go to **My Account** → **Security**
4. Generate new token with name "quality-api"
5. Copy token to environment variables

### Database Schema

The PostgreSQL schema is automatically created via the database schema file:

```bash
psql -U sonar -d sonar -f infrastructure/persistence/database_schema.sql
```

## API Usage

### Create Project

```bash
curl -X POST http://localhost:5000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "my-project",
    "name": "My Project",
    "description": "A sample project",
    "languages": ["python", "javascript"]
  }'
```

### Trigger Analysis

```bash
curl -X POST http://localhost:5000/api/v1/analysis/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "my-project",
    "branch": "main",
    "commit_hash": "abc123def456"
  }'
```

### Check Analysis Status

```bash
curl http://localhost:5000/api/v1/analysis/{analysis_id}/status
```

### Get Quality Report

```bash
curl "http://localhost:5000/api/v1/projects/my-project/report?days=30"
```

## Analysis Tools

### Python Deep Analyzer

```bash
python analysis-tools/python/deep_analyzer.py /path/to/project
```

### Go Infrastructure Analyzer

```bash
cd analysis-tools/go/infrastructure-analyzer
go run main.go /path/to/infrastructure
```

### Rust Performance Tools

```bash
cd analysis-tools/rust/performance-tools
cargo run -- /path/to/rust/project
```

## GitHub Actions Integration

### Setup Secrets

1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Add the following secrets:
   - `SONAR_HOST_URL`: Your SonarQube server URL
   - `SONAR_TOKEN`: Generated SonarQube token

### Workflow Configuration

The GitHub Actions workflow is automatically triggered on:
- Push to main/master/develop branches
- Pull request creation and updates

### Quality Gates

The workflow enforces quality gates:
- Analysis must pass
- Security vulnerabilities must be addressed
- Performance tests must pass

## Monitoring and Maintenance

### Health Checks

- **API Health**: `GET /health`
- **Readiness Check**: `GET /ready`
- **Database Connection**: Checked via readiness probe

### Logs

```bash
# Docker logs
docker-compose logs -f quality-api
docker-compose logs -f sonarqube

# Kubernetes logs
kubectl logs -f deployment/quality-api -n code-quality
kubectl logs -f deployment/sonarqube -n code-quality
```

### Backup and Recovery

#### PostgreSQL Backup

```bash
# Docker
docker-compose exec db pg_dump -U sonar sonar > backup.sql

# Kubernetes
kubectl exec -n code-quality postgresql-0 -- pg_dump -U sonar sonar > backup.sql
```

#### Restore

```bash
# Docker
docker-compose exec -T db psql -U sonar sonar < backup.sql

# Kubernetes
kubectl exec -i -n code-quality postgresql-0 -- psql -U sonar sonar < backup.sql
```

## Troubleshooting

### Common Issues

1. **SonarQube Connection Failed**
   - Verify SonarQube is running: `curl http://localhost:9000/api/system/status`
   - Check token validity
   - Verify network connectivity

2. **Database Connection Failed**
   - Check PostgreSQL status: `docker-compose ps db`
   - Verify connection string
   - Check database logs

3. **Analysis Timeout**
   - Increase timeout in configuration
   - Check project size and complexity
   - Verify SonarQube server resources

4. **GitHub Actions Failures**
   - Check secrets configuration
   - Verify workflow permissions
   - Review action logs

### Performance Optimization

1. **SonarQube Performance**
   - Increase JVM heap size: `SONAR_WEB_JAVAOPTS="-Xmx4g -Xms4g"`
   - Use SSD storage for PostgreSQL
   - Configure connection pooling

2. **API Performance**
   - Enable database connection pooling
   - Implement caching for frequent queries
   - Use horizontal scaling

## Security Considerations

1. **Network Security**
   - Use HTTPS in production
   - Implement network policies in Kubernetes
   - Restrict access to SonarQube UI

2. **Authentication**
   - Use strong SonarQube tokens
   - Rotate tokens regularly
   - Implement RBAC for API access

3. **Data Protection**
   - Encrypt database connections
   - Use secrets management
   - Regular security updates

## Scaling

### Horizontal Scaling

- API services can be scaled horizontally
- Use load balancer for API endpoints
- Implement session affinity if needed

### Vertical Scaling

- Increase SonarQube memory for large projects
- Scale PostgreSQL based on load
- Monitor resource usage regularly

## Support

For issues and questions:
1. Check logs for error messages
2. Review troubleshooting section
3. Consult SonarQube documentation
4. Review GitHub Actions workflow logs

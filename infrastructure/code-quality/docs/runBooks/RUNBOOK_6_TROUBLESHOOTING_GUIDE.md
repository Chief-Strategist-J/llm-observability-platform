# Runbook 6: Issues and Troubleshooting Guide

## Overview
This runbook covers common issues, errors, and troubleshooting procedures for the SonarQube DTAE setup. It includes real-world problems we encountered and their solutions, plus prevention strategies.

## Error Categories

### 1. Authentication & Token Issues
### 2. Network & Connectivity Issues  
### 3. Configuration Issues
### 4. Coverage Generation Issues
### 5. Scanner Execution Issues
### 6. Server Performance Issues
### 7. Docker & Container Issues

## Authentication & Token Issues

### Issue 1: HTTP 401 Unauthorized (Most Common)
**Symptoms**: Scanner fails with "HTTP 401 Unauthorized" error
**Root Causes**: 
- Token truncated or incomplete (most common - 95% of cases)
- Wrong token format (sqp_ vs squ_)
- Token expired or revoked
- Incorrect authentication method
- Token generated for wrong user type
- Token copied with extra whitespace or characters

#### Deep Technical Analysis

**Token Format Requirements**:
- **Length**: Exactly 44 characters
- **Prefix**: Must start with "squ_" (user tokens) or "sqp_" (project tokens)
- **Charset**: Only alphanumeric characters after prefix
- **No whitespace**: No spaces, newlines, or special characters
- **Case sensitivity**: Tokens are case-sensitive

**Token Types**:
- **User tokens (squ_)**: For running analysis scans
- **Project tokens (sqp_)**: For project administration
- **Global tokens**: For system-wide operations

#### Solutions

##### Solution 1.1: Comprehensive Token Verification
```bash
#!/bin/bash
# verify_token_comprehensive.sh

TOKEN="$1"

echo "=== Token Verification ==="
echo "Token provided: ${TOKEN:0:10}...${TOKEN: -10}"
echo "Token length: ${#TOKEN}"
echo "Token prefix: ${TOKEN:0:4}"

# Check length
if [[ ${#TOKEN} -ne 44 ]]; then
    echo "❌ FAILED: Token length is ${#TOKEN} (should be 44)"
    echo "This is the most common cause of 401 errors"
    echo "Token was likely truncated during copy-paste"
    exit 1
fi

# Check prefix
if [[ ! "$TOKEN" =~ ^squ_[a-zA-Z0-9]+$ ]]; then
    echo "❌ FAILED: Invalid token format"
    echo "Expected: squ_ followed by 40 alphanumeric characters"
    echo "Got: ${TOKEN:0:4} prefix"
    
    if [[ "$TOKEN" =~ ^sqp_ ]]; then
        echo "💡 INFO: You have a project token (sqp_), need a user token (squ_)"
    fi
    exit 1
fi

# Check for whitespace
if [[ "$TOKEN" != "$(echo -n "$TOKEN" | tr -d ' \t\n\r')" ]]; then
    echo "❌ FAILED: Token contains whitespace"
    echo "Remove any spaces, tabs, or newlines from token"
    exit 1
fi

# Test token validity
echo "Testing token validity..."
VALIDATION_RESPONSE=$(curl -s -u "$TOKEN:" "http://localhost:9000/api/authentication/validate" 2>/dev/null || echo "")

if [[ "$VALIDATION_RESPONSE" == '{"valid":true}' ]]; then
    echo "✅ PASSED: Token is valid and working"
else
    echo "❌ FAILED: Token validation failed"
    echo "Server response: $VALIDATION_RESPONSE"
    echo "Token may be expired or revoked"
    exit 1
fi

echo "=== Token Verification Complete ==="
```

##### Solution 1.2: Generate New Token via API (With Error Handling)
```bash
#!/bin/bash
# generate_token_robust.sh

TOKEN_NAME="${1:-scanner-token-$(date +%s)}"
ADMIN_USER="${2:-admin}"
ADMIN_PASSWORD="${3:-admin}"
SERVER_URL="${4:-http://localhost:9000}"

echo "=== Generating New Token ==="
echo "Token name: $TOKEN_NAME"

# Check server availability
echo "Checking server availability..."
if ! curl -s --connect-timeout 5 "$SERVER_URL/api/system/status" > /dev/null; then
    echo "❌ FAILED: Cannot connect to SonarQube server"
    echo "Check if server is running: docker ps | grep sonarqube"
    echo "Check server logs: docker logs sonarqube"
    exit 1
fi

echo "✅ Server is available"

# Check existing tokens
echo "Checking for existing tokens..."
EXISTING_TOKENS=$(curl -s -u "$ADMIN_USER:$ADMIN_PASSWORD" "$SERVER_URL/api/user_tokens/search" 2>/dev/null || echo "")

if echo "$EXISTING_TOKENS" | jq -e '.userTokens[] | select(.name=="'$TOKEN_NAME'")' > /dev/null 2>&1; then
    echo "⚠️  WARNING: Token with name '$TOKEN_NAME' already exists"
    echo "Revoking existing token..."
    
    REVOKE_RESPONSE=$(curl -s -X POST -u "$ADMIN_USER:$ADMIN_PASSWORD" \
        "$SERVER_URL/api/user_tokens/revoke?name=$TOKEN_NAME" 2>/dev/null || echo "")
    
    if [[ -z "$REVOKE_RESPONSE" ]]; then
        echo "✅ Existing token revoked"
    else
        echo "⚠️  Could not revoke existing token: $REVOKE_RESPONSE"
    fi
fi

# Generate new token with retry logic
MAX_ATTEMPTS=3
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "Generation attempt $ATTEMPT/$MAX_ATTEMPTS..."
    
    RESPONSE=$(curl -s -X POST -u "$ADMIN_USER:$ADMIN_PASSWORD" \
        "$SERVER_URL/api/user_tokens/generate?name=$TOKEN_NAME" \
        -w "%{http_code}" 2>/dev/null)
    
    HTTP_CODE="${RESPONSE: -3}"
    RESPONSE_BODY="${RESPONSE%???}"
    
    if [[ "$HTTP_CODE" == "200" ]]; then
        if echo "$RESPONSE_BODY" | jq -e '.token' > /dev/null 2>&1; then
            NEW_TOKEN=$(echo "$RESPONSE_BODY" | jq -r '.token')
            
            # Verify token format
            if [[ ${#NEW_TOKEN} -eq 44 && "$NEW_TOKEN" =~ ^squ_[a-zA-Z0-9]+$ ]]; then
                echo "✅ Token generated successfully"
                echo "Token: ${NEW_TOKEN:0:10}...${NEW_TOKEN: -10} (${#NEW_TOKEN} chars)"
                echo "Token created at: $(echo "$RESPONSE_BODY" | jq -r '.createdAt')"
                
                # Test the new token immediately
                echo "Testing new token..."
                TEST_RESPONSE=$(curl -s -u "$NEW_TOKEN:" "$SERVER_URL/api/authentication/validate" 2>/dev/null || echo "")
                
                if [[ "$TEST_RESPONSE" == '{"valid":true}' ]]; then
                    echo "✅ New token validated successfully"
                    echo "=== Token Generation Complete ==="
                    echo "Token: $NEW_TOKEN"
                    echo "Store this token securely in your configuration"
                    exit 0
                else
                    echo "❌ New token failed validation: $TEST_RESPONSE"
                fi
            else
                echo "❌ Invalid token format: ${#NEW_TOKEN} chars, prefix: ${NEW_TOKEN:0:4}"
            fi
        else
            echo "❌ Invalid response format: $RESPONSE_BODY"
        fi
    else
        echo "❌ HTTP $HTTP_CODE: $RESPONSE_BODY"
    fi
    
    if [[ $ATTEMPT -eq $MAX_ATTEMPTS ]]; then
        echo "❌ FAILED: Could not generate valid token after $MAX_ATTEMPTS attempts"
        echo "Troubleshooting steps:"
        echo "1. Check admin credentials: curl -u $ADMIN_USER:$ADMIN_PASSWORD $SERVER_URL/api/system/status"
        echo "2. Check server logs: docker logs sonarqube"
        echo "3. Check server resources: docker stats sonarqube"
        echo "4. Try different token name"
        exit 1
    fi
    
    ((ATTEMPT++))
    sleep 2
done
```

##### Solution 1.3: Fix Common Token Copy-Paste Issues
```bash
#!/bin/bash
# fix_token_copy_paste.sh

echo "=== Fixing Token Copy-Paste Issues ==="

# Common issues and fixes
echo "Common token copy-paste issues and fixes:"
echo ""
echo "1. Token truncated in terminal:"
echo "   Problem: Terminal line wrapping cuts off token"
echo "   Fix: Use echo -n or copy from browser inspect element"
echo ""
echo "2. Extra whitespace:"
echo "   Problem: Token has leading/trailing spaces or newlines"
echo "   Fix: echo -n \"\$TOKEN\" | tr -d ' \\t\\n'"
echo ""
echo "3. Wrong token type:"
echo "   Problem: Using sqp_ instead of squ_"
echo "   Fix: Generate user token, not project token"
echo ""
echo "4. Token from UI vs API:"
echo "   Problem: UI display truncates token"
echo "   Fix: Use API generation or browser inspect element"
echo ""

# Create a token sanitization function
sanitize_token() {
    local input="$1"
    # Remove whitespace and common formatting issues
    echo -n "$input" | tr -d ' \t\n\r' | sed 's/^"//;s/"$//'
}

# Test the function
echo "Testing token sanitization:"
echo "Input: \"  squ_1234567890abcdef...  \""
echo "Output: $(sanitize_token "  squ_1234567890abcdef...  ")"
echo ""
echo "Use this function to clean up copied tokens before use"
```

##### Solution 1.3: Update Configuration
```bash
# Update sonar-config.json with new token
jq '.sonarToken = "squ_44characterlongtoken..."' sonar-config.json > temp.json
mv temp.json sonar-config.json

# Regenerate properties file
bash scripts/sonar/sonar_scanner.sh create_properties
```

##### Solution 1.4: Test Token Validity
```bash
# Test token authentication
TOKEN="squ_44characterlongtoken..."
curl -u "$TOKEN:" "http://localhost:9000/api/authentication/validate"

# Expected: {"valid":true}
```

### Issue 2: Token Format Errors
**Symptoms**: Token appears as "sqp_" instead of "squ_"
**Root Cause**: Using wrong token type or generation method

#### Solutions
```bash
# Generate correct user token (squ_ prefix)
curl -X POST -u admin:admin "http://localhost:9000/api/user_tokens/generate?name=correct-token"

# NOT project token (sqp_ prefix) - these are different
# User tokens: squ_ (for analysis)
# Project tokens: sqp_ (for project administration)
```

### Issue 3: Token Already Exists
**Symptoms**: "Token name already exists" error
**Root Cause**: Trying to generate token with existing name

#### Solutions
```bash
# Use unique token name with timestamp
TOKEN_NAME="scanner-token-$(date +%s)"
curl -X POST -u admin:admin "http://localhost:9000/api/user_tokens/generate?name=$TOKEN_NAME"

# Or revoke existing token first
curl -X POST -u admin:admin "http://localhost:9000/api/user_tokens/revoke?name=existing-token"
```

## Network & Connectivity Issues

### Issue 1: Scanner Cannot Reach Server
**Symptoms**: "Failed to query server version" or connection refused
**Root Cause**: Wrong URL, network misconfiguration, Docker network issues

#### Solutions

##### Solution 1.1: Check Server Status
```bash
# Test server from host
curl -I "http://localhost:9000/api/system/status"

# Expected: HTTP/1.1 200 OK

# Test from Docker container
docker run --rm --network docker_sonarqube_network \
  alpine/curl "http://sonarqube:9000/api/system/status"

# Expected: {"status":"UP"}
```

##### Solution 1.2: Verify Docker Network
```bash
# Check if network exists
docker network ls | grep sonarqube

# Expected: docker_sonarqube_network

# Inspect network
docker network inspect docker_sonarqube_network

# Create network if missing
docker network create docker_sonarqube_network
```

##### Solution 1.3: Fix URL Configuration
```bash
# Use correct Docker internal URL (not localhost)
SONAR_HOST_URL="http://sonarqube:9000"  # ✅ Correct for scanner
# NOT: http://localhost:9000          # ❌ Wrong for scanner

# Update configuration
jq '.sonarHostUrl = "http://sonarqube:9000"' sonar-config.json > temp.json
mv temp.json sonar-config.json
```

### Issue 2: Port Conflicts
**Symptoms**: Port 9000 already in use
**Root Cause**: Another service using port 9000

#### Solutions
```bash
# Check what's using port 9000
sudo netstat -tlnp | grep :9000

# Stop conflicting service
sudo systemctl stop conflicting-service

# Or change SonarQube port in docker-compose.yml
ports:
  - "9001:9000"  # Use different host port
```

### Issue 3: Firewall Blocking Access
**Symptoms**: Connection timeout from browser
**Root Cause**: Firewall blocking port 9000

#### Solutions
```bash
# Ubuntu/Debian
sudo ufw allow 9000/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=9000/tcp
sudo firewall-cmd --reload

# Check if port is open
telnet localhost 9000
```

## Configuration Issues

### Issue 1: Invalid JSON Syntax
**Symptoms**: "parse error" or JSON validation failures
**Root Cause**: Syntax errors in sonar-config.json

#### Solutions
```bash
# Validate JSON syntax
jq . sonar-config.json

# Common fixes:
# - Add missing commas
# - Remove trailing commas
# - Quote unquoted strings
# - Fix escape characters

# Example fix:
# Before: {"key":"value"}
# After:  {"key":"value",}
```

### Issue 2: Missing Required Fields
**Symptoms**: "Required field 'projectKey' is missing"
**Root Cause**: Incomplete configuration

#### Solutions
```bash
# Check required fields
REQUIRED_FIELDS=("projectKey" "projectName" "projectVersion" "language" "sourceDirs" "sonarHostUrl" "sonarToken")

for field in "${REQUIRED_FIELDS[@]}"; do
    if jq -e ".$field" sonar-config.json > /dev/null; then
        echo "✅ $field exists"
    else
        echo "❌ $field missing - adding default value"
        jq ".$field = \"default-$field\"" sonar-config.json > temp.json
        mv temp.json sonar-config.json
    fi
done
```

### Issue 3: Invalid Project Key
**Symptoms**: "Invalid project key" error
**Root Cause**: Project key contains invalid characters

#### Solutions
```bash
# Valid project key format: letters, numbers, hyphens, underscores only
PROJECT_KEY="my-project-key"  # ✅ Valid
PROJECT_KEY="my project key"  # ❌ Invalid (spaces)
PROJECT_KEY="my.project.key"  # ❌ Invalid (dots)

# Fix project key
jq '.projectKey = "my-project-key"' sonar-config.json > temp.json
mv temp.json sonar-config.json
```

## Coverage Generation Issues

### Issue 1: Cargo Tarpaulin Not Found
**Symptoms**: "cargo: No such command: `tarpaulin`"
**Root Cause**: cargo-tarpaulin not installed

#### Solutions
```bash
# Install cargo-tarpaulin
cargo install cargo-tarpaulin

# Verify installation
cargo tarpaulin --version

# If installation fails, install dependencies first
sudo apt-get install -y pkg-config libssl-dev
cargo install cargo-tarpaulin
```

### Issue 2: Coverage File Not Generated
**Symptoms**: "coverage/cobertura.xml not found"
**Root Cause**: Coverage generation failed

#### Solutions
```bash
# Check coverage directory
ls -la coverage/

# Run coverage manually to debug
cargo tarpaulin --output-dir coverage --skip-clean --verbose

# Check for compilation errors
cargo test

# Common fixes:
# - Fix compilation errors first
# - Ensure tests exist and pass
# - Check file permissions
```

### Issue 3: Coverage XML Parsing Error
**Symptoms**: "Error during parsing of the generic coverage report"
**Root Cause**: XML format incompatible with SonarQube

#### Solutions
```bash
# Solution 1: Exclude coverage temporarily
# Remove coverage line from sonar-project.properties
sed -i '/sonar.coverageReportPaths/d' sonar-project.properties

# Solution 2: Fix XML format
# Ensure XML is well-formed
xmllint --format coverage/cobertura.xml > coverage/cobertura_fixed.xml
mv coverage/cobertura_fixed.xml coverage/cobertura.xml

# Solution 3: Use different output format
cargo tarpaulin --output-dir coverage --output-format xml --skip-clean
```

## Scanner Execution Issues

### Issue 1: SonarScanner Not Found
**Symptoms**: "Command not found: sonar-scanner"
**Root Cause**: SonarScanner CLI not installed locally

#### Solutions
```bash
# Solution 1: Use Docker (recommended)
# Already configured in scripts

# Solution 2: Install locally
# Download SonarScanner CLI
wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-8.0.1.6346-linux.zip

# Extract and install
unzip sonar-scanner-cli-*.zip
sudo mv sonar-scanner-8.0.1.6346-linux /opt/sonar-scanner
sudo ln -s /opt/sonar-scanner/bin/sonar-scanner /usr/local/bin/

# Test installation
sonar-scanner --version
```

### Issue 2: Scanner Memory Issues
**Symptoms**: "Java heap space error" or OutOfMemoryError
**Root Cause**: Insufficient memory allocated to scanner

#### Solutions
```bash
# Increase scanner memory
export SONAR_SCANNER_JAVA_OPTS="-Xmx4g"

# Or use Docker with memory limit
docker run --rm --network docker_sonarqube_network \
  -e SONAR_SCANNER_JAVA_OPTS="-Xmx4g" \
  -e SONAR_HOST_URL="http://sonarqube:9000" \
  -e SONAR_TOKEN="$TOKEN" \
  -v "$(pwd):/project" \
  sonarsource/sonar-scanner-cli \
  -Dproject.settings=/project/sonar-project.properties
```

### Issue 3: Scanner Timeout
**Symptoms**: Scanner hangs or times out
**Root Cause**: Large project or network issues

#### Solutions
```bash
# Increase timeout
docker run --rm --network docker_sonarqube_network \
  -e SONAR_SCANNER_JAVA_OPTS="-Xmx4g -Dsonar.timeout=600" \
  -e SONAR_HOST_URL="http://sonarqube:9000" \
  -e SONAR_TOKEN="$TOKEN" \
  -v "$(pwd):/project" \
  sonarsource/sonar-scanner-cli \
  -Dproject.settings=/project/sonar-project.properties

# Or reduce analysis scope
# Update exclusions in sonar-config.json
jq '.exclusions += ["generated/**", "**/*.pb.go"]' sonar-config.json > temp.json
mv temp.json sonar-config.json
```

## Server Performance Issues

### Issue 1: Server Startup Slow
**Symptoms**: SonarQube takes >5 minutes to start
**Root Cause**: Insufficient resources, database initialization

#### Solutions
```bash
# Check system resources
free -h
df -h

# Increase Docker memory limits
# Docker Desktop -> Settings -> Resources -> Memory -> 4GB+

# Check database logs
docker logs sonarqube_db

# Restart services
docker-compose down -v
docker-compose up -d
```

### Issue 2: Server Out of Memory
**Symptoms**: Container crashes, OOM errors in logs
**Root Cause**: Insufficient memory allocation

#### Solutions
```bash
# Add memory limits to docker-compose.yml
services:
  sonarqube:
    deploy:
      resources:
        limits:
          memory: 4g
        reservations:
          memory: 2g

# Or increase system swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Issue 3: Database Connection Issues
**Symptoms**: "Could not connect to database" errors
**Root Cause**: Database not ready, network issues

#### Solutions
```bash
# Start database first
docker-compose up -d db

# Wait for database to be ready
until docker exec sonarqube_db pg_isready -U sonar; do
  echo "Waiting for database..."
  sleep 5
done

# Then start SonarQube
docker-compose up -d sonarqube
```

## Docker & Container Issues

### Issue 1: Docker Permission Denied
**Symptoms**: "permission denied while trying to connect to Docker daemon"
**Root Cause**: User not in docker group

#### Solutions
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply group membership
newgrp docker

# Or use sudo (not recommended)
sudo docker run hello-world
```

### Issue 2: Container Not Starting
**Symptoms**: Container exits immediately
**Root Cause**: Port conflicts, volume issues, configuration errors

#### Solutions
```bash
# Check container logs
docker logs sonarqube

# Check container status
docker ps -a | grep sonarqube

# Inspect container
docker inspect sonarqube

# Common fixes:
# - Free up port 9000
# - Check volume permissions
# - Verify environment variables
```

### Issue 3: Network Issues
**Symptoms**: Containers cannot communicate
**Root Cause: Network misconfiguration

#### Solutions
```bash
# Recreate network
docker network rm docker_sonarqube_network
docker network create docker_sonarqube_network

# Restart services
docker-compose down
docker-compose up -d

# Test connectivity
docker exec sonarqube ping sonarqube_db
```

## Real-World Troubleshooting Scenarios

### Scenario 1: First-Time Setup Failure
**Problem**: Complete setup fails with multiple errors

#### Step-by-Step Resolution
```bash
#!/bin/bash
# complete_troubleshoot.sh

echo "=== Complete SonarQube Troubleshooting ==="

# Step 1: Check Docker
echo "1. Checking Docker..."
if ! docker --version > /dev/null; then
    echo "❌ Docker not installed or accessible"
    exit 1
fi
echo "✅ Docker OK"

# Step 2: Check Docker Compose
echo "2. Checking Docker Compose..."
if ! docker-compose --version > /dev/null; then
    echo "❌ Docker Compose not installed"
    exit 1
fi
echo "✅ Docker Compose OK"

# Step 3: Check network
echo "3. Checking network..."
if ! docker network ls | grep -q sonarqube; then
    echo "Creating SonarQube network..."
    docker network create docker_sonarqube_network
fi
echo "✅ Network OK"

# Step 4: Start server
echo "4. Starting SonarQube server..."
cd ../code-quality/deployment/docker
docker-compose down -v
docker-compose up -d db
sleep 30
docker-compose up -d sonarqube

# Step 5: Wait for server
echo "5. Waiting for server..."
until curl -s http://localhost:9000/api/system/status | grep -q "UP"; do
    echo "Waiting for SonarQube..."
    sleep 10
done
echo "✅ Server OK"

# Step 6: Generate token
echo "6. Generating token..."
TOKEN_RESPONSE=$(curl -s -X POST -u admin:admin \
  "http://localhost:9000/api/user_tokens/generate?name=troubleshoot-token")

if echo "$TOKEN_RESPONSE" | jq -e '.token' > /dev/null; then
    TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.token')
    echo "✅ Token generated: ${TOKEN:0:20}..."
else
    echo "❌ Token generation failed"
    exit 1
fi

# Step 7: Create project
echo "7. Creating project..."
PROJECT_RESPONSE=$(curl -s -X POST -u admin:admin \
  "http://localhost:9000/api/projects/create?project=troubleshoot-test&name=Troubleshoot%20Test")

if echo "$PROJECT_RESPONSE" | jq -e '.project' > /dev/null; then
    echo "✅ Project created"
else
    echo "⚠️ Project might already exist"
fi

# Step 8: Update config
echo "8. Updating configuration..."
cd ../../distributedTraceAnalysisEngine
jq '.sonarToken = "'$TOKEN'"' sonar-config.json > temp.json
mv temp.json sonar-config.json

echo "=== Troubleshooting Complete ==="
echo "Token: $TOKEN"
echo "Next: make sonar-analyze"
```

### Scenario 2: CI/CD Pipeline Issues
**Problem**: Analysis works locally but fails in CI

#### Solutions
```bash
# CI-specific troubleshooting
#!/bin/bash
# ci_troubleshoot.sh

echo "=== CI/CD Troubleshooting ==="

# Check environment variables
echo "1. Checking environment..."
if [[ -z "$SONAR_TOKEN" ]]; then
    echo "❌ SONAR_TOKEN not set"
    exit 1
fi

if [[ -z "$CI_PROJECT_NAME" ]]; then
    echo "❌ CI_PROJECT_NAME not set"
    exit 1
fi
echo "✅ Environment OK"

# Check Docker in CI
echo "2. Checking Docker..."
if ! docker --version > /dev/null; then
    echo "❌ Docker not available in CI"
    exit 1
fi
echo "✅ Docker OK"

# Check network
echo "3. Checking network..."
if ! docker network ls | grep -q sonarqube; then
    echo "Creating SonarQube network in CI..."
    docker network create docker_sonarqube_network
fi
echo "✅ Network OK"

# Check SonarQube server
echo "4. Checking SonarQube server..."
if ! curl -s "$SONAR_HOST_URL/api/system/status" > /dev/null; then
    echo "❌ SonarQube server not accessible"
    exit 1
fi
echo "✅ Server OK"

# Test token
echo "5. Testing token..."
if ! curl -u "$SONAR_TOKEN:" "$SONAR_HOST_URL/api/authentication/validate" > /dev/null; then
    echo "❌ Token validation failed"
    exit 1
fi
echo "✅ Token OK"

echo "=== CI/CD Troubleshooting Complete ==="
```

## Prevention Strategies

### 1. Automated Health Checks
```bash
#!/bin/bash
# health_check.sh

echo "=== SonarQube Health Check ==="

# Check server
if curl -s http://localhost:9000/api/system/status | grep -q "UP"; then
    echo "✅ Server healthy"
else
    echo "❌ Server unhealthy"
    exit 1
fi

# Check token
if [[ -f sonar-config.json ]]; then
    TOKEN=$(jq -r '.sonarToken' sonar-config.json)
    if curl -u "$TOKEN:" http://localhost:9000/api/authentication/validate > /dev/null; then
        echo "✅ Token valid"
    else
        echo "❌ Token invalid"
        exit 1
    fi
else
    echo "❌ Configuration file missing"
    exit 1
fi

# Check dependencies
if command -v cargo-tarpaulin &> /dev/null; then
    echo "✅ Dependencies installed"
else
    echo "❌ Dependencies missing"
    exit 1
fi

echo "=== Health Check Complete ==="
```

### 2. Configuration Validation
```bash
#!/bin/bash
# validate_setup.sh

echo "=== Setup Validation ==="

# Validate JSON
if jq . sonar-config.json > /dev/null; then
    echo "✅ JSON valid"
else
    echo "❌ JSON invalid"
    exit 1
fi

# Check required fields
REQUIRED_FIELDS=("projectKey" "projectName" "language" "sonarHostUrl" "sonarToken")
for field in "${REQUIRED_FIELDS[@]}"; do
    if jq -e ".$field" sonar-config.json > /dev/null; then
        echo "✅ $field present"
    else
        echo "❌ $field missing"
        exit 1
    fi
done

# Check scripts
SCRIPTS=("utils.sh" "config_loader.sh" "server_manager.sh" "coverage_generator.sh" "sonar_scanner.sh" "orchestrator.sh")
for script in "${SCRIPTS[@]}"; do
    if [[ -f "scripts/sonar/$script" ]]; then
        echo "✅ $script exists"
    else
        echo "❌ $script missing"
        exit 1
    fi
done

echo "=== Validation Complete ==="
```

### 3. Monitoring Setup
```bash
#!/bin/bash
# monitor_setup.sh

# Monitor server resources
docker stats --no-stream sonarqube

# Monitor disk usage
df -h

# Monitor memory usage
free -h

# Check logs for errors
docker logs sonarqube 2>&1 | grep -i error | tail -5
```

## Quick Reference Commands

### Emergency Commands
```bash
# Restart everything
docker-compose down -v && docker-compose up -d

# Generate new token
curl -X POST -u admin:admin "http://localhost:9000/api/user_tokens/generate?name=emergency-token"

# Validate setup
bash validate_setup.sh

# Check health
bash health_check.sh
```

### Diagnostic Commands
```bash
# Check all services
docker-compose ps

# Check logs
docker logs -f sonarqube

# Test connectivity
curl -I http://localhost:9000/api/system/status

# Validate configuration
jq . sonar-config.json
```

### Recovery Commands
```bash
# Reset configuration
git checkout sonar-config.json

# Regenerate properties
bash scripts/sonar/sonar_scanner.sh create_properties

# Clean coverage
rm -rf coverage/
make sonar-coverage
```

## Support Escalation

### When to Seek Help
- Multiple failed attempts with same error
- Error not documented in this guide
- Performance issues affecting team productivity
- Security concerns

### Information to Collect
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

### Support Channels
- Internal team: Create issue in project repository
- SonarQube Community: https://community.sonarsource.com/
- Docker Support: https://forums.docker.com/

## Conclusion

This troubleshooting guide covers the most common issues encountered with the SonarQube DTAE setup. The key principles are:

1. **Verify before fixing** - Always validate assumptions
2. **Check logs** - Logs contain valuable diagnostic information  
3. **Test incrementally** - Fix one issue at a time
4. **Document solutions** - Share fixes with the team
5. **Prevent issues** - Use health checks and validation

By following this guide, most issues can be resolved quickly and efficiently. For complex or persistent issues, don't hesitate to seek additional support.

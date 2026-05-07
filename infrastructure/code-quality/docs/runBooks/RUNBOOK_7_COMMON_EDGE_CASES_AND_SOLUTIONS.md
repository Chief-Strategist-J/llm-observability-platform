# RUNBOOK 7: Common Edge Cases and Solutions

## Overview

This runbook documents common edge cases encountered during SonarQube setup and execution, along with their solutions. These issues can significantly extend setup time if not handled properly.

## Table of Contents

1. [Authentication Edge Cases](#authentication-edge-cases)
2. [Coverage Sensor Conflicts](#coverage-sensor-conflicts)
3. [Environment Constraint Issues](#environment-constraint-issues)
4. [Network Connectivity Problems](#network-connectivity-problems)
5. [Tool Installation Issues](#tool-installation-issues)
6. [Configuration File Conflicts](#configuration-file-conflicts)

---

## Authentication Edge Cases

### Issue: SonarQube Token Authentication Failures

**Symptoms:**
```
ERROR Failed to query server version: GET http://localhost:9000/api/v2/analysis/version failed with HTTP 401 Unauthorized
```

**Root Cause:**
- Using deprecated `sonar.login` property instead of `sonar.token`
- Invalid or expired tokens
- Missing token generation step

**Solutions:**

#### Solution 1: Generate Token via API
```bash
# Generate token using admin credentials
TOKEN=$(curl -s -X POST -u admin:PASSWORD \
  "http://localhost:9000/api/user_tokens/generate?name=project-$(date +%s)" \
  | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

# Use the token in analysis
docker run --rm --network host \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli:latest \
  -Dsonar.token="$TOKEN" \
  -Dsonar.host.url=http://localhost:9000
```

#### Solution 2: Update Properties File
```properties
# Remove deprecated property
# sonar.login=admin  # DELETE THIS LINE

# Use token instead
sonar.token=squ_your_actual_token_here
```

#### Solution 3: Add Token Generation to Scripts
```bash
# In sonar_scanner.sh
generate_token() {
  local token=$(curl -s -X POST -u admin:PASSWORD \
    "http://localhost:9000/api/user_tokens/generate?name=project-$(date +%s)" \
    | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
  
  if [[ -z "$token" ]]; then
    log_error "Failed to generate SonarQube token"
    return 1
  fi
  
  echo "$token"
}
```

**Prevention:**
- Always use `sonar.token` instead of `sonar.login`
- Add token validation before running analysis
- Implement automatic token generation in orchestrator scripts

---

## Coverage Sensor Conflicts

### Issue: Generic Coverage Sensor vs Cobertura Sensor Conflict

**Symptoms:**
```
INFO Sensor Cobertura Sensor for Python coverage [python] (done) | time=100ms
INFO Sensor Generic Coverage Report
ERROR Error during parsing of the generic coverage report '/usr/src/coverage/coverage.xml'
```

**Root Cause:**
- Both `sonar.coverageReportPaths` and `sonar.python.coverage.reportPaths` are set
- Generic Coverage sensor expects different XML format than Cobertura
- Both sensors try to parse the same file

**Solutions:**

#### Solution 1: Remove Generic Coverage Path from Properties
```bash
# Edit sonar-project.properties
# REMOVE THIS LINE:
# sonar.coverageReportPaths=coverage/coverage.xml

# KEEP ONLY:
sonar.python.coverage.reportPaths=coverage/coverage.xml
```

#### Solution 2: Update Properties Generation Script
```bash
# In sonar_scanner.sh - create_properties()
cat > "$properties_file" << EOF
sonar.projectKey=$SONAR_PROJECT_KEY
sonar.projectName=$SONAR_PROJECT_NAME
sonar.projectVersion=$SONAR_PROJECT_VERSION
sonar.language=$SONAR_LANGUAGE
sonar.sources=$SONAR_SOURCE_DIRS
sonar.tests=$SONAR_TEST_DIRS
sonar.exclusions=$SONAR_EXCLUSIONS
sonar.host.url=$SONAR_HOST_URL
# ONLY Python-specific coverage path
sonar.python.coverage.reportPaths=$COVERAGE_OUTPUT_DIR/coverage.xml
sonar.scm.disabled=true
EOF
```

#### Solution 3: Disable Generic Sensor Explicitly
```bash
docker run --rm --network host \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli:latest \
  -Dsonar.coverageReportPaths= \
  -Dsonar.python.coverage.reportPaths=coverage/coverage.xml
```

**Prevention:**
- Never set `sonar.coverageReportPaths` for Python projects
- Always use language-specific coverage paths (e.g., `sonar.python.coverage.reportPaths`)
- Add validation in scripts to prevent conflicting properties

---

## Environment Constraint Issues

### Issue: Externally Managed Python Environment

**Symptoms:**
```
ERROR: externally-managed-environment
error: externally-managed-environment
```

**Root Cause:**
- System Python environment is externally managed (PEP 668)
- `pip install` is blocked to prevent system package conflicts

**Solutions:**

#### Solution 1: Use --user Flag
```bash
pip install --user pytest-cov
```

#### Solution 2: Skip Installation if Already Available
```bash
# In coverage_generator.sh
install_pytest_cov() {
  if python3 -c "import pytest_cov" &>/dev/null; then
    log_info "pytest-cov is already installed"
    return 0
  fi

  log_info "Installing pytest-cov..."
  if pip install --user pytest-cov; then
    log_success "pytest-cov installed successfully"
    return 0
  else
    log_error "Failed to install pytest-cov"
    return 1
  fi
}
```

#### Solution 3: Skip Coverage Generation Gracefully
```bash
generate_coverage() {
  if ! install_pytest_cov; then
    log_info "Skipping coverage generation due to missing dependencies"
    return 0
  fi
  
  # Continue with coverage generation
}
```

**Prevention:**
- Always check if packages are already installed before attempting installation
- Use `--user` flag for pip installations
- Provide graceful fallback when dependencies are unavailable
- Document required dependencies in project README

---

## Network Connectivity Problems

### Issue: SonarQube Server Connection Failures

**Symptoms:**
```
ERROR Cannot connect to SonarQube server at http://sonarqube:9000
ERROR Failed to query server version
```

**Root Cause:**
- Using Docker network name (`sonarqube:9000`) from host machine
- Scanner running in different network namespace than SonarQube server
- Incorrect host URL configuration

**Solutions:**

#### Solution 1: Use Localhost with Host Networking
```bash
# In sonar_scanner.sh
docker run --rm --network host \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli:latest \
  -Dsonar.host.url=http://localhost:9000
```

#### Solution 2: Add Connection Validation
```bash
# In sonar_scanner.sh
check_sonarqube_connection() {
  if ! curl -s "http://localhost:9000/api/system/status" > /dev/null; then
    log_error "Cannot connect to SonarQube server at http://localhost:9000"
    return 1
  fi
  log_info "SonarQube server is reachable"
  return 0
}
```

#### Solution 3: Update Configuration Files
```properties
# In sonar-config.json
"sonarHostUrl": "http://localhost:9000"  # Use localhost, not sonarqube:9000
```

**Prevention:**
- Always use `localhost:9000` when scanner runs on host machine
- Add connection checks before running analysis
- Document network topology in project setup guide
- Use host networking for Docker containers when possible

---

## Tool Installation Issues

### Issue: sonar-scanner CLI Not Installed

**Symptoms:**
```
ERROR sonar-scanner is not installed
ERROR command not found: sonar-scanner
```

**Root Cause:**
- sonar-scanner not installed locally
- Not in system PATH
- Version mismatch

**Solutions:**

#### Solution 1: Use Docker Image (Recommended)
```bash
docker run --rm --network host \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli:latest
```

#### Solution 2: Install sonar-scanner Locally
```bash
# Download and install
wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-4.8.0.2856-linux.zip
unzip sonar-scanner-cli-4.8.0.2856-linux.zip
export PATH=$PATH:$PWD/sonar-scanner-4.8.0.2856-linux/bin
```

#### Solution 3: Add Tool Check in Scripts
```bash
# In sonar_scanner.sh
check_sonar_scanner() {
  if check_command "sonar-scanner"; then
    return 0
  fi
  
  if check_command "docker"; then
    log_info "Using Docker-based sonar-scanner"
    return 0
  fi
  
  log_error "Neither sonar-scanner nor Docker is available"
  return 1
}
```

**Prevention:**
- Prefer Docker-based scanner to avoid installation issues
- Add tool availability checks in orchestrator scripts
- Document Docker as the recommended installation method
- Provide fallback to local installation when Docker is unavailable

---

## Database Data Directory Permission Issues

### Issue: AccessDeniedException When Scanning Projects with Database Data

**Symptoms:**
```
ERROR Error during SonarScanner Engine execution
java.io.UncheckedIOException: java.nio.file.AccessDeniedException: /usr/src/data/mongodb-7/diagnostic.data
Caused by: java.nio.file.AccessDeniedException: /usr/src/data/mongodb-7/diagnostic.data
```

**Root Cause:**
- Project contains database data directories (MongoDB, PostgreSQL, etc.) with restricted permissions
- Python sensor attempts to scan all directories before exclusions are applied
- Database data files (diagnostic.data, journal, etc.) have restricted access permissions
- Exclusion patterns don't prevent the sensor from attempting to access files during initial discovery

**Solutions:**

#### Solution 1: Scan from Subdirectory (Recommended)
```bash
# In sonar_scanner.sh - run_scan()
run_scan() {
  # Change to the actual source directory instead of project root
  cd "$PROJECT_ROOT/infrastructure"
  
  docker run --rm --network host \
    -v "$(pwd):/usr/src" \
    sonarsource/sonar-scanner-cli:latest \
    -Dsonar.projectKey=messaging \
    -Dsonar.sources=. \
    # ... other parameters
}
```

#### Solution 2: Explicit Source Directory Specification
```bash
docker run --rm --network host \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli:latest \
  -Dsonar.projectKey=messaging \
  -Dsonar.sources=infrastructure \
  -Dsonar.exclusions=**/__pycache__/**,**/data/** \
  # ... other parameters
```

**Note:** Exclusions alone may not work as the Python sensor accesses files before applying exclusion patterns.

#### Solution 3: Move Data Directory Outside Project
```bash
# Move data directory outside of source control
mv data/ ../data-backup/

# Run analysis
./scripts/sonar/orchestrator.sh

# Restore if needed
mv ../data-backup/ data/
```

#### Solution 4: Use .dockerignore or .gitignore
```dockerignore
# .dockerignore
data/
**/diagnostic.data
**/journal
```

```gitignore
# .gitignore
data/
**/diagnostic.data
**/journal
```

**Prevention:**
- Keep database data directories outside of source code directories
- Use separate volumes or directories for runtime data
- Structure projects with clear separation: `src/`, `tests/`, `data/`
- Document which directories should be scanned vs. excluded
- Use Docker volumes for database data instead of local directories

---

## Configuration File Conflicts

### Issue: Properties File Recreation Overwrites Manual Fixes

**Symptoms:**
- Manual fixes to `sonar-project.properties` are overwritten
- Same errors persist after manual correction
- Properties file regenerated during each run

**Root Cause:**
- Orchestrator scripts regenerate properties file on each run
- Manual edits are lost when script runs again
- Properties generation logic includes problematic settings

**Solutions:**

#### Solution 1: Fix the Properties Generation Script
```bash
# In sonar_scanner.sh - create_properties()
# Ensure this function generates correct properties
cat > "$properties_file" << EOF
sonar.projectKey=$SONAR_PROJECT_KEY
sonar.projectName=$SONAR_PROJECT_NAME
sonar.projectVersion=$SONAR_PROJECT_VERSION
sonar.language=$SONAR_LANGUAGE
sonar.sources=$SONAR_SOURCE_DIRS
sonar.tests=$SONAR_TEST_DIRS
sonar.exclusions=$SONAR_EXCLUSIONS
sonar.host.url=$SONAR_HOST_URL
# Only language-specific coverage
sonar.python.coverage.reportPaths=$COVERAGE_OUTPUT_DIR/coverage.xml
# Disable SCM to avoid warnings
sonar.scm.disabled=true
EOF
```

#### Solution 2: Add Properties Validation
```bash
validate_properties() {
  local properties_file="$PROJECT_ROOT/sonar-project.properties"
  
  # Check for conflicting coverage paths
  if grep -q "sonar.coverageReportPaths=" "$properties_file" && \
     grep -q "sonar.python.coverage.reportPaths=" "$properties_file"; then
    log_error "Conflicting coverage paths in properties file"
    return 1
  fi
  
  # Check for deprecated properties
  if grep -q "sonar.login=" "$properties_file"; then
    log_error "Deprecated sonar.login property found"
    return 1
  fi
  
  return 0
}
```

#### Solution 3: Use Command-Line Properties Instead
```bash
# Skip properties file generation and use command-line
docker run --rm --network host \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli:latest \
  -Dsonar.projectKey=log-intelligent \
  -Dsonar.projectName="Log Intelligent" \
  -Dsonar.language=py \
  -Dsonar.sources=api,client,domain \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.token="$TOKEN"
```

**Prevention:**
- Fix properties generation script at the source
- Add validation to catch configuration errors early
- Consider using command-line properties for simple projects
- Document which properties are safe to modify manually

---

## Quick Reference: Common Error Messages and Solutions

| Error Message | Root Cause | Solution |
|--------------|------------|----------|
| `HTTP 401 Unauthorized` | Invalid token | Generate new token via API |
| `Cannot resolve file path dummy.py` | Invalid coverage XML | Use proper Cobertura format |
| `externally-managed-environment` | Python environment constraint | Use `--user` flag or skip install |
| `Cannot connect to SonarQube` | Network issue | Use `localhost:9000` with host networking |
| `sonar-scanner not found` | Tool not installed | Use Docker image |
| `Error parsing generic coverage report` | Sensor conflict | Remove `sonar.coverageReportPaths` |
| `AccessDeniedException: /usr/src/data/mongodb-7/diagnostic.data` | Database data directory permissions | Scan from subdirectory or move data outside project |

---

## Best Practices to Avoid Edge Cases

1. **Always use Docker-based sonar-scanner** to avoid installation issues
2. **Generate tokens dynamically** via API instead of hardcoding
3. **Use language-specific coverage paths** (e.g., `sonar.python.coverage.reportPaths`)
4. **Add connection checks** before running analysis
5. **Implement graceful fallbacks** for missing dependencies
6. **Validate configuration** before running analysis
7. **Use host networking** for Docker containers when scanner and server are on same machine
8. **Add comprehensive logging** to help diagnose issues
9. **Document all edge cases** in project documentation
10. **Test scripts in isolated environments** before deployment
11. **Keep database data directories separate from source code** to avoid permission issues
12. **Scan from specific source directories** rather than project root to avoid unwanted directories

---

## Related Documentation

- [RUNBOOK_1_NEW_PROJECT_SETUP.md](RUNBOOK_1_NEW_PROJECT_SETUP.md) - Initial project setup
- [RUNBOOK_6_TROUBLESHOOTING_GUIDE.md](RUNBOOK_6_TROUBLESHOOTING_GUIDE.md) - General troubleshooting
- [TECHNICAL_REFERENCE_GUIDE.md](TECHNICAL_REFERENCE_GUIDE.md) - Technical architecture details

---

## Version History

- **v1.1** (2026-05-07): Added database data directory permission issues edge case from messaging project setup
- **v1.0** (2026-05-07): Initial version documenting edge cases from logIntelligent project setup

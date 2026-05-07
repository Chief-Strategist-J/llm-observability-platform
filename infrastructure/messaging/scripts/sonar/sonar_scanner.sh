#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/utils.sh"
source "$SCRIPT_DIR/config_loader.sh"

validate_properties() {
  local properties_file="$PROJECT_ROOT/sonar-project.properties"
  
  if [[ ! -f "$properties_file" ]]; then
    log_error "Properties file not found: $properties_file"
    return 1
  fi
  
  log_info "Validating properties file..."
  
  # Check for conflicting coverage paths
  if grep -q "sonar.coverageReportPaths=" "$properties_file" && \
     grep -q "sonar.python.coverage.reportPaths=" "$properties_file"; then
    log_error "Conflicting coverage paths detected: both generic and Python-specific paths set"
    return 1
  fi
  
  # Check for deprecated properties
  if grep -q "sonar.login=" "$properties_file"; then
    log_error "Deprecated sonar.login property found - use sonar.token instead"
    return 1
  fi
  
  log_success "Properties file validation passed"
  return 0
}

create_properties() {
  local properties_file="$PROJECT_ROOT/sonar-project.properties"

  log_info "Creating sonar-project.properties..."

  cat > "$properties_file" << EOF
sonar.projectKey=$SONAR_PROJECT_KEY
sonar.projectName=$SONAR_PROJECT_NAME
sonar.projectVersion=$SONAR_PROJECT_VERSION
sonar.language=$SONAR_LANGUAGE
sonar.sources=$SONAR_SOURCE_DIRS
sonar.tests=$SONAR_TEST_DIRS
sonar.exclusions=$SONAR_EXCLUSIONS
sonar.host.url=$SONAR_HOST_URL
sonar.python.coverage.reportPaths=$COVERAGE_OUTPUT_DIR/coverage.xml
sonar.scm.disabled=true
EOF

  if [[ -f "$properties_file" ]]; then
    log_success "sonar-project.properties created successfully"
    validate_properties || return 1
    return 0
  else
    log_error "Failed to create sonar-project.properties"
    return 1
  fi
}

run_scan() {
  cd "$PROJECT_ROOT/infrastructure"

  if ! check_command "docker"; then
    log_error "Docker is not installed or not in PATH"
    return 1
  fi

  log_info "Running SonarQube scan with Docker..."

  # Check if we can connect to SonarQube server (use localhost for host connection)
  if ! curl -s "http://localhost:9000/api/system/status" > /dev/null; then
    log_error "Cannot connect to SonarQube server at http://localhost:9000"
    return 1
  fi

  # Generate token for authentication
  local token=$(curl -s -X POST -u admin:Scaibu@12345678 "http://localhost:9000/api/user_tokens/generate?name=messaging-$(date +%s)" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
  
  if [[ -z "$token" ]]; then
    log_error "Failed to generate SonarQube token"
    return 1
  fi

  # Run SonarQube scan using Docker (map port to host)
  if docker run --rm --network host \
    -v "$(pwd):/usr/src" \
    sonarsource/sonar-scanner-cli:latest \
    -Dsonar.projectKey=messaging \
    -Dsonar.projectName="Messaging SDK" \
    -Dsonar.projectVersion=0.1.0 \
    -Dsonar.language=py \
    -Dsonar.sources=. \
    -Dsonar.exclusions=**/__pycache__/**,**/node_modules/**,**/target/**,*.json,*.yaml,*.yml,*.md,Dockerfile,docker-compose*.yml \
    -Dsonar.host.url=http://localhost:9000 \
    -Dsonar.token="$token" \
    -Dsonar.genericcoverage.reportPaths=""; then
    log_success "SonarQube scan completed successfully"
    log_info "View results at: $SONAR_HOST_URL/dashboard?id=$SONAR_PROJECT_KEY"
    return 0
  else
    log_error "SonarQube scan failed"
    return 1
  fi
}

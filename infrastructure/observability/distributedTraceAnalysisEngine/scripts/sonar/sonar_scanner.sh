#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/utils.sh"
source "$SCRIPT_DIR/config_loader.sh"

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
sonar.login=$SONAR_TOKEN
sonar.coverageReportPaths=$COVERAGE_OUTPUT_DIR/cobertura.xml
EOF

  if [[ -f "$properties_file" ]]; then
    log_success "sonar-project.properties created successfully"
    return 0
  else
    log_error "Failed to create sonar-project.properties"
    return 1
  fi
}

run_scan() {
  cd "$PROJECT_ROOT"

  if ! check_command "sonar-scanner"; then
    log_error "sonar-scanner is not installed"
    log_info "Install sonar-scanner: https://docs.sonarqube.org/latest/analysis/scan/sonarscanner/"
    return 1
  fi

  log_info "Running SonarQube scan..."

  if sonar-scanner; then
    log_success "SonarQube scan completed successfully"
    log_info "View results at: $SONAR_HOST_URL/dashboard?id=$SONAR_PROJECT_KEY"
    return 0
  else
    log_error "SonarQube scan failed"
    return 1
  fi
}

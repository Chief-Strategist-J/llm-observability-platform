#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh"
source "$SCRIPT_DIR/config_loader.sh"
source "$SCRIPT_DIR/server_manager.sh"
source "$SCRIPT_DIR/coverage_generator.sh"
source "$SCRIPT_DIR/sonar_scanner.sh"

orchestrate_analysis() {
  log_info "Starting SonarQube analysis orchestration..."

  if ! load_config; then
    log_error "Failed to load configuration"
    return 1
  fi

  if ! validate_config; then
    log_error "Configuration validation failed"
    return 1
  fi

  if ! start_server; then
    log_error "Failed to start SonarQube server"
    log_info "Check that Docker is running and SonarQube container is accessible"
    return 1
  fi

  log_info "Attempting coverage generation (may be skipped if dependencies unavailable)"
  if ! generate_coverage; then
    log_info "Coverage generation skipped - analysis will continue without coverage data"
  fi

  if ! create_properties; then
    log_error "Failed to create sonar-project.properties"
    return 1
  fi

  log_info "Running SonarQube scan with Docker (this may take several minutes)..."
  if ! run_scan; then
    log_error "Failed to run SonarQube scan"
    log_info "Common causes:"
    log_info "  - Authentication issues: Check SonarQube credentials in sonar_scanner.sh"
    log_info "  - Network issues: Ensure SonarQube server is running at localhost:9000"
    log_info "  - Coverage file issues: Check coverage/coverage.xml format"
    return 1
  fi

  log_success "SonarQube analysis completed successfully"
  log_info "View results at: $SONAR_HOST_URL/dashboard?id=$SONAR_PROJECT_KEY"
  return 0
}

main() {
  orchestrate_analysis
  exit $?
}

main "$@"

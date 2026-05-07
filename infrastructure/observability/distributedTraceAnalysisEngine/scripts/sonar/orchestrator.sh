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
    return 1
  fi

  if ! generate_coverage; then
    log_error "Failed to generate coverage"
    return 1
  fi

  if ! create_properties; then
    log_error "Failed to create sonar-project.properties"
    return 1
  fi

  if ! run_scan; then
    log_error "Failed to run SonarQube scan"
    return 1
  fi

  log_success "SonarQube analysis completed successfully"
  return 0
}

main() {
  orchestrate_analysis
  exit $?
}

main "$@"

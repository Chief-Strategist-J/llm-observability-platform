#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/utils.sh"

CONFIG_FILE="$PROJECT_ROOT/sonar-config.json"

load_config() {
  if [[ ! -f "$CONFIG_FILE" ]]; then
    log_error "Configuration file not found: $CONFIG_FILE"
    return 1
  fi

  if ! check_command "jq"; then
    log_error "jq is required to parse configuration"
    return 1
  fi

  export SONAR_PROJECT_KEY
  export SONAR_PROJECT_NAME
  export SONAR_PROJECT_VERSION
  export SONAR_LANGUAGE
  export SONAR_SOURCE_DIRS
  export SONAR_TEST_DIRS
  export SONAR_EXCLUSIONS
  export SONAR_HOST_URL
  export SONAR_TOKEN
  export COVERAGE_TOOL
  export COVERAGE_OUTPUT_FORMAT
  export COVERAGE_OUTPUT_DIR

  SONAR_PROJECT_KEY=$(jq -r '.projectKey' "$CONFIG_FILE")
  SONAR_PROJECT_NAME=$(jq -r '.projectName' "$CONFIG_FILE")
  SONAR_PROJECT_VERSION=$(jq -r '.projectVersion' "$CONFIG_FILE")
  SONAR_LANGUAGE=$(jq -r '.language' "$CONFIG_FILE")
  SONAR_SOURCE_DIRS=$(jq -r '.sourceDirs[]' "$CONFIG_FILE" | tr '\n' ',')
  SONAR_TEST_DIRS=$(jq -r '.testDirs[]' "$CONFIG_FILE" | tr '\n' ',')
  SONAR_EXCLUSIONS=$(jq -r '.exclusions[]' "$CONFIG_FILE" | tr '\n' ',')
  SONAR_HOST_URL=$(jq -r '.sonarHostUrl' "$CONFIG_FILE")
  SONAR_TOKEN=$(jq -r '.sonarToken' "$CONFIG_FILE")
  COVERAGE_TOOL=$(jq -r '.coverage.tool' "$CONFIG_FILE")
  COVERAGE_OUTPUT_FORMAT=$(jq -r '.coverage.outputFormat' "$CONFIG_FILE")
  COVERAGE_OUTPUT_DIR=$(jq -r '.coverage.outputDir' "$CONFIG_FILE")

  log_info "Configuration loaded from: $CONFIG_FILE"
  return 0
}

validate_config() {
  local errors=0

  if [[ -z "$SONAR_PROJECT_KEY" ]]; then
    log_error "projectKey is required in configuration"
    errors=$((errors + 1))
  fi

  if [[ -z "$SONAR_PROJECT_NAME" ]]; then
    log_error "projectName is required in configuration"
    errors=$((errors + 1))
  fi

  if [[ -z "$SONAR_LANGUAGE" ]]; then
    log_error "language is required in configuration"
    errors=$((errors + 1))
  fi

  if [[ -z "$SONAR_HOST_URL" ]]; then
    log_error "sonarHostUrl is required in configuration"
    errors=$((errors + 1))
  fi

  if [[ $errors -gt 0 ]]; then
    log_error "Configuration validation failed with $errors errors"
    return 1
  fi

  log_success "Configuration validation passed"
  return 0
}

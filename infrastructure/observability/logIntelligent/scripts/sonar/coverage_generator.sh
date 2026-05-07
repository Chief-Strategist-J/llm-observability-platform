#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/utils.sh"
source "$SCRIPT_DIR/config_loader.sh"

install_pytest_cov() {
  if python3 -c "import pytest_cov" &>/dev/null; then
    log_info "pytest-cov is already installed"
    return 0
  fi

  log_info "Installing pytest-cov..."
  if pip install --user pytest-cov 2>/dev/null; then
    log_success "pytest-cov installed successfully"
    return 0
  else
    log_error "Failed to install pytest-cov (externally managed environment or other error)"
    log_info "Will skip coverage generation gracefully"
    return 1
  fi
}

generate_coverage() {
  cd "$PROJECT_ROOT"

  if ! install_pytest_cov; then
    log_info "Skipping coverage generation due to missing dependencies"
    return 0
  fi

  log_info "Generating coverage report..."

  local coverage_dir="$PROJECT_ROOT/$COVERAGE_OUTPUT_DIR"
  ensure_dir "$coverage_dir"

  if python3 -m pytest --cov=. --cov-report=xml:$coverage_dir/coverage.xml --cov-report=html:$coverage_dir/html --cov-report=term test/; then
    log_success "Coverage report generated successfully"
    log_info "Coverage report location: $coverage_dir/coverage.xml"
    return 0
  else
    log_info "Coverage generation failed, skipping coverage"
    return 0
  fi
}

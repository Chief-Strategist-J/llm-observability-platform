#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/utils.sh"
source "$SCRIPT_DIR/config_loader.sh"

install_tarpaulin() {
  if cargo tarpaulin --version &>/dev/null; then
    log_info "cargo-tarpaulin is already installed"
    return 0
  fi

  log_info "Installing cargo-tarpaulin..."
  if cargo install cargo-tarpaulin; then
    log_success "cargo-tarpaulin installed successfully"
    return 0
  else
    log_error "Failed to install cargo-tarpaulin"
    return 1
  fi
}

generate_coverage() {
  cd "$PROJECT_ROOT"

  if ! install_tarpaulin; then
    return 1
  fi

  log_info "Generating coverage report..."

  local coverage_dir="$PROJECT_ROOT/$COVERAGE_OUTPUT_DIR"
  ensure_dir "$coverage_dir"

  if cargo tarpaulin --out Xml --output-dir "$coverage_dir" --verbose; then
    log_success "Coverage report generated successfully"
    log_info "Coverage report location: $coverage_dir/cobertura.xml"
    return 0
  else
    log_error "Failed to generate coverage report"
    return 1
  fi
}

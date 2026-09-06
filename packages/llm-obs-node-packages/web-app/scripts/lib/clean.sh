#!/usr/bin/env bash

# Artifact Cleanup Module

remove_target() {
  local target=$1
  if [ -e "$target" ]; then
    log_warn "  - Removing $target"
    rm -rf "$target"
  fi
}

clean_build_artifacts() {
  ensure_app_dir
  log_info "Cleaning build artifacts..."
  for target in "${BUILD_TARGETS[@]}"; do
    remove_target "$target"
  done
  log_success "Clean completed successfully."
}

clean_deep_artifacts() {
  ensure_app_dir
  clean_build_artifacts
  log_info "Performing deep clean..."
  for target in "${DEEP_TARGETS[@]}"; do
    if [ -e "$target" ]; then
      log_error "  - Removing $target"
      rm -rf "$target"
    fi
  done
  log_success "Deep clean completed successfully."
}

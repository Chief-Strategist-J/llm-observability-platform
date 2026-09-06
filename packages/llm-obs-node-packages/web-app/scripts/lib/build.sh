#!/usr/bin/env bash

# Build Verification & Dependency Installation Module

cmd_install_deps() {
  ensure_app_dir
  if [ "$1" = "--clean" ] || [ "$1" = "-c" ]; then
    clean_deep_artifacts
  fi
  log_info "Installing and updating dependencies..."
  npm install && npm update
  log_success "Dependencies installed and updated successfully."
}

cmd_build_verify() {
  ensure_app_dir
  log_info "Running build verification pipeline..."
  clean_build_artifacts
  log_warn "Running typecheck..."
  npx tsc --noEmit
  log_warn "Running lint..."
  npx eslint
  log_warn "Building Next.js app..."
  npx next build
  log_success "Verification completed successfully!"
}

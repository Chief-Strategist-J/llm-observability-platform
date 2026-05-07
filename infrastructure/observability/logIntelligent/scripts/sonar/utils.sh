#!/bin/bash

log_info() {
  echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
  echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

log_success() {
  echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

resolve_path() {
  local path="$1"
  if [[ -d "$path" ]]; then
    cd "$path" && pwd
  else
    log_error "Path does not exist: $path"
    return 1
  fi
}

check_command() {
  local cmd="$1"
  if ! command -v "$cmd" &> /dev/null; then
    log_error "Command not found: $cmd"
    return 1
  fi
  return 0
}

ensure_dir() {
  local dir="$1"
  if [[ ! -d "$dir" ]]; then
    log_info "Creating directory: $dir"
    mkdir -p "$dir"
  fi
}

get_script_dir() {
  local source="${BASH_SOURCE[0]}"
  while [ -h "$source" ]; do
    local dir="$(cd -P "$(dirname "$source")" && pwd)"
    source="$(readlink "$source")"
    [[ $source != /* ]] && source="$dir/$source"
  done
  cd -P "$(dirname "$source")" && pwd
}

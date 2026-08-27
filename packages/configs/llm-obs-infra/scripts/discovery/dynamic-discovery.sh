#!/usr/bin/env bash

set -e

discover_script_dir() {
  local source="${BASH_SOURCE[0]}"
  local dir=""
  while [ -h "$source" ]; do
    dir="$(cd -P "$(dirname "$source")" && pwd)"
    source="$(readlink "$source")"
    [[ $source != /* ]] && source="$dir/$source"
  done
  cd -P "$(dirname "$source")" && pwd
}

discover_file_upward() {
  local filename=$1
  local start_dir=${2:-$(pwd)}
  local curr="$start_dir"

  while [ "$curr" != "/" ] && [ -n "$curr" ]; do
    if [ -f "$curr/$filename" ]; then
      echo "$curr/$filename"
      return 0
    fi
    curr="$(dirname "$curr")"
  done

  return 1
}

discover_dir_upward_containing() {
  local target_file=$1
  local start_dir=${2:-$(pwd)}
  local found_file
  found_file=$(discover_file_upward "$target_file" "$start_dir" || echo "")

  if [ -n "$found_file" ]; then
    dirname "$found_file"
    return 0
  fi
  return 1
}

discover_git_repo_root() {
  local start_dir=${1:-$(pwd)}
  if command -v git >/dev/null 2>&1; then
    local root
    root=$(git -C "$start_dir" rev-parse --show-toplevel 2>/dev/null || echo "")
    if [ -n "$root" ]; then
      echo "$root"
      return 0
    fi
  fi
  return 1
}

discover_script_file_recursive() {
  local script_name=$1
  local search_root=$2
  local match=""

  if [ -n "$search_root" ] && [ -d "$search_root" ]; then
    match=$(find "$search_root" -maxdepth 4 -type f -name "$script_name" 2>/dev/null | head -n 1 || echo "")
  fi

  if [ -z "$match" ]; then
    match=$(find "$(pwd)" -maxdepth 4 -type f -name "$script_name" 2>/dev/null | head -n 1 || echo "")
  fi

  if [ -z "$match" ]; then
    local git_root
    git_root=$(discover_git_repo_root "$(pwd)" || echo "")
    if [ -n "$git_root" ]; then
      match=$(find "$git_root" -type f -name "$script_name" 2>/dev/null | head -n 1 || echo "")
    fi
  fi

  if [ -n "$match" ]; then
    echo "$match"
    return 0
  fi

  return 1
}

export -f discover_script_dir
export -f discover_file_upward
export -f discover_dir_upward_containing
export -f discover_git_repo_root
export -f discover_script_file_recursive

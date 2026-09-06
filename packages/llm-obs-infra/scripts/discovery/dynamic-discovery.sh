#!/usr/bin/env bash

set -e

declare -gA PATH_HASH_SET=()

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

execute_iterative_dfs() {
  local root_dir=$1
  local max_depth=${2:-3}
  local target_pattern=$3

  [ ! -d "$root_dir" ] && return 0

  local stack=("$root_dir:0")

  while [ ${#stack[@]} -gt 0 ]; do
    local current_item="${stack[-1]}"
    unset 'stack[${#stack[@]}-1]'

    local dir="${current_item%:*}"
    local depth="${current_item##*:}"

    [ "$depth" -gt "$max_depth" ] && continue

    [ -n "${PATH_HASH_SET["$dir"]:-}" ] && continue
    PATH_HASH_SET["$dir"]=1

    for entry in "$dir"/*; do
      [ ! -e "$entry" ] && continue

      if [ -d "$entry" ]; then
        if [[ "$(basename "$entry")" != .* ]] && [[ "$(basename "$entry")" != "node_modules" ]] && [[ "$(basename "$entry")" != "venv" ]]; then
          stack+=("$entry:$((depth + 1))")
        fi
      elif [ -f "$entry" ]; then
        if [[ "$(basename "$entry")" == $target_pattern ]]; then
          echo "$entry"
        fi
      fi
    done
  done
}

scan_content_signature() {
  local file_path=$1
  local required_tokens=$2

  [ ! -r "$file_path" ] && echo "0" && return 0

  local match_score=0
  for token in $required_tokens; do
    if grep -q -F "$token" "$file_path" 2>/dev/null; then
      match_score=$((match_score + 10))
    fi
  done

  echo "$match_score"
}

rank_candidates() {
  local candidates=("$@")
  local best_candidate=""
  local max_score=-1

  for item in "${candidates[@]}"; do
    [ -z "$item" ] && continue
    local score=0

    [ -x "$item" ] && score=$((score + 50))

    local slash_count
    slash_count=$(tr -dc '/' <<< "$item" | wc -c)
    score=$((score + (100 - (slash_count * 5))))

    local sig_score
    sig_score=$(scan_content_signature "$item" "main bash set -e")
    score=$((score + sig_score))

    if [ "$score" -gt "$max_score" ]; then
      max_score=$score
      best_candidate="$item"
    fi
  done

  echo "$best_candidate"
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

discover_script_file_recursive() {
  local script_name=$1
  local search_root=$2

  if [ -n "$search_root" ] && [ -f "$search_root/scripts/$script_name" ]; then
    echo "$search_root/scripts/$script_name"
    return 0
  fi

  if [ -f "$(pwd)/$script_name" ]; then
    echo "$(pwd)/$script_name"
    return 0
  fi

  PATH_HASH_SET=()

  local raw_candidates=()
  while IFS= read -r line; do
    if [ -n "$line" ]; then
      raw_candidates+=("$line")
      break
    fi
  done < <(execute_iterative_dfs "$search_root" 3 "$script_name")

  if [ ${#raw_candidates[@]} -gt 0 ]; then
    echo "${raw_candidates[0]}"
    return 0
  fi

  local git_root
  git_root=$(discover_git_repo_root "$(pwd)" || echo "")
  if [ -n "$git_root" ]; then
    while IFS= read -r line; do
      if [ -n "$line" ]; then
        raw_candidates+=("$line")
        break
      fi
    done < <(execute_iterative_dfs "$git_root" 4 "$script_name")
  fi

  local ranked_best
  ranked_best=$(rank_candidates "${raw_candidates[@]}")

  if [ -n "$ranked_best" ]; then
    echo "$ranked_best"
    return 0
  fi

  return 1
}

export -f discover_script_dir
export -f discover_file_upward
export -f discover_dir_upward_containing
export -f discover_git_repo_root
export -f discover_script_file_recursive

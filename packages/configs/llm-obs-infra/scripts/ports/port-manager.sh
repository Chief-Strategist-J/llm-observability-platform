#!/usr/bin/env bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

free_single_port() {
  local port=$1
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${port}/tcp" >/dev/null 2>&1 || true
  elif command -v lsof >/dev/null 2>&1; then
    local pids
    pids=$(lsof -t -i:"${port}" 2>/dev/null || true)
    if [ -n "$pids" ]; then
      echo -e "${YELLOW}  - Terminating process(es) on port ${port}: ${pids}${NC}"
      kill -9 $pids 2>/dev/null || true
    fi
  fi
}

free_all_ports() {
  local ports=$1
  echo -e "${BLUE}[frontend-deployment] Freeing all stack ports...${NC}"
  for p in $ports; do
    free_single_port "$p"
  done
  echo -e "${GREEN}✓ All stack ports verified/freed.${NC}"
}

main() {
  local ports=${1:-"31410 31411 31412 31413 31414 31415 31416 31417 31418 31419 31420 31421 31422 31423 31424 31425"}
  free_all_ports "$ports"
}

main "$@"

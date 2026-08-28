#!/usr/bin/env bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

free_single_port() {
  local port=$1
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids=$(lsof -t -i:"${port}" 2>/dev/null || true)
    if [ -n "$pids" ]; then
      for pid in $pids; do
        if grep -qE "docker|containerd|llmobs" "/proc/${pid}/cgroup" 2>/dev/null || grep -qE "docker|containerd|llmobs" "/proc/${pid}/cmdline" 2>/dev/null; then
          echo -e "${YELLOW}  - Terminating stale container process ${pid} on port ${port}${NC}"
          kill -9 "$pid" 2>/dev/null || true
        else
          echo -e "${YELLOW}⚠️ Warning: Port ${port} occupied by host process ${pid}. Skipping termination.${NC}"
        fi
      done
    fi
  elif command -v fuser >/dev/null 2>&1; then
    fuser -k "${port}/tcp" >/dev/null 2>&1 || true
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

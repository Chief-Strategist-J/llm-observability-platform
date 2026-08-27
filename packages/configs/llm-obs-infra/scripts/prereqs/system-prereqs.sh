#!/usr/bin/env bash

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

verify_host_utilities() {
  local missing=()
  command -v fuser >/dev/null 2>&1 || missing+=("psmisc")
  command -v lsof >/dev/null 2>&1 || missing+=("lsof")
  command -v nc >/dev/null 2>&1 || missing+=("netcat-openbsd")

  if [ ${#missing[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️ Missing required host utilities: ${missing[*]}${NC}"
    echo -e "${BLUE}Prompting for sudo to install missing dependencies (${missing[*]})...${NC}"
    sudo apt-get update && sudo apt-get install -y "${missing[@]}"
  else
    echo -e "${GREEN}✓ All host utilities (fuser, lsof, nc) are installed.${NC}"
  fi
}

verify_docker_daemon() {
  if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}✖ Docker daemon is not running.${NC}"
    echo -e "${BLUE}Prompting for sudo to start and enable docker.service...${NC}"
    sudo systemctl enable --now docker
  else
    echo -e "${GREEN}✓ Docker daemon is active and running.${NC}"
  fi
}

verify_file_descriptors() {
  local min_files=${1:-65536}
  local current_limit
  current_limit=$(ulimit -n 2>/dev/null || echo "1024")

  if [ "$current_limit" != "unlimited" ] && [ "$current_limit" -lt "$min_files" ]; then
    echo -e "${YELLOW}⚠️ Warning: Open file descriptors limit is low (${current_limit}). Setting ulimit -n ${min_files}...${NC}"
    ulimit -n "$min_files" 2>/dev/null || echo -e "${YELLOW}⚠️ Could not automatically raise ulimit. Requires: ulimit -n ${min_files}${NC}"
  else
    echo -e "${GREEN}✓ File descriptor limit verified (${current_limit}).${NC}"
  fi
}

verify_kernel_sysctls() {
  local current_map_count
  current_map_count=$(sysctl -n vm.max_map_count 2>/dev/null || echo "65530")

  if [ "$current_map_count" -lt 262144 ]; then
    echo -e "${YELLOW}⚠️ Warning: vm.max_map_count is low (${current_map_count}). Raising to 262144 for Kafka mmap...${NC}"
    sudo sysctl -w vm.max_map_count=262144 >/dev/null 2>&1 || echo -e "${YELLOW}⚠️ Could not raise vm.max_map_count.${NC}"
  else
    echo -e "${GREEN}✓ Kernel vm.max_map_count verified (${current_map_count}).${NC}"
  fi

  if [ -f "/sys/kernel/mm/transparent_hugepage/enabled" ]; then
    local thp_val
    thp_val=$(cat /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || echo "")
    if echo "$thp_val" | grep -q "\[always\]"; then
      echo -e "${YELLOW}⚠️ Warning: Transparent Huge Pages (THP) enabled.${NC}"
    fi
  fi
}

verify_clock_sync() {
  if command -v systemd-timesyncd >/dev/null 2>&1 || command -v chronyc >/dev/null 2>&1 || command -v ntpq >/dev/null 2>&1; then
    echo -e "${GREEN}✓ System NTP time synchronization active.${NC}"
  elif command -v timedatectl >/dev/null 2>&1; then
    local ntp_status
    ntp_status=$(timedatectl status 2>/dev/null | grep "NTP service" | awk '{print $3}' || echo "active")
    if [ "$ntp_status" = "active" ] || [ "$ntp_status" = "yes" ]; then
      echo -e "${GREEN}✓ System NTP time synchronization active.${NC}"
    else
      echo -e "${YELLOW}⚠️ Warning: NTP time sync inactive.${NC}"
    fi
  fi
}

verify_firewall_rules() {
  if command -v ufw >/dev/null 2>&1; then
    local ufw_status
    ufw_status=$(sudo ufw status 2>/dev/null | grep -i "Status: active" || echo "")
    if [ -n "$ufw_status" ]; then
      echo -e "${YELLOW}⚠️ Warning: UFW Firewall active. Ensuring docker bridge interface pass-through...${NC}"
      sudo ufw allow in on llmobs-network to any >/dev/null 2>&1 || true
    fi
  fi
}

verify_docker_socket() {
  local socket_path=$1
  if [ -r "$socket_path" ]; then
    echo -e "${GREEN}✓ Docker socket permissions verified.${NC}"
    return 0
  else
    echo -e "${YELLOW}⚠️ Warning: $socket_path is not readable by current user.${NC}"
    return 1
  fi
}

verify_system_memory() {
  local min_mb=${1:-2500}
  if command -v free >/dev/null 2>&1; then
    local avail_mem_mb
    avail_mem_mb=$(free -m | awk '/^Mem:/{print $7}')
    if [ -n "$avail_mem_mb" ] && [ "$avail_mem_mb" -lt "$min_mb" ]; then
      echo -e "${YELLOW}⚠️ Warning: Low available memory (${avail_mem_mb}MB free). Min required: ${min_mb}MB.${NC}"
      return 1
    else
      echo -e "${GREEN}✓ Available system RAM verified (${avail_mem_mb}MB free).${NC}"
      return 0
    fi
  fi
  return 0
}

reconcile_network_conflict() {
  local network_name=$1
  local target_project=$2
  if docker network inspect "$network_name" >/dev/null 2>&1; then
    local net_project
    net_project=$(docker network inspect "$network_name" --format '{{index .Labels "com.docker.compose.project"}}' 2>/dev/null || echo "")
    if [ "$net_project" != "$target_project" ]; then
      echo -e "${YELLOW}⚡ Re-creating external network '$network_name' for project '$target_project'...${NC}"
      docker network rm "$network_name" >/dev/null 2>&1 || true
    fi
  fi
}

main() {
  verify_host_utilities
  verify_docker_daemon
  verify_file_descriptors 65536
  verify_kernel_sysctls
  verify_clock_sync
  verify_firewall_rules
  verify_docker_socket "/var/run/docker.sock" || true
  verify_system_memory 2500 || true
  reconcile_network_conflict "llmobs-network" "llm-obs-infra"
}

main "$@"

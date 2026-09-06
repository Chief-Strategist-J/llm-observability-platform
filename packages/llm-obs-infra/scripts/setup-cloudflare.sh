#!/usr/bin/env bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

get_script_dir() {
  cd "$(dirname "${BASH_SOURCE[0]}")" && pwd
}

get_pkg_dir() {
  local script_dir=$1
  dirname "$script_dir"
}

get_docker_compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    echo "docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
  else
    echo ""
  fi
}

prompt_user_confirmation() {
  echo -e "${BLUE}====================================================${NC}"
  echo -e "${BOLD}   Cloudflare Tunnel Optional Integration${NC}"
  echo -e "${BLUE}====================================================${NC}"
  echo -e "Cloudflare Tunnel enables secure public ingress with zero open firewall ports"
  echo -e "and automatic edge SSL certificates for your llm-obs-infra platform.\n"

  read -p "Do you want to configure and enable Cloudflare Tunnel? (y/N): " confirm
  case "$confirm" in
    [yY][eE][sS]|[yY])
      return 0
      ;;
    *)
      echo -e "${YELLOW}Skipping Cloudflare Tunnel configuration.${NC}"
      return 1
      ;;
  esac
}

configure_tunnel_token() {
  local pkg_dir=$1
  local env_file="$pkg_dir/.env"

  echo -e "\n${BLUE}🔑 Cloudflare Tunnel Authentication${NC}"
  echo -e "Obtain your Tunnel Token from Cloudflare Zero Trust Dashboard (Networks → Tunnels)."
  read -p "Enter your Cloudflare Tunnel Token: " token

  if [ -z "$token" ]; then
    echo -e "${RED}Error: Tunnel Token cannot be empty.${NC}"
    exit 1
  fi

  if [ -f "$env_file" ]; then
    if grep -q "^CLOUDFLARE_TUNNEL_TOKEN=" "$env_file"; then
      sed -i "s|^CLOUDFLARE_TUNNEL_TOKEN=.*|CLOUDFLARE_TUNNEL_TOKEN=${token}|" "$env_file"
    else
      echo "CLOUDFLARE_TUNNEL_TOKEN=${token}" >> "$env_file"
    fi
  else
    echo "CLOUDFLARE_TUNNEL_TOKEN=${token}" > "$env_file"
  fi

  echo -e "${GREEN}✓ Cloudflare Tunnel Token saved securely to .env${NC}"
}

start_cloudflare_tunnel() {
  local pkg_dir=$1
  local bin=$2
  local base_compose="$pkg_dir/docker-compose.yml"
  local cf_compose="$pkg_dir/docker-compose.cloudflare.yml"

  echo -e "${BLUE}⚡ Starting Cloudflare Tunnel container...${NC}"
  $bin -f "$base_compose" -f "$cf_compose" up -d llmobs-cloudflare-tunnel
  echo -e "${GREEN}✓ Cloudflare Tunnel active! Status:${NC}"
  $bin -f "$base_compose" -f "$cf_compose" ps llmobs-cloudflare-tunnel
}

stop_cloudflare_tunnel() {
  local pkg_dir=$1
  local bin=$2
  local base_compose="$pkg_dir/docker-compose.yml"
  local cf_compose="$pkg_dir/docker-compose.cloudflare.yml"

  echo -e "${BLUE}Stopping Cloudflare Tunnel container...${NC}"
  $bin -f "$base_compose" -f "$cf_compose" stop llmobs-cloudflare-tunnel 2>/dev/null || true
  $bin -f "$base_compose" -f "$cf_compose" rm -f llmobs-cloudflare-tunnel 2>/dev/null || true
  echo -e "${GREEN}✓ Cloudflare Tunnel stopped.${NC}"
}

show_status() {
  local pkg_dir=$1
  local bin=$2
  local base_compose="$pkg_dir/docker-compose.yml"
  local cf_compose="$pkg_dir/docker-compose.cloudflare.yml"

  $bin -f "$base_compose" -f "$cf_compose" ps llmobs-cloudflare-tunnel
}

show_logs() {
  local pkg_dir=$1
  local bin=$2
  local base_compose="$pkg_dir/docker-compose.yml"
  local cf_compose="$pkg_dir/docker-compose.cloudflare.yml"

  $bin -f "$base_compose" -f "$cf_compose" logs -f llmobs-cloudflare-tunnel
}

main() {
  local command=${1:-"setup"}
  local script_dir
  script_dir=$(get_script_dir)
  local pkg_dir
  pkg_dir=$(get_pkg_dir "$script_dir")
  local bin
  bin=$(get_docker_compose_cmd)

  if [ -z "$bin" ]; then
    echo -e "${RED}Error: Docker Compose command not found.${NC}"
    exit 1
  fi

  case "$command" in
    setup)
      if prompt_user_confirmation; then
        configure_tunnel_token "$pkg_dir"
        start_cloudflare_tunnel "$pkg_dir" "$bin"
      fi
      ;;
    start)
      start_cloudflare_tunnel "$pkg_dir" "$bin"
      ;;
    stop)
      stop_cloudflare_tunnel "$pkg_dir" "$bin"
      ;;
    status)
      show_status "$pkg_dir" "$bin"
      ;;
    logs)
      show_logs "$pkg_dir" "$bin"
      ;;
    *)
      echo "Usage: $0 {setup|start|stop|status|logs}"
      exit 1
      ;;
  esac
}

main "$@"

#!/usr/bin/env bash
#
# setup.sh — LLMObs Frontend Deployment — Full Environment Setup
#
# Run this ONCE on a new PC to configure everything needed.
# Steps: prerequisites → .env → TLS certs → /etc/hosts → Docker images → validate
#
# Usage:
#   ./scripts/setup.sh
#

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(dirname "$SCRIPT_DIR")"

HOSTS_DOMAINS="llmobs.gateway llmobs.grafana llmobs.tempo llmobs.otel llmobs.kafka llmobs.redis"

IMAGES=(
  "traefik:v2.10"
  "redis:7-alpine"
  "apache/kafka:latest"
  "grafana/tempo:latest"
  "otel/opentelemetry-collector-contrib:latest"
  "grafana/grafana:latest"
)

TOTAL_STEPS=6
PASSED_STEPS=0

echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD} LLMObs Frontend Deployment — Full Environment Setup${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"

echo -e "\n${YELLOW}[1/${TOTAL_STEPS}] Checking system prerequisites...${NC}"

check_cmd() {
  local cmd=$1
  local install_hint=$2
  if command -v "$cmd" &>/dev/null; then
    local version
    version=$("$cmd" --version 2>/dev/null | head -1 || echo "installed")
    echo -e "  ${GREEN}✓${NC} ${BOLD}${cmd}${NC} — ${version}"
    return 0
  else
    echo -e "  ${RED}✖${NC} ${BOLD}${cmd}${NC} — NOT FOUND"
    echo -e "    Install: ${BOLD}${install_hint}${NC}"
    return 1
  fi
}

PREREQS_OK=true
check_cmd "docker"       "https://docs.docker.com/engine/install/" || PREREQS_OK=false
check_cmd "openssl"      "sudo apt install openssl"                || PREREQS_OK=false
check_cmd "curl"         "sudo apt install curl"                   || PREREQS_OK=false
check_cmd "nc"           "sudo apt install netcat-openbsd"         || PREREQS_OK=false
check_cmd "node"         "https://nodejs.org/en/download/"         || PREREQS_OK=false
check_cmd "npm"          "Bundled with Node.js"                    || PREREQS_OK=false

if docker compose version &>/dev/null; then
  echo -e "  ${GREEN}✓${NC} ${BOLD}docker compose${NC} — $(docker compose version 2>/dev/null | head -1)"
elif command -v docker-compose &>/dev/null; then
  echo -e "  ${GREEN}✓${NC} ${BOLD}docker-compose${NC} — $(docker-compose --version 2>/dev/null | head -1)"
else
  echo -e "  ${RED}✖${NC} ${BOLD}docker compose${NC} — NOT FOUND"
  echo -e "    Install: ${BOLD}sudo apt install docker-compose-plugin${NC}"
  PREREQS_OK=false
fi

if docker info &>/dev/null; then
  echo -e "  ${GREEN}✓${NC} ${BOLD}Docker daemon${NC} — running"
else
  echo -e "  ${RED}✖${NC} ${BOLD}Docker daemon${NC} — NOT running"
  echo -e "    Start: ${BOLD}sudo systemctl start docker${NC}"
  PREREQS_OK=false
fi

if [ "$PREREQS_OK" = true ]; then
  echo -e "  ${GREEN}${BOLD}All prerequisites satisfied.${NC}"
  PASSED_STEPS=$((PASSED_STEPS + 1))
else
  echo -e "\n  ${RED}${BOLD}Missing prerequisites. Install them and re-run this script.${NC}"
  exit 1
fi

echo -e "\n${YELLOW}[2/${TOTAL_STEPS}] Configuring environment variables...${NC}"
if [ -f "$PKG_DIR/.env" ]; then
  echo -e "  ${GREEN}✓${NC} .env already exists — skipping"
else
  if [ -f "$PKG_DIR/.env.example" ]; then
    cp "$PKG_DIR/.env.example" "$PKG_DIR/.env"
    REDIS_PW=$(openssl rand -hex 16)
    GRAFANA_PW=$(openssl rand -hex 16)
    sed -i "s|REDIS_PASSWORD=<CHANGE_ME>|REDIS_PASSWORD=${REDIS_PW}|" "$PKG_DIR/.env"
    sed -i "s|GF_SECURITY_ADMIN_PASSWORD=<CHANGE_ME>|GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PW}|" "$PKG_DIR/.env"
    echo -e "  ${GREEN}✓${NC} .env created with auto-generated secrets"
    echo -e "    Redis password:   ${REDIS_PW}"
    echo -e "    Grafana password: ${GRAFANA_PW}"
  else
    echo -e "  ${RED}✖${NC} .env.example not found — cannot create .env"
    exit 1
  fi
fi
PASSED_STEPS=$((PASSED_STEPS + 1))

echo -e "\n${YELLOW}[3/${TOTAL_STEPS}] Generating TLS certificates...${NC}"
bash "$SCRIPT_DIR/generate-certs.sh"
PASSED_STEPS=$((PASSED_STEPS + 1))

echo -e "\n${YELLOW}[4/${TOTAL_STEPS}] Configuring /etc/hosts for custom domains...${NC}"

HOSTS_LINE="127.0.0.1  ${HOSTS_DOMAINS}"
HOSTS_MISSING=false

for domain in $HOSTS_DOMAINS; do
  if ! grep -q "$domain" /etc/hosts 2>/dev/null; then
    HOSTS_MISSING=true
    break
  fi
done

if [ "$HOSTS_MISSING" = true ]; then
  echo -e "  ${YELLOW}⚠${NC} Custom domains not found in /etc/hosts"
  echo -e "  ${BOLD}Add this line to /etc/hosts (requires sudo):${NC}"
  echo -e "  ${BLUE}${HOSTS_LINE}${NC}"
  echo ""
  read -p "  Add automatically? [y/N] " -n 1 -r
  echo ""
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "$HOSTS_LINE" | sudo tee -a /etc/hosts >/dev/null
    echo -e "  ${GREEN}✓${NC} Custom domains added to /etc/hosts"
  else
    echo -e "  ${YELLOW}⚠${NC} Skipped — add manually before using custom gateway URLs"
  fi
else
  echo -e "  ${GREEN}✓${NC} All custom domains already configured in /etc/hosts"
fi
PASSED_STEPS=$((PASSED_STEPS + 1))

echo -e "\n${YELLOW}[5/${TOTAL_STEPS}] Pulling Docker images...${NC}"
cd "$PKG_DIR"

for img in "${IMAGES[@]}"; do
  echo -e "  Pulling ${BOLD}${img}${NC}..."
  docker pull "$img" --quiet 2>/dev/null || docker pull "$img" 2>/dev/null
done
echo -e "  ${GREEN}✓${NC} All Docker images pulled"
PASSED_STEPS=$((PASSED_STEPS + 1))

echo -e "\n${YELLOW}[6/${TOTAL_STEPS}] Validating setup...${NC}"

VALID=true

for f in "$PKG_DIR/config/certs/ca.pem" "$PKG_DIR/config/certs/server.pem" "$PKG_DIR/config/certs/server-key.pem"; do
  if [ -f "$f" ]; then
    echo -e "  ${GREEN}✓${NC} $(basename "$f") exists"
  else
    echo -e "  ${RED}✖${NC} $(basename "$f") missing"
    VALID=false
  fi
done

if [ -f "$PKG_DIR/.env" ]; then
  echo -e "  ${GREEN}✓${NC} .env configured"
else
  echo -e "  ${RED}✖${NC} .env missing"
  VALID=false
fi

if docker compose -f "$PKG_DIR/docker-compose.yml" config --quiet 2>/dev/null; then
  echo -e "  ${GREEN}✓${NC} docker-compose.yml is valid"
else
  echo -e "  ${YELLOW}⚠${NC} docker-compose.yml validation returned warnings (may be OK)"
fi

if [ "$VALID" = true ]; then
  PASSED_STEPS=$((PASSED_STEPS + 1))
fi

echo -e "\n${BLUE}══════════════════════════════════════════════════════════${NC}"
if [ "$PASSED_STEPS" -eq "$TOTAL_STEPS" ]; then
  echo -e "${GREEN}${BOLD}✓ SETUP COMPLETE — ${PASSED_STEPS}/${TOTAL_STEPS} STEPS PASSED${NC}"
  echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
  echo -e "\n${BOLD}Next steps:${NC}"
  echo -e "  1. Start the stack:  ${BLUE}npm run up${NC}"
  echo -e "  2. Run health check: ${BLUE}npm run health${NC}"
  echo -e "  3. Open Grafana:     ${BLUE}https://llmobs.grafana:31419${NC}"
  echo -e "  4. Open Gateway:     ${BLUE}https://llmobs.gateway:31419${NC}"
else
  echo -e "${RED}${BOLD}✖ SETUP INCOMPLETE — ${PASSED_STEPS}/${TOTAL_STEPS} STEPS PASSED${NC}"
  echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
  echo -e "  Fix the issues above and re-run: ${BOLD}./scripts/setup.sh${NC}"
  exit 1
fi

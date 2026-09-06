#!/usr/bin/env bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

log_info() {
  echo -e "${BLUE}[INFO] $1${NC}"
}

log_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

log_warn() {
  echo -e "${YELLOW}[WARN] $1${NC}"
}

log_error() {
  echo -e "${RED}[ERROR] $1${NC}" >&2
}

log_header() {
  echo -e "${BLUE}====================================================${NC}"
  echo -e "${BOLD} $1${NC}"
  echo -e "${BLUE}====================================================${NC}"
}

log_step() {
  echo -e "${YELLOW} -> $1...${NC}"
}

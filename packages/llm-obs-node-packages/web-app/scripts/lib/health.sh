#!/usr/bin/env bash

# Service Health Check Module

cmd_health() {
  log_info "Performing health check across registered services [ENV=${APP_ENV}]..."
  for entry in "${SERVICE_REGISTRY[@]}"; do
    IFS=':' read -r key name port dir cmd <<< "$entry"
    if [ "$key" = "auth" ]; then
      check_http_service "$name" "http://localhost:${port}/health"
    elif [ "$key" = "kafka" ]; then
      check_tcp_port "$name" "$port"
    else
      check_http_service "$name" "http://localhost:${port}"
    fi
  done
}

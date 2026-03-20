#!/bin/bash
HOSTS_FILE="/etc/hosts"
TARGET_IP="127.0.2.1"
HOSTNAMES=(
    "scaibu.grafana"
    "scaibu.prometheus"
    "scaibu.loki"
    "scaibu.jaeger"
    "scaibu.alertmanager"
    "scaibu.otel"
    "scaibu.temporal"
    "scaibu.observability-api"
)

echo "Checking host entries..."
MISSING=()
for host in "${HOSTNAMES[@]}"; do
    if ! grep -E "^[[:space:]]*${TARGET_IP}[[:space:]]+${host}([[:space:]]|$)" "$HOSTS_FILE" >/dev/null; then
        MISSING+=("$host")
    fi
done

if [ ${#MISSING[@]} -eq 0 ]; then
    echo "All host entries are already configured."
    exit 0
fi

if [ "$1" == "--apply" ]; then
    if [ "$EUID" -ne 0 ]; then
        echo "Error: Please run with sudo to apply changes."
        exit 1
    fi
    for host in "${MISSING[@]}"; do
        sed -i "/$host/d" "$HOSTS_FILE"
        echo "$TARGET_IP $host" >> "$HOSTS_FILE"
        echo "Added $host"
    done
    echo "Host entries updated successfully."
else
    echo "The following host entries are missing:"
    for host in "${MISSING[@]}"; do
        echo "  $TARGET_IP $host"
    done
    echo ""
    echo "To add them, please run:"
    echo "sudo $0 --apply"
fi

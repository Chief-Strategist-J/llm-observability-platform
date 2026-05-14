#!/bin/bash
# migration:      0001
# description:    initial kafka topics for instrumentation layer
# author:         antigravity
# date:           2026-05-14
# depends_on:     None
# reversible:     YES
# lock_risk:      LOW
# rows_affected:  schema only
# reason:         bootstrap instrumentation layer spans and DLQ

set -e

# Use the centralized registry sync script
python3 scripts/sync_kafka_registry.py

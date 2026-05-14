#!/bin/bash
# migration:      0001
# description:    initialize kafka topics from registry
# author:         Antigravity
# date:           2026-05-14
# depends_on:     NONE
# reversible:     YES
# lock_risk:      LOW
# rows_affected:  schema only
# reason:         setup initial messaging infrastructure for spans

set -e

SCRIPT_DIR=$(dirname "$0")
$SCRIPT_DIR/../../scripts/setup_kafka.sh

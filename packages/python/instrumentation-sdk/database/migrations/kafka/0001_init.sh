#!/bin/bash

set -e

SCRIPT_DIR=$(dirname "$0")
$SCRIPT_DIR/../../scripts/setup_kafka.sh

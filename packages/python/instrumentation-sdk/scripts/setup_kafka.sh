#!/bin/bash

# Kafka Topic Provisioning Utility
# Directly manages topic creation for the development environment.
# Called by migrations to ensure idempotency.

set -e

KAFKA_BIN=$(which kafka-topics || echo "/usr/bin/kafka-topics")
BOOTSTRAP_SERVER=${KAFKA_BOOTSTRAP_SERVER:-"kafka:29092"}

function create_topic() {
    local name=$1
    local partitions=$2
    local replication=$3

    $KAFKA_BIN --create --if-not-exists \
        --bootstrap-server $BOOTSTRAP_SERVER \
        --topic $name \
        --partitions $partitions \
        --replication-factor $replication
}

# Initial topic set defined in topics.yaml registry
create_topic "llm.spans.raw.unvalidated" 3 1
create_topic "llm.spans.raw" 3 1
create_topic "llm.spans.raw.dlq" 1 1
create_topic "llm.spans.sampled" 3 1
create_topic "llm.instrumentation.events" 3 1

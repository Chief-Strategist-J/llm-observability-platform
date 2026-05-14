#!/bin/bash
# migration:      0001
# description:    rollback kafka topics
# author:         Antigravity
# date:           2026-05-14
# depends_on:     NONE
# reversible:     YES
# lock_risk:      LOW
# rows_affected:  schema only
# reason:         revert initial messaging infrastructure

set -e

KAFKA_BIN=$(which kafka-topics || echo "/usr/bin/kafka-topics")
BOOTSTRAP_SERVER=${KAFKA_BOOTSTRAP_SERVER:-"kafka:29092"}

function delete_topic() {
    local name=$1
    $KAFKA_BIN --delete --if-exists --bootstrap-server $BOOTSTRAP_SERVER --topic $name
}

delete_topic "llm.spans.raw.unvalidated"
delete_topic "llm.spans.raw"
delete_topic "llm.spans.raw.dlq"
delete_topic "llm.spans.sampled"

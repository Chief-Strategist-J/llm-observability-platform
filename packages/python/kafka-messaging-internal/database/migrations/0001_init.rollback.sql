-- migration:      0001
-- description:    Rollback kafka_events database schema
-- author:         kafka-messaging-internal
-- date:           2025-01-11
-- depends_on:     none
-- reversible:     YES
-- lock_risk:      LOW
-- rows_affected:  schema only
-- reason:         Rollback of initial schema

-- Drop indexes first (in reverse order of creation)
DROP INDEX IF EXISTS idx_consumer_offsets_topic;
DROP INDEX IF EXISTS idx_consumer_offsets_group;
DROP INDEX IF EXISTS idx_events_processed;
DROP INDEX IF EXISTS idx_events_event_id;
DROP INDEX IF EXISTS idx_events_topic_created;
DROP INDEX IF EXISTS idx_events_topic;
DROP INDEX IF EXISTS idx_kafka_events_unique;

-- Drop tables
DROP TABLE IF EXISTS consumer_offsets;
DROP TABLE IF EXISTS kafka_events;

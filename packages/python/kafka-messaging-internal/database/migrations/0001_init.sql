-- migration:      0001
-- description:    Initialize kafka_events database schema
-- author:         kafka-messaging-internal
-- date:           2025-01-11
-- depends_on:     none
-- reversible:     YES
-- lock_risk:      LOW
-- rows_affected:  schema only
-- reason:         Initial schema for Kafka event storage with consumer offset tracking

-- Create kafka_events table
CREATE TABLE IF NOT EXISTS kafka_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE,
    topic VARCHAR(255) NOT NULL,
    partition INTEGER NOT NULL CHECK (partition >= 0),
    "offset" BIGINT NOT NULL CHECK ("offset" >= 0),
    key TEXT,
    value JSONB NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    headers JSONB,
    processed BOOLEAN DEFAULT FALSE,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for kafka_events
CREATE UNIQUE INDEX IF NOT EXISTS idx_kafka_events_unique 
ON kafka_events(topic, partition, "offset");

CREATE INDEX IF NOT EXISTS idx_events_topic 
ON kafka_events(topic);

CREATE INDEX IF NOT EXISTS idx_events_topic_created 
ON kafka_events(topic, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_events_event_id 
ON kafka_events(event_id);

CREATE INDEX IF NOT EXISTS idx_events_processed 
ON kafka_events(processed, created_at DESC);

-- Create consumer_offsets table
CREATE TABLE IF NOT EXISTS consumer_offsets (
    id SERIAL PRIMARY KEY,
    consumer_group VARCHAR(255) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    partition INTEGER NOT NULL CHECK (partition >= 0),
    "offset" BIGINT NOT NULL CHECK ("offset" >= 0),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(consumer_group, topic, partition)
);

-- Create indexes for consumer_offsets
CREATE INDEX IF NOT EXISTS idx_consumer_offsets_group 
ON consumer_offsets(consumer_group);

CREATE INDEX IF NOT EXISTS idx_consumer_offsets_topic 
ON consumer_offsets(topic);

-- Add table comments
COMMENT ON TABLE kafka_events IS 'Stores Kafka event records with processing status';
COMMENT ON TABLE consumer_offsets IS 'Stores consumer group offset information';

-- Add column comments
COMMENT ON COLUMN kafka_events.event_id IS 'Unique identifier for event tracking and idempotency';
COMMENT ON COLUMN kafka_events.topic IS 'Kafka topic name';
COMMENT ON COLUMN kafka_events.partition IS 'Kafka partition number';
COMMENT ON COLUMN kafka_events."offset" IS 'Kafka message offset within partition';
COMMENT ON COLUMN kafka_events.key IS 'Kafka message key (optional)';
COMMENT ON COLUMN kafka_events.value IS 'Kafka message payload as JSON';
COMMENT ON COLUMN kafka_events.timestamp IS 'Kafka message timestamp';
COMMENT ON COLUMN kafka_events.headers IS 'Kafka message headers as JSON';
COMMENT ON COLUMN kafka_events.processed IS 'Event processing status';
COMMENT ON COLUMN kafka_events.error IS 'Error message if processing failed';
COMMENT ON COLUMN kafka_events.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN kafka_events.updated_at IS 'Record last update timestamp';

COMMENT ON COLUMN consumer_offsets.consumer_group IS 'Consumer group identifier';
COMMENT ON COLUMN consumer_offsets.topic IS 'Kafka topic name';
COMMENT ON COLUMN consumer_offsets.partition IS 'Kafka partition number';
COMMENT ON COLUMN consumer_offsets."offset" IS 'Committed offset for consumer group';
COMMENT ON COLUMN consumer_offsets.updated_at IS 'Offset last update timestamp';

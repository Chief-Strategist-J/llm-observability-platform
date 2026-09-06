CREATE TABLE alert_history (
    id BIGSERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    service VARCHAR(255),
    model VARCHAR(255),
    user_id VARCHAR(255),
    event_type VARCHAR(50),
    payload JSONB NOT NULL,
    delivery_latency_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alert_history_alert_type_created ON alert_history(alert_type, created_at);

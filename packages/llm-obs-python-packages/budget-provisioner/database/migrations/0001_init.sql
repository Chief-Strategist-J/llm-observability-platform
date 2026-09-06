CREATE TABLE budget_configs (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    max_budget DOUBLE PRECISION NOT NULL,
    window_size_secs INTEGER NOT NULL DEFAULT 900,
    initial_fill_fraction DOUBLE PRECISION NOT NULL DEFAULT 0.1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX idx_budget_configs_user_model ON budget_configs(user_id, model);

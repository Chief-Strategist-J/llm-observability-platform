CREATE TABLE IF NOT EXISTS quality_scores (
    id BIGSERIAL PRIMARY KEY,
    span_id UUID NOT NULL UNIQUE,
    trace_id UUID,
    model VARCHAR(255) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    prompt_type VARCHAR(255),
    composite_score DOUBLE PRECISION,
    quality_flags TEXT[] NOT NULL DEFAULT '{}',
    scored_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quality_scores_lookup ON quality_scores (model, endpoint, prompt_type, scored_at, composite_score);

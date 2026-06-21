-- migration:      0001
-- description:    create forecasts table
-- author:         Antigravity
-- date:           2026-06-21
-- depends_on:     
-- reversible:     YES
-- lock_risk:      LOW
-- rows_affected:  schema only
-- reason:         Initial database schema for storing TimesFM forecasting results

CREATE TABLE forecasts (
  id BIGSERIAL PRIMARY KEY,
  service VARCHAR(255) NOT NULL,
  model VARCHAR(255) NOT NULL,
  forecast_time TIMESTAMP WITH TIME ZONE NOT NULL,
  forecast_mean DOUBLE PRECISION NOT NULL,
  forecast_p10 DOUBLE PRECISION NOT NULL,
  forecast_p90 DOUBLE PRECISION NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (service, model, forecast_time)
);

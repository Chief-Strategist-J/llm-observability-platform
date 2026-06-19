-- Migration: Initialize trace database schema
-- Target: SQLite WAL

CREATE TABLE IF NOT EXISTS traces (
  tid          TEXT PRIMARY KEY,
  name         TEXT,
  status       TEXT,        -- ok | error | running
  start_time   INTEGER,     -- unix nano
  end_time     INTEGER,
  span_count   INTEGER,
  error_count  INTEGER
);

CREATE TABLE IF NOT EXISTS spans (
  sid          TEXT PRIMARY KEY,
  tid          TEXT,
  parent_sid   TEXT,        -- null = root
  class        TEXT,        -- OTel attribute: code.namespace
  function     TEXT,        -- OTel attribute: code.function
  status       TEXT,        -- ok | error | unset
  start_time   INTEGER,
  end_time     INTEGER,
  attrs        TEXT         -- JSON, all extra OTel attributes
);

CREATE TABLE IF NOT EXISTS steps (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  sid          TEXT,
  tid          TEXT,
  step         TEXT,        -- OTel span event name
  message      TEXT,        -- OTel event attribute: message
  level        TEXT,        -- OTel event attribute: level
  ts           INTEGER
);

CREATE INDEX IF NOT EXISTS idx_spans_tid ON spans(tid);
CREATE INDEX IF NOT EXISTS idx_spans_class ON spans(class);
CREATE INDEX IF NOT EXISTS idx_spans_function ON spans(function);
CREATE INDEX IF NOT EXISTS idx_spans_parent_sid ON spans(parent_sid);
CREATE INDEX IF NOT EXISTS idx_steps_sid ON steps(sid);
CREATE INDEX IF NOT EXISTS idx_steps_tid ON steps(tid);
CREATE INDEX IF NOT EXISTS idx_traces_start_time ON traces(start_time);
CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(status);

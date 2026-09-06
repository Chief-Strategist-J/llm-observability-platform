-- migration:      0001
-- description:    rollback llm_spans table in PostgreSQL
-- author:         antigravity
-- date:           2026-05-13
-- reversible:     YES

DROP TABLE IF EXISTS llm_spans;

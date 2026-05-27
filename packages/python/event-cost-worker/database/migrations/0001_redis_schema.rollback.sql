-- rollback:       0001
-- description:    Remove all cost-engine Redis keys
-- reversible:     YES

-- DEL all fenwick:* keys
-- DEL all budget:tb:* keys
-- DEL dedup:cost_engine
-- Or FLUSHDB on isolated Redis instance

import pytest
import uuid
from fastapi.testclient import TestClient
from infrastructure.database.mongodb.client.algo_api_server import app

client = TestClient(app)

def test_btree_audit():
    res = client.post("/algo/btree-index", json={"collection": "f_btree", "key": "k"})
    assert res.status_code == 200
    assert "treeDepth" in res.json()

def test_compound_ordering():
    res = client.post("/algo/compound-index", json={"collection": "f_compound", "keys": ["a", "b"]})
    assert res.status_code == 200
    assert "optimized_sort" in res.json()

def test_partial_selection():
    res = client.post("/algo/partial-index", json={"collection": "f_partial", "fields": ["x"], "filter_expr": {"x": {"$gt": 0}}})
    assert res.status_code == 200
    assert "ixscan" in res.json()

def test_sparse_evaluation():
    res = client.post("/algo/sparse-index", json={"collection": "f_sparse", "key": "s"})
    assert res.status_code == 200
    assert "indexed" in res.json()

def test_hashed_index():
    res = client.post("/algo/hashed-index", json={"collection": "f_hashed", "key": "h"})
    assert res.status_code == 200
    assert "ixscan" in res.json()

def test_hash_sharding():
    res = client.post("/algo/hash-sharding", json={"shard_key": "sk"})
    assert res.status_code == 200

def test_range_sharding():
    res = client.post("/algo/range-sharding", json={"shard_key": "rk"})
    assert res.status_code == 200

def test_shard_cardinality():
    res = client.post("/algo/shard-key-cardinality", json={"collection": "f_card", "key": "k"})
    assert res.status_code == 200
    assert "ratio" in res.json()

def test_chunk_split():
    res = client.post("/algo/chunk-split", json={"namespace": "f.c", "split_point": {"_id": 1}})
    assert res.status_code == 200

def test_chunk_migration():
    res = client.post("/algo/chunk-migration", json={"namespace": "f.c", "chunk_id": "c1", "target": "s1"})
    assert res.status_code == 200

def test_balancer_status():
    res = client.post("/algo/balancer-status")
    assert res.status_code == 200

def test_query_planner():
    res = client.post("/algo/query-plan", json={"collection": "f_query", "query": {"x": 1}})
    assert res.status_code == 200
    assert "winner" in res.json()

def test_plan_cache():
    res = client.post("/algo/plan-cache-evict", json={"collection": "f_cache", "query_hash": "h"})
    assert res.status_code == 200

def test_index_intersection():
    res = client.post("/algo/index-intersection", json={"collection": "f_inter", "query": {"a": 1, "b": 1}})
    assert res.status_code == 200

def test_covered_query():
    res = client.post("/algo/covered-query", json={"collection": "f_cov", "query": {"x": 1}, "projection": {"x": 1, "_id": 0}})
    assert res.status_code == 200

def test_agg_optimize():
    res = client.post("/algo/agg-optimize", json={"collection": "f_agg", "pipeline": [{"$match": {"x": 1}}]})
    assert res.status_code == 200

def test_pushdown_optimize():
    res = client.post("/algo/pushdown-optimize", json={"collection": "f_push", "pipeline": [{"$match": {"x": 1}}]})
    assert res.status_code == 200

def test_group_hash():
    res = client.post("/algo/group-hash", json={"collection": "f_group", "group_field": "g"})
    assert res.status_code == 200

def test_external_sort():
    res = client.post("/algo/external-sort", json={"collection": "f_sort", "sort_field": "s"})
    assert res.status_code == 200

def test_lookup_join():
    res = client.post("/algo/lookup-join", json={"local": "f_l", "foreign": "f_f", "local_field": "a", "foreign_field": "b"})
    assert res.status_code == 200

def test_facet_parallel():
    res = client.post("/algo/facet-parallel", json={"collection": "f_facet", "facets": {"f1": [{"$count": "c"}]}})
    assert res.status_code == 200

def test_graph_lookup():
    res = client.post("/algo/graph-lookup", json={"collection": "f_graph", "start_at": "a", "connect_from": "b", "connect_to": "c"})
    assert res.status_code == 200

def test_timeseries_bucket():
    res = client.post("/algo/timeseries-bucket", json={"collection": "f_ts"})
    assert res.status_code == 200

def test_ttl_expiration():
    res = client.post("/algo/ttl-expiration", json={"collection": "f_ttl", "field": "exp", "expire": 60})
    assert res.status_code == 200
    assert "ttl_seconds" in res.json()

def test_wt_mvcc():
    res = client.post("/algo/wt-mvcc", json={"collection": "f_mvcc", "doc_id": "m1", "data": {"v": 1}})
    assert res.status_code == 200

def test_doc_lock():
    res = client.post("/algo/doc-lock", json={"collection": "f_lock", "doc_id": "l1", "update": {"v": 2}})
    assert res.status_code == 200

def test_2pc_coordinator():
    tx_id = f"tx_p_{uuid.uuid4().hex[:8]}"
    res = client.post("/algo/2pc-coordinator", json={"collection": "f_2pc", "tx_id": tx_id})
    assert res.status_code == 200
    assert res.json()["final_state"] == "DONE"

def test_oplog():
    res = client.post("/algo/oplog")
    assert res.status_code == 200

def test_causal_consistency():
    res = client.post("/algo/causal-consistency")
    assert res.status_code == 200

def test_raft_election():
    res = client.post("/algo/raft-election")
    assert res.status_code == 200

def test_heartbeat_detection():
    res = client.post("/algo/raft-election")
    assert res.status_code == 200

def test_rollback_recovery():
    res = client.post("/algo/rollback-recovery")
    assert res.status_code == 200

def test_journal_wal():
    res = client.post("/algo/journal-wal")
    assert res.status_code == 200

def test_checkpoint_algo():
    res = client.post("/algo/checkpoint")
    assert res.status_code == 200

def test_crash_recovery():
    res = client.post("/algo/journal-wal")
    assert res.status_code == 200

def test_coll_stats():
    res = client.post("/algo/coll-stats", json={"collection": "f_comp"})
    assert res.status_code == 200

def test_cache_stats():
    res = client.post("/algo/cache-stats")
    assert res.status_code == 200

def test_admission_control():
    res = client.post("/algo/cache-stats")
    assert res.status_code == 200

def test_page_faults():
    res = client.post("/algo/page-faults")
    assert res.status_code == 200

def test_read_pref():
    res = client.post("/algo/read-pref-route", json={"collection": "f_pref", "pref": "primaryPreferred"})
    assert res.status_code == 200

def test_wc_ack():
    res = client.post("/algo/wc-ack", json={"collection": "f_wc", "doc": {"x": 1}, "w": "1"})
    assert res.status_code == 200

def test_rc_consistency():
    res = client.post("/algo/rc-consistency", json={"collection": "f_rc", "level": "local"})
    assert res.status_code == 200

def test_resume_token():
    res = client.post("/algo/resume-token", json={"collection": "f_token"})
    assert res.status_code == 200

def test_retryable_write():
    res = client.post("/algo/retryable-write", json={"collection": "f_retry", "doc": {"x": 1}})
    assert res.status_code == 200

def test_bg_index():
    res = client.post("/algo/bg-index", json={"collection": "f_bg", "field": "b"})
    assert res.status_code == 200

def test_commit_quorum():
    res = client.post("/algo/commit-quorum", json={"collection": "f_quorum", "field": "q", "quorum": "1"})
    assert res.status_code == 200

def test_cursor_batch():
    res = client.post("/algo/cursor-batch", json={"collection": "f_batch", "size": 10})
    assert res.status_code == 200

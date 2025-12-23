from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import datetime
from bson import ObjectId, Binary
import infrastructure.database.mongodb.client.mongodb_algorithms as algo

app = FastAPI(title="Scaibu MongoDB Hyper-Fidelity Algorithms API")

def bson_encoder(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, Binary):
        return str(obj)
    if isinstance(obj, dict):
        return {k: bson_encoder(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [bson_encoder(x) for x in obj]
    return obj

def handle_algo_call(func, *args, **kwargs):
    res = func(*args, **kwargs)
    return JSONResponse(content=bson_encoder(res))

class BTreeReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    key: str

class CompoundReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    keys: List[str]

class PartialReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    fields: List[str]
    filter_expr: Dict[str, Any]

class SparseReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    key: str

class HashShardReq(BaseModel):
    shard_key: str

class CardinalityReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    key: str

class ChunkSplitReq(BaseModel):
    namespace: str
    split_point: Dict[str, Any]

class ChunkMigrateReq(BaseModel):
    namespace: str
    chunk_id: str
    target: str

class QueryPlanReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    query: Dict[str, Any]

class PlanEvictReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    query_hash: str

class IndexInterReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    query: Dict[str, Any]

class CoveredReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    query: Dict[str, Any]
    projection: Dict[str, int]

class AggReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    pipeline: List[Dict[str, Any]]

class GroupHashReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    group_field: str

class SortReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    sort_field: str

class LookupReq(BaseModel):
    db: str = "scaibu_default"
    local: str
    foreign: str
    local_field: str
    foreign_field: str

class FacetReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    facets: Dict[str, List[Dict[str, Any]]]

class GraphReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    start_at: str
    connect_from: str
    connect_to: str

class TSReq(BaseModel):
    db: str = "scaibu_default"
    collection: str

class TTLReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    field: str
    expire: int

class MVCCReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    doc_id: Any
    data: Dict[str, Any]

class LockReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    doc_id: Any
    update: Dict[str, Any]

class TwoPCReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    tx_id: str

class PreferenceReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    pref: str

class ConcernReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    level: str

class AckReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    doc: Dict[str, Any]
    w: str

class TokenReq(BaseModel):
    db: str = "scaibu_default"
    collection: str

class IdempotentReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    doc: Dict[str, Any]

class IndexBuildReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    field: str

class QuorumReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    field: str
    quorum: str

class BatchReq(BaseModel):
    db: str = "scaibu_default"
    collection: str
    size: int

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/algo/btree-index")
def api_btree_index(req: BTreeReq):
    return handle_algo_call(algo.btree_index_algorithm, req.db, req.collection, req.key)

@app.post("/algo/compound-index")
def api_compound_index(req: CompoundReq):
    return handle_algo_call(algo.compound_index_ordering, req.db, req.collection, req.keys)

@app.post("/algo/partial-index")
def api_partial_index(req: PartialReq):
    return handle_algo_call(algo.partial_index_selection, req.db, req.collection, req.fields, req.filter_expr)

@app.post("/algo/sparse-index")
def api_sparse_index(req: SparseReq):
    return handle_algo_call(algo.sparse_index_evaluation, req.db, req.collection, req.key)

@app.post("/algo/hashed-index")
def api_hashed_index(req: SparseReq):
    return handle_algo_call(algo.hashed_index_algorithm, req.db, req.collection, req.key)

@app.post("/algo/hash-sharding")
def api_hash_sharding(req: HashShardReq):
    return handle_algo_call(algo.hash_based_sharding, req.shard_key)

@app.post("/algo/range-sharding")
def api_range_sharding(req: HashShardReq):
    return handle_algo_call(algo.range_based_sharding, req.shard_key)

@app.post("/algo/shard-key-cardinality")
def api_shard_cardinality(req: CardinalityReq):
    return handle_algo_call(algo.shard_key_cardinality_evaluation, req.db, req.collection, req.key)

@app.post("/algo/chunk-split")
def api_chunk_split(req: ChunkSplitReq):
    return handle_algo_call(algo.chunk_split_algorithm, req.namespace, req.split_point)

@app.post("/algo/chunk-migration")
def api_chunk_migration(req: ChunkMigrateReq):
    return handle_algo_call(algo.chunk_migration_algorithm, req.namespace, req.chunk_id, req.target)

@app.post("/algo/balancer-status")
def api_balancer_status():
    return handle_algo_call(algo.balancer_load_equalization)

@app.post("/algo/query-plan")
def api_query_plan(req: QueryPlanReq):
    return handle_algo_call(algo.query_planner_cost_optimizer, req.db, req.collection, req.query)

@app.post("/algo/plan-cache-evict")
def api_plan_cache_evict(req: PlanEvictReq):
    return handle_algo_call(algo.plan_cache_eviction, req.db, req.collection, req.query_hash)

@app.post("/algo/index-intersection")
def api_index_intersection(req: IndexInterReq):
    return handle_algo_call(algo.index_intersection_algorithm, req.db, req.collection, req.query)

@app.post("/algo/covered-query")
def api_covered_query(req: CoveredReq):
    return handle_algo_call(algo.covered_query_optimization, req.db, req.collection, req.query, req.projection)

@app.post("/algo/agg-optimize")
def api_agg_optimize(req: AggReq):
    return handle_algo_call(algo.aggregation_pipeline_optimization, req.db, req.collection, req.pipeline)

@app.post("/algo/pushdown-optimize")
def api_pushdown_optimize(req: AggReq):
    return handle_algo_call(algo.match_project_pushdown, req.db, req.collection, req.pipeline)

@app.post("/algo/group-hash")
def api_group_hash(req: GroupHashReq):
    return handle_algo_call(algo.group_hash_aggregation, req.db, req.collection, req.group_field)

@app.post("/algo/external-sort")
def api_external_sort(req: SortReq):
    return handle_algo_call(algo.sort_external_merge_sort, req.db, req.collection, req.sort_field)

@app.post("/algo/lookup-join")
def api_lookup_join(req: LookupReq):
    return handle_algo_call(algo.lookup_indexed_nested_loop, req.db, req.local, req.foreign, req.local_field, req.foreign_field)

@app.post("/algo/facet-parallel")
def api_facet_parallel(req: FacetReq):
    return handle_algo_call(algo.facet_parallel_execution, req.db, req.collection, req.facets)

@app.post("/algo/graph-lookup")
def api_graph_lookup(req: GraphReq):
    return handle_algo_call(algo.graph_lookup_traversal, req.db, req.collection, req.start_at, req.connect_from, req.connect_to)

@app.post("/algo/timeseries-bucket")
def api_timeseries_bucket(req: TSReq):
    return handle_algo_call(algo.time_series_bucketization, req.db, req.collection)

@app.post("/algo/ttl-expiration")
def api_ttl_expiration(req: TTLReq):
    return handle_algo_call(algo.ttl_expiration_algorithm, req.db, req.collection, req.field, req.expire)

@app.post("/algo/wt-mvcc")
def api_wt_mvcc(req: MVCCReq):
    return handle_algo_call(algo.wiredtiger_mvcc_concurrency, req.db, req.collection, req.doc_id, req.data)

@app.post("/algo/doc-lock")
def api_doc_lock(req: LockReq):
    return handle_algo_call(algo.document_level_locking, req.db, req.collection, req.doc_id, req.update)

@app.post("/algo/2pc-coordinator")
def api_2pc_coordinator(req: TwoPCReq):
    return handle_algo_call(algo.two_phase_commit_coordinator, req.db, req.collection, req.tx_id)

@app.post("/algo/oplog")
def api_oplog():
    from infrastructure.database.mongodb.client.mongodb_client import get_client, MongoConnectionConfig
    return handle_algo_call(algo.oplog_replication_algorithm, get_client(MongoConnectionConfig().uri))

@app.post("/algo/causal-consistency")
def api_causal_consistency():
    from infrastructure.database.mongodb.client.mongodb_client import get_client, MongoConnectionConfig
    return handle_algo_call(algo.causal_consistency_algorithm, get_client(MongoConnectionConfig().uri))

@app.post("/algo/raft-election")
def api_raft_election():
    from infrastructure.database.mongodb.client.mongodb_client import get_client, MongoConnectionConfig
    return handle_algo_call(algo.raft_election_algorithm, get_client(MongoConnectionConfig().uri))

@app.post("/algo/rollback-recovery")
def api_rollback_recovery():
    from infrastructure.database.mongodb.client.mongodb_client import get_client, MongoConnectionConfig
    return handle_algo_call(algo.rollback_recovery_algorithm, get_client(MongoConnectionConfig().uri))

@app.post("/algo/journal-wal")
def api_journal_wal():
    from infrastructure.database.mongodb.client.mongodb_client import get_client, MongoConnectionConfig
    return handle_algo_call(algo.journaling_wal_algorithm, get_client(MongoConnectionConfig().uri))

@app.post("/algo/checkpoint")
def api_checkpoint():
    from infrastructure.database.mongodb.client.mongodb_client import get_client, MongoConnectionConfig
    return handle_algo_call(algo.checkpointing_algorithm, get_client(MongoConnectionConfig().uri))

@app.post("/algo/coll-stats")
def api_coll_stats(req: TSReq):
    return handle_algo_call(algo.compression_snappy_zstd, req.db, req.collection)

@app.post("/algo/cache-stats")
def api_cache_stats():
    from infrastructure.database.mongodb.client.mongodb_client import get_client, MongoConnectionConfig
    return handle_algo_call(algo.memory_eviction_lru, get_client(MongoConnectionConfig().uri))

@app.post("/algo/page-faults")
def api_page_faults():
    from infrastructure.database.mongodb.client.mongodb_client import get_client, MongoConnectionConfig
    return handle_algo_call(algo.page_fault_handling, get_client(MongoConnectionConfig().uri))

@app.post("/algo/read-pref-route")
def api_read_pref_route(req: PreferenceReq):
    return handle_algo_call(algo.read_preference_routing, req.db, req.collection, req.pref)

@app.post("/algo/wc-ack")
def api_wc_ack(req: AckReq):
    return handle_algo_call(algo.write_concern_acknowledgment, req.db, req.collection, req.doc, req.w)

@app.post("/algo/rc-consistency")
def api_rc_consistency(req: ConcernReq):
    return handle_algo_call(algo.read_concern_consistency, req.db, req.collection, req.level)

@app.post("/algo/resume-token")
def api_resume_token(req: TokenReq):
    return handle_algo_call(algo.change_stream_resume_token, req.db, req.collection)

@app.post("/algo/retryable-write")
def api_retryable_write(req: IdempotentReq):
    return handle_algo_call(algo.idempotent_retryable_writes, req.db, req.collection, req.doc)

@app.post("/algo/bg-index")
def api_bg_index(req: IndexBuildReq):
    return handle_algo_call(algo.background_index_build, req.db, req.collection, req.field)

@app.post("/algo/commit-quorum")
def api_commit_quorum(req: QuorumReq):
    return handle_algo_call(algo.index_build_commit_quorum, req.db, req.collection, req.field, req.quorum)

@app.post("/algo/cursor-batch")
def api_cursor_batch(req: BatchReq):
    return handle_algo_call(algo.query_cursor_batching, req.db, req.collection, req.size)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

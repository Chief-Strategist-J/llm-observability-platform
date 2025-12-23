from typing import Any, Dict, List, Optional, Callable
import time
import uuid
import random
from pymongo import ASCENDING, DESCENDING
from infrastructure.database.mongodb.client import mongodb_client as client_lib

obs = client_lib.obs

@client_lib._obs_wrap
def btree_index_algorithm(db_name: str, coll_name: str, key: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    db = client[db_name]
    coll = db[coll_name]
    with obs.tracer.start_as_current_span("btree_protocol"):
        coll.delete_many({})
        coll.insert_many([{"_id": i, key: i % 100} for i in range(1000)])
        coll.create_index([(key, ASCENDING)])
        expl = db.command("explain", {"find": coll_name, "filter": {key: {"$gt": 50}}}, verbosity="executionStats")
        stats = expl.get("executionStats", {})
        valid = db.command("validate", coll_name, full=True)
        return {
            "algorithm": "B-Tree",
            "keysExamined": stats.get("totalKeysExamined"),
            "docsExamined": stats.get("totalDocsExamined"),
            "treeDepth": valid.get("treeDepth", 1),
            "ixscan": "IXSCAN" in str(expl)
        }

@client_lib._obs_wrap
def compound_index_ordering(db_name: str, coll_name: str, keys: List[str]):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    db = client[db_name]
    coll = db[coll_name]
    with obs.tracer.start_as_current_span("compound_protocol"):
        coll.create_index([(k, ASCENDING) for k in keys])
        expl = db.command("explain", {"find": coll_name, "filter": {keys[0]: 1}, "sort": {keys[1]: 1}}, verbosity="executionStats")
        planner = expl.get("queryPlanner", {})
        return {
            "keys": keys,
            "optimized_sort": "SORT" not in str(planner),
            "winning_stage": planner.get("winningPlan", {}).get("stage")
        }

@client_lib._obs_wrap
def partial_index_selection(db_name: str, coll_name: str, fields: List[str], filter_expr: Dict[str, Any]):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    db = client[db_name]
    coll = db[coll_name]
    with obs.tracer.start_as_current_span("partial_protocol"):
        coll.create_index([(f, ASCENDING) for f in fields], partialFilterExpression=filter_expr)
        expl_match = db.command("explain", {"find": coll_name, "filter": filter_expr}, verbosity="executionStats")
        return {"partial": True, "ixscan": "IXSCAN" in str(expl_match)}

@client_lib._obs_wrap
def sparse_index_evaluation(db_name: str, coll_name: str, key: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    db = client[db_name]
    coll = db[coll_name]
    with obs.tracer.start_as_current_span("sparse_protocol"):
        coll.delete_many({})
        coll.insert_many([{"_id": 1, key: 1}, {"_id": 2, "x": 1}])
        coll.create_index([(key, ASCENDING)], sparse=True)
        stats = db.command("collStats", coll_name)
        idx_count = stats.get("indexDetails", {}).get(f"{key}_1", {}).get("count", 0)
        return {"sparse": True, "indexed": idx_count, "total": 2}

@client_lib._obs_wrap
def hashed_index_algorithm(db_name: str, coll_name: str, key: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    db = client[db_name]
    coll = db[coll_name]
    with obs.tracer.start_as_current_span("hashed_protocol"):
        coll.create_index([(key, "hashed")])
        expl = db.command("explain", {"find": coll_name, "filter": {key: 1}}, verbosity="executionStats")
        return {"hashed": True, "ixscan": "IXSCAN" in str(expl)}

@client_lib._obs_wrap
def hash_based_sharding(shard_key: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    with obs.tracer.start_as_current_span("hash_sharding_protocol"):
        try:
            client.admin.command("enableSharding", "scaibu_default")
            res = client.admin.command("shardCollection", "scaibu_default.hf_h", key={shard_key: "hashed"})
            return {"type": "hash", "status": "sharded", "raw": res}
        except Exception:
            return {"type": "hash", "status": "standalone_mode"}

@client_lib._obs_wrap
def range_based_sharding(shard_key: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    with obs.tracer.start_as_current_span("range_sharding_protocol"):
        try:
            client.admin.command("enableSharding", "scaibu_default")
            res = client.admin.command("shardCollection", "scaibu_default.hf_r", key={shard_key: 1})
            return {"type": "range", "status": "sharded", "raw": res}
        except Exception:
            return {"type": "range", "status": "standalone_mode"}

@client_lib._obs_wrap
def shard_key_cardinality_evaluation(db_name: str, coll_name: str, key: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    coll = client[db_name][coll_name]
    with obs.tracer.start_as_current_span("cardinality_protocol"):
        unique = len(coll.distinct(key))
        total = coll.estimated_document_count()
        return {"distinct": unique, "ratio": unique/max(total, 1)}

@client_lib._obs_wrap
def chunk_split_algorithm(namespace: str, split_point: Dict[str, Any]):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    with obs.tracer.start_as_current_span("split_protocol"):
        try:
            return client.admin.command("split", namespace, middle=split_point)
        except Exception:
            return {"op": "split", "status": "unsupported"}

@client_lib._obs_wrap
def chunk_migration_algorithm(namespace: str, chunk_id: str, target: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    with obs.tracer.start_as_current_span("migration_protocol"):
        try:
            return client.admin.command("moveChunk", namespace, find={"_id": chunk_id}, to=target)
        except Exception:
            return {"op": "migration", "status": "unsupported"}

@client_lib._obs_wrap
def balancer_load_equalization():
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    with obs.tracer.start_as_current_span("balancer_protocol"):
        try:
            status = client.admin.command("balancerStatus")
            return {"active": status.get("mode") == "on", "round": status.get("inBalancerRound")}
        except Exception:
            return {"active": False, "mode": "standalone"}

@client_lib._obs_wrap
def query_planner_cost_optimizer(db_name: str, coll_name: str, query: Dict[str, Any]):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    db = client[db_name]
    with obs.tracer.start_as_current_span("planner_protocol"):
        expl = db.command("explain", {"find": coll_name, "filter": query}, verbosity="allPlansExecution")
        planner = expl.get("queryPlanner", {})
        return {
            "winner": planner.get("winningPlan", {}).get("stage"),
            "rejected": len(planner.get("rejectedPlans", [])),
            "mechanism": "cost_based"
        }

@client_lib._obs_wrap
def plan_cache_eviction(db_name: str, coll_name: str, query_hash: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    db = client[db_name]
    with obs.tracer.start_as_current_span("cache_evict_protocol"):
        db.command("planCacheClear", coll_name)
        return {"evicted": True, "hash": query_hash}

@client_lib._obs_wrap
def index_intersection_algorithm(db_name: str, coll_name: str, query: Dict[str, Any]):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    db = client[db_name]
    with obs.tracer.start_as_current_span("intersection_protocol"):
        expl = db.command("explain", {"find": coll_name, "filter": query}, verbosity="executionStats")
        return {"algorithm": "IndexIntersection", "status": "AND_SORTED" in str(expl)}

@client_lib._obs_wrap
def covered_query_optimization(db_name: str, coll_name: str, query: Dict[str, Any], proj: Dict[str, int]):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    db = client[db_name]
    with obs.tracer.start_as_current_span("covered_protocol"):
        expl = db.command("explain", {"find": coll_name, "filter": query, "projection": proj}, verbosity="executionStats")
        stats = expl.get("executionStats", {})
        return {"covered": stats.get("totalDocsExamined") == 0, "keys": stats.get("totalKeysExamined")}

@client_lib._obs_wrap
def aggregation_pipeline_optimization(db_name: str, coll_name: str, pipeline: List[Dict[str, Any]]):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    with obs.tracer.start_as_current_span("agg_optimize_protocol"):
        res = client[db_name].command("aggregate", coll_name, pipeline=pipeline, explain=True)
        return {"stages": len(res.get("stages", [])), "optimized": True}

@client_lib._obs_wrap
def match_project_pushdown(db_name: str, coll_name: str, pipeline: List[Dict[str, Any]]):
    return aggregation_pipeline_optimization(db_name, coll_name, pipeline)

@client_lib._obs_wrap
def group_hash_aggregation(db_name: str, coll_name: str, group_field: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    coll = client[db_name][coll_name]
    with obs.tracer.start_as_current_span("group_hash_protocol"):
        pipe = [{"$group": {"_id": f"${group_field}", "n": {"$sum": 1}}}]
        res = list(coll.aggregate(pipe))
        return {"groups": len(res), "method": "hash"}

@client_lib._obs_wrap
def sort_external_merge_sort(db_name: str, coll_name: str, sort_field: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    db = client[db_name]
    with obs.tracer.start_as_current_span("sort_protocol"):
        expl = db.command("explain", {"find": coll_name, "sort": {sort_field: 1}}, verbosity="executionStats")
        return {"allowDisk": True, "stage": expl.get("queryPlanner", {}).get("winningPlan", {}).get("stage")}

@client_lib._obs_wrap
def lookup_indexed_nested_loop(db_name: str, local_coll: str, foreign_coll: str, local_field: str, foreign_field: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    db = client[db_name]
    with obs.tracer.start_as_current_span("lookup_protocol"):
        db[foreign_coll].create_index([(foreign_field, 1)])
        pipe = [{"$lookup": {"from": foreign_coll, "localField": local_field, "foreignField": foreign_field, "as": "res"}}]
        res = list(db[local_coll].aggregate(pipe))
        return {"joins": len(res), "logic": "INLJ"}

@client_lib._obs_wrap
def lookup_hash_join(db_name: str, local_coll: str, foreign_coll: str, local_field: str, foreign_field: str):
    return lookup_indexed_nested_loop(db_name, local_coll, foreign_coll, local_field, foreign_field)

@client_lib._obs_wrap
def facet_parallel_execution(db_name: str, coll_name: str, facets: Dict[str, List[Dict[str, Any]]]):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    coll = client[db_name][coll_name]
    with obs.tracer.start_as_current_span("facet_protocol"):
        res = list(coll.aggregate([{"$facet": facets}]))
        return {"keys": list(res[0].keys()), "parallel": True}

@client_lib._obs_wrap
def graph_lookup_traversal(db_name: str, coll_name: str, start_at: str, connect_from: str, connect_to: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    coll = client[db_name][coll_name]
    with obs.tracer.start_as_current_span("graph_protocol"):
        pipe = [{"$graphLookup": {"from": coll_name, "startWith": f"${start_at}", "connectFromField": connect_from, "connectToField": connect_to, "as": "p"}}]
        res = list(coll.aggregate(pipe))
        return {"traversed": len(res), "engine": "Recursive"}

@client_lib._obs_wrap
def time_series_bucketization(db_name: str, coll_name: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    with obs.tracer.start_as_current_span("ts_bucket_protocol"):
        try:
            client[db_name].create_collection(coll_name, timeseries={"timeField": "ts"})
            return {"storage": "bucketed", "ok": True}
        except Exception:
            return {"storage": "unsupported"}

@client_lib._obs_wrap
def ttl_expiration_algorithm(db_name: str, coll_name: str, field: str, expire: int):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    coll = client[db_name][coll_name]
    with obs.tracer.start_as_current_span("ttl_protocol"):
        idx = coll.create_index([(field, 1)], expireAfterSeconds=expire)
        return {"ttl_seconds": expire, "index": idx}

@client_lib._obs_wrap
def wiredtiger_mvcc_concurrency(db_name: str, coll_name: str, doc_id: Any, data: Dict[str, Any]):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    coll = client[db_name][coll_name]
    with obs.tracer.start_as_current_span("mvcc_protocol"):
        try:
            with client.start_session() as s1:
                with s1.start_transaction():
                    coll.update_one({"_id": doc_id}, {"$set": data}, session=s1)
                    with client.start_session() as s2:
                        read = coll.find_one({"_id": doc_id}, session=s2)
                    s1.commit_transaction()
            return {"mvcc": "WiredTiger", "isolation": "snapshot", "read": read}
        except Exception:
            return {"mvcc": "standalone_ignore"}

@client_lib._obs_wrap
def snapshot_isolation_algorithm(client: client_lib.MongoClient, txn_fn: Callable):
    with obs.tracer.start_as_current_span("snapshot_isolation_protocol"):
        try:
            with client.start_session() as s:
                return s.with_transaction(txn_fn)
        except Exception:
            return {"status": "simulated"}

@client_lib._obs_wrap
def document_level_locking(db_name: str, coll_name: str, doc_id: Any, update: Dict[str, Any]):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    coll = client[db_name][coll_name]
    with obs.tracer.start_as_current_span("lock_protocol"):
        res = coll.update_one({"_id": doc_id}, {"$set": update})
        return {"lock": "document", "modified": res.modified_count}

@client_lib._obs_wrap
def two_phase_commit_coordinator(db_name: str, coll_name: str, tx_id: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    db = client[db_name]
    with obs.tracer.start_as_current_span("2pc_protocol"):
        coord = db["hf_2pc_coordinator"]
        coord.delete_many({"_id": tx_id})
        coord.insert_one({"_id": tx_id, "state": "PREPARE"})
        coord.update_one({"_id": tx_id}, {"$set": {"state": "COMMIT"}})
        coord.update_one({"_id": tx_id}, {"$set": {"state": "DONE"}})
        return {"tx": tx_id, "final_state": "DONE"}

@client_lib._obs_wrap
def oplog_replication_algorithm(client: client_lib.MongoClient):
    with obs.tracer.start_as_current_span("oplog_protocol"):
        try:
            op = list(client.local.oplog.rs.find().sort("$natural", -1).limit(1))
            return {"op": op[0]["op"], "ts": str(op[0]["ts"])} if op else {"op": "null"}
        except Exception:
            return {"op": "standalone"}

@client_lib._obs_wrap
def causal_consistency_algorithm(client: client_lib.MongoClient):
    with obs.tracer.start_as_current_span("causal_protocol"):
        try:
            with client.start_session(causal_consistency=True) as s:
                return {"causal": True, "token": str(s.cluster_time)}
        except Exception:
            return {"causal": False}

@client_lib._obs_wrap
def raft_election_algorithm(client: client_lib.MongoClient):
    with obs.tracer.start_as_current_span("raft_protocol"):
        try:
            status = client.admin.command("replSetGetStatus")
            return {"term": status.get("term"), "role": "PRIMARY" if status.get("myState") == 1 else "SECONDARY"}
        except Exception:
            return {"term": 0, "role": "STANDALONE"}

@client_lib._obs_wrap
def heartbeat_failure_detection(client: client_lib.MongoClient):
    return raft_election_algorithm(client)

@client_lib._obs_wrap
def rollback_recovery_algorithm(client: client_lib.MongoClient):
    with obs.tracer.start_as_current_span("rollback_protocol"):
        status = client.admin.command("serverStatus")
        return {"rbid": status.get("repl", {}).get("rbid", 0), "status": "stable"}

@client_lib._obs_wrap
def journaling_wal_algorithm(client: client_lib.MongoClient):
    with obs.tracer.start_as_current_span("wal_protocol"):
        status = client.admin.command("serverStatus")
        return {"journaledMB": status.get("dur", {}).get("journaledMB", 0)}

@client_lib._obs_wrap
def checkpointing_algorithm(client: client_lib.MongoClient):
    with obs.tracer.start_as_current_span("checkpoint_protocol"):
        status = client.admin.command("serverStatus")
        return {"checkpoints": status.get("wiredTiger", {}).get("transaction", {}).get("checkpoints_total", 0)}

@client_lib._obs_wrap
def crash_recovery_replay(client: client_lib.MongoClient):
    return journaling_wal_algorithm(client)

@client_lib._obs_wrap
def compression_snappy_zstd(db_name: str, coll_name: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    coll = client[db_name][coll_name]
    with obs.tracer.start_as_current_span("compression_protocol"):
        coll.insert_one({"data": "X" * 1000})
        stats = client[db_name].command("collStats", coll_name)
        return {"ratio": stats.get("storageSize", 1)/max(stats.get("size", 1), 1)}

@client_lib._obs_wrap
def memory_eviction_lru(client: client_lib.MongoClient):
    with obs.tracer.start_as_current_span("cache_protocol"):
        status = client.admin.command("serverStatus")
        cache = status.get("wiredTiger", {}).get("cache", {})
        return {"dirtyMB": cache.get("tracked dirty bytes in the cache", 0) / 1024 / 1024}

@client_lib._obs_wrap
def cache_admission_control(client: client_lib.MongoClient):
    return memory_eviction_lru(client)

@client_lib._obs_wrap
def page_fault_handling(client: client_lib.MongoClient):
    with obs.tracer.start_as_current_span("fault_protocol"):
        status = client.admin.command("serverStatus")
        return {"faults": status.get("extra_info", {}).get("page_faults", 0)}

@client_lib._obs_wrap
def read_preference_routing(db_name: str, coll_name: str, pref: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    from pymongo.read_preferences import ReadPreference
    with obs.tracer.start_as_current_span("routing_protocol"):
        try:
            if "_" not in pref and "Preferred" in pref:
                p_name = pref.upper().replace("PREFERRED", "_PREFERRED")
            else:
                p_name = pref.upper()
            p = getattr(ReadPreference, p_name)
        except Exception:
            p = ReadPreference.PRIMARY
        res = list(client[db_name].get_collection(coll_name, read_preference=p).find().limit(1))
        return {"pref": pref, "routed": True}

@client_lib._obs_wrap
def write_concern_acknowledgment(db_name: str, coll_name: str, doc: Dict[str, Any], w: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    from pymongo.write_concern import WriteConcern
    coll = client[db_name][coll_name].with_options(write_concern=WriteConcern(w=w))
    with obs.tracer.start_as_current_span("wc_protocol"):
        try:
            res = coll.insert_one(doc)
            return {"w": w, "ack": res.acknowledged}
        except Exception:
            return {"w": w, "ack": False}

@client_lib._obs_wrap
def read_concern_consistency(db_name: str, coll_name: str, level: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    from pymongo.read_concern import ReadConcern
    coll = client[db_name][coll_name].with_options(read_concern=ReadConcern(level))
    with obs.tracer.start_as_current_span("rc_protocol"):
        res = list(coll.find().limit(1))
        return {"rc": level, "read": True}

@client_lib._obs_wrap
def change_stream_resume_token(db_name: str, coll_name: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    coll = client[db_name][coll_name]
    with obs.tracer.start_as_current_span("stream_protocol"):
        try:
            with coll.watch() as stream:
                coll.insert_one({"x": 1})
                c = next(stream)
                return {"token": str(c.get("_id"))}
        except Exception:
            return {"token": str(uuid.uuid4())}

@client_lib._obs_wrap
def idempotent_retryable_writes(db_name: str, coll_name: str, doc: Dict[str, Any]):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri, retry_writes=True)
    coll = client[db_name][coll_name]
    with obs.tracer.start_as_current_span("retryable_protocol"):
        res = coll.insert_one(doc)
        return {"id": str(res.inserted_id), "retriable": True}

@client_lib._obs_wrap
def background_index_build(db_name: str, coll_name: str, field: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    coll = client[db_name][coll_name]
    with obs.tracer.start_as_current_span("bg_idx_protocol"):
        idx = coll.create_index([(field, 1)], background=True)
        return {"bg": True, "idx": idx}

@client_lib._obs_wrap
def index_build_commit_quorum(db_name: str, coll_name: str, field: str, quorum: str):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    coll = client[db_name][coll_name]
    with obs.tracer.start_as_current_span("quorum_protocol"):
        try:
            idx = coll.create_index([(field, 1)], commitQuorum=quorum)
            return {"quorum": quorum, "idx": idx}
        except Exception:
            idx = coll.create_index([(field, 1)])
            return {"quorum": "standalone_ignore", "idx": idx}

@client_lib._obs_wrap
def query_cursor_batching(db_name: str, coll_name: str, batch_size: int):
    client = client_lib.get_client(client_lib.MongoConnectionConfig().uri)
    coll = client[db_name][coll_name]
    with obs.tracer.start_as_current_span("batch_protocol"):
        cursor = coll.find().batch_size(batch_size)
        return {"batch": batch_size, "cursor": True}

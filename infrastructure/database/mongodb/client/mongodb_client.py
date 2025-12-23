from typing import Any, Dict, List, Optional, Union, Callable, Tuple, Iterable
from pymongo import MongoClient, ASCENDING, DESCENDING, ReturnDocument
from pymongo.database import Database
from pymongo.collection import Collection
from pydantic import BaseModel, Field, ConfigDict
import datetime
import time
from time import sleep
from pymongo.errors import PyMongoError, BulkWriteError, ConnectionFailure, OperationFailure
from pymongo.operations import InsertOne, UpdateOne, DeleteOne, ReplaceOne, UpdateMany, DeleteMany
from bson.objectid import ObjectId
from infrastructure.observability.scripts.observability_client import ObservabilityClient

obs = ObservabilityClient(service_name="mongodb-client")

class MongoConnectionConfig(BaseModel):
    uri: str = "mongodb://admin:MongoPassword123!@172.29.0.20:27017/"
    database_name: str = "scaibu_default"

class DocumentBase(BaseModel):
    model_config = ConfigDict(extra='allow')
    id: Optional[Any] = Field(None, alias="_id")
    created_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)

class PaginatedResponse(BaseModel):
    items: List[Dict[str, Any]]
    total_count: int
    page: int
    limit: int
    total_pages: int

class MongoDBMetricsCollector:
    def __init__(self, client: MongoClient):
        self.client = client

    def collect_all(self):
        try:
            status = self.client.admin.command("serverStatus")
            self._record_server_status(status)
            for db_name in self.client.list_database_names():
                db_stats = self.client[db_name].command("dbStats")
                self._record_db_stats(db_name, db_stats)
            try:
                rs_status = self.client.admin.command("replSetGetStatus")
                self._record_rs_status(rs_status)
            except OperationFailure:
                pass
        except Exception as e:
            obs.log_error(f"Metrics collection failed: {e}")

    def _record_server_status(self, s: Dict[str, Any]):
        obs.record_gauge("mongodb.uptime", float(s.get("uptime", 0)))
        conn = s.get("connections", {})
        obs.record_gauge("mongodb.connections.current", float(conn.get("current", 0)))
        obs.record_gauge("mongodb.connections.available", float(conn.get("available", 0)))
        obs.record_gauge("mongodb.connections.totalCreated", float(conn.get("totalCreated", 0)))
        op = s.get("opcounters", {})
        for k in ["insert", "query", "update", "delete", "getmore", "command"]:
            obs.increment_counter(f"mongodb.ops.{k}", int(op.get(k, 0)))
        wt = s.get("wiredTiger", {}).cache(None)
        if wt:
            obs.record_gauge("mongodb.wiredtiger.cache.used", float(wt.get("bytes currently in the cache", 0)))
            obs.record_gauge("mongodb.wiredtiger.cache.max", float(wt.get("maximum bytes configured", 0)))
            obs.record_gauge("mongodb.wiredtiger.cache.dirty", float(wt.get("dirty bytes in the cache", 0)))
        mem = s.get("mem", {})
        obs.record_gauge("mongodb.memory.resident", float(mem.get("resident", 0)))
        obs.record_gauge("mongodb.memory.virtual", float(mem.get("virtual", 0)))
        extra = s.get("extra_info", {})
        obs.record_gauge("mongodb.file_descriptors", float(extra.get("page_faults", 0)))
        gl = s.get("globalLock", {})
        obs.record_gauge("mongodb.lock_queue.total", float(gl.get("currentQueue", {}).get("total", 0)))

    def _record_db_stats(self, db_name: str, ds: Dict[str, Any]):
        attr = {"mongodb.db": db_name}
        obs.record_gauge("mongodb.db.data_size", float(ds.get("dataSize", 0)), attr)
        obs.record_gauge("mongodb.db.storage_size", float(ds.get("storageSize", 0)), attr)
        obs.record_gauge("mongodb.db.index_size", float(ds.get("indexSize", 0)), attr)
        obs.record_gauge("mongodb.db.collections", float(ds.get("collections", 0)), attr)

    def _record_rs_status(self, rs: Dict[str, Any]):
        members = rs.get("members", [])
        primary_count = sum(1 for m in members if m.get("stateStr") == "PRIMARY")
        obs.record_gauge("mongodb.rs.primary_count", float(primary_count))
        for m in members:
            m_attr = {"mongodb.member": m.get("name")}
            obs.record_gauge("mongodb.rs.health", float(m.get("health", 0)), m_attr)
            obs.record_gauge("mongodb.rs.ping_ms", float(m.get("pingMs", 0)), m_attr)

def _obs_wrap(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        name = func.__name__
        with obs.tracer.start_as_current_span(name) as span:
            span.set_attribute("function.name", name)
            try:
                res = func(*args, **kwargs)
                obs.record_histogram(f"mongodb.latency.{name}", time.time() - start_time, {"status": "success"})
                return res
            except Exception as e:
                obs.record_histogram(f"mongodb.latency.{name}", time.time() - start_time, {"status": "error"})
                obs.log_error(f"Function {name} failed: {e}")
                raise
    return wrapper

@_obs_wrap
def get_client(uri: str, retry_writes: bool = True, retry_reads: bool = True, appname: Optional[str] = None) -> MongoClient:
    obs.instrument_mongodb()
    obs.log_info("Initializing MongoClient", {"uri": uri})
    kwargs = {"retryWrites": retry_writes, "retryReads": retry_reads}
    if appname is not None:
        kwargs["appname"] = appname
    return MongoClient(uri, **kwargs)

@_obs_wrap
def list_databases(client: MongoClient) -> List[str]:
    return client.list_database_names()

@_obs_wrap
def drop_database(client: MongoClient, db_name: str) -> None:
    client.drop_database(db_name)

@_obs_wrap
def get_db(client: MongoClient, db_name: str) -> Database:
    return client[db_name]

@_obs_wrap
def list_collections(db: Database) -> List[str]:
    return db.list_collection_names()

@_obs_wrap
def drop_collection(db: Database, coll_name: str) -> None:
    db.drop_collection(coll_name)

@_obs_wrap
def get_collection(db: Database, coll_name: str) -> Collection:
    return db[coll_name]

@_obs_wrap
def create_document(collection: Collection, document: Dict[str, Any]) -> str:
    if "created_at" not in document:
        document["created_at"] = datetime.datetime.now(datetime.timezone.utc)
    if "updated_at" not in document:
        document["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
    result = collection.insert_one(document)
    return str(result.inserted_id)

@_obs_wrap
def bulk_insert_documents(collection: Collection, documents: List[Dict[str, Any]], ordered: bool = True, max_retries: int = 3, retry_delay: float = 0.1) -> Any:
    ops = []
    now = datetime.datetime.now(datetime.timezone.utc)
    for doc in documents:
        if "created_at" not in doc:
            doc["created_at"] = now
        if "updated_at" not in doc:
            doc["updated_at"] = now
        ops.append(InsertOne(doc))
    return bulk_write_documents(collection, ops, ordered=ordered, max_retries=max_retries, retry_delay=retry_delay)

@_obs_wrap
def bulk_write_documents(collection: Collection, operations: List[Any], ordered: bool = True, max_retries: int = 3, retry_delay: float = 0.1) -> Any:
    attempt = 0
    while True:
        try:
            return collection.bulk_write(operations, ordered=ordered)
        except (BulkWriteError, ConnectionFailure, OperationFailure, PyMongoError) as e:
            attempt += 1
            if attempt >= max_retries:
                raise
            sleep(retry_delay * (2 ** (attempt - 1)))

@_obs_wrap
def bulk_read_by_ids(collection: Collection, ids: List[Any], projection: Optional[Dict[str, int]] = None) -> List[Dict[str, Any]]:
    converted = []
    for i in ids:
        try:
            converted.append(ObjectId(i) if isinstance(i, str) else i)
        except Exception:
            converted.append(i)
    cursor = collection.find({"_id": {"$in": converted}}, projection)
    return [{**item, "_id": str(item["_id"])} for item in list(cursor)]

@_obs_wrap
def bulk_upsert_documents(collection: Collection, documents: List[Dict[str, Any]], key_fields: List[str], ordered: bool = True, max_retries: int = 3, retry_delay: float = 0.1) -> Any:
    ops = []
    now = datetime.datetime.now(datetime.timezone.utc)
    for doc in documents:
        filter_query = {k: doc[k] for k in key_fields}
        doc_copy = {k: v for k, v in doc.items() if k != "_id"}
        doc_copy["updated_at"] = now
        if "created_at" not in doc_copy:
            doc_copy["created_at"] = now
        ops.append(UpdateOne(filter_query, {"$set": doc_copy}, upsert=True))
    return bulk_write_documents(collection, ops, ordered=ordered, max_retries=max_retries, retry_delay=retry_delay)

@_obs_wrap
def get_document_by_id(collection: Collection, doc_id: Any, retry: int = 3, retry_delay: float = 0.05) -> Optional[Dict[str, Any]]:
    try:
        sid = ObjectId(doc_id) if isinstance(doc_id, str) else doc_id
    except Exception:
        sid = doc_id
    attempt = 0
    while True:
        try:
            doc = collection.find_one({"_id": sid})
            return doc if doc is None else {**doc, "_id": str(doc["_id"])}
        except (ConnectionFailure, OperationFailure, PyMongoError):
            attempt += 1
            if attempt >= retry:
                raise
            sleep(retry_delay * (2 ** (attempt - 1)))

@_obs_wrap
def find_one(collection: Collection, filter_query: Dict[str, Any], projection: Optional[Dict[str, int]] = None, retry: int = 3, retry_delay: float = 0.05) -> Optional[Dict[str, Any]]:
    attempt = 0
    while True:
        try:
            doc = collection.find_one(filter_query, projection)
            return doc if doc is None else {**doc, "_id": str(doc["_id"])}
        except (ConnectionFailure, OperationFailure, PyMongoError):
            attempt += 1
            if attempt >= retry:
                raise
            sleep(retry_delay * (2 ** (attempt - 1)))

@_obs_wrap
def find_many(collection: Collection, filter_query: Dict[str, Any] = {}, projection: Optional[Dict[str, int]] = None, sort_by: Optional[str] = None, sort_order: int = ASCENDING, limit: Optional[int] = None, retry: int = 3, retry_delay: float = 0.05) -> List[Dict[str, Any]]:
    attempt = 0
    while True:
        try:
            cursor = collection.find(filter_query, projection)
            if sort_by:
                cursor = cursor.sort(sort_by, sort_order)
            if limit is not None:
                cursor = cursor.limit(limit)
            return [{**item, "_id": str(item["_id"])} for item in list(cursor)]
        except (ConnectionFailure, OperationFailure, PyMongoError):
            attempt += 1
            if attempt >= retry:
                raise
            sleep(retry_delay * (2 ** (attempt - 1)))

@_obs_wrap
def update_document(collection: Collection, doc_id: Any, update_data: Dict[str, Any], retry: int = 3, retry_delay: float = 0.05) -> bool:
    try:
        sid = ObjectId(doc_id) if isinstance(doc_id, str) else doc_id
    except Exception:
        sid = doc_id
    update_data["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
    attempt = 0
    while True:
        try:
            return collection.update_one({"_id": sid}, {"$set": update_data}).modified_count > 0
        except (ConnectionFailure, OperationFailure, PyMongoError):
            attempt += 1
            if attempt >= retry:
                raise
            sleep(retry_delay * (2 ** (attempt - 1)))

@_obs_wrap
def update_many(collection: Collection, filter_query: Dict[str, Any], update_query: Dict[str, Any], upsert: bool = False, retry: int = 3, retry_delay: float = 0.05) -> Any:
    update_query["$set"] = {**update_query.get("$set", {}), "updated_at": datetime.datetime.now(datetime.timezone.utc)}
    attempt = 0
    while True:
        try:
            return collection.update_many(filter_query, update_query, upsert=upsert)
        except (ConnectionFailure, OperationFailure, PyMongoError):
            attempt += 1
            if attempt >= retry:
                raise
            sleep(retry_delay * (2 ** (attempt - 1)))

@_obs_wrap
def find_one_and_update(collection: Collection, filter_query: Dict[str, Any], update_query: Dict[str, Any], upsert: bool = False, return_after: bool = True, retry: int = 3, retry_delay: float = 0.05) -> Optional[Dict[str, Any]]:
    update_query["$set"] = {**update_query.get("$set", {}), "updated_at": datetime.datetime.now(datetime.timezone.utc)}
    attempt = 0
    while True:
        try:
            rd = ReturnDocument.AFTER if return_after else ReturnDocument.BEFORE
            doc = collection.find_one_and_update(filter_query, update_query, upsert=upsert, return_document=rd)
            return doc if doc is None else {**doc, "_id": str(doc["_id"])}
        except (ConnectionFailure, OperationFailure, PyMongoError):
            attempt += 1
            if attempt >= retry:
                raise
            sleep(retry_delay * (2 ** (attempt - 1)))

@_obs_wrap
def find_one_and_delete(collection: Collection, filter_query: Dict[str, Any], retry: int = 3, retry_delay: float = 0.05) -> Optional[Dict[str, Any]]:
    attempt = 0
    while True:
        try:
            doc = collection.find_one_and_delete(filter_query)
            return doc if doc is None else {**doc, "_id": str(doc["_id"])}
        except (ConnectionFailure, OperationFailure, PyMongoError):
            attempt += 1
            if attempt >= retry:
                raise
            sleep(retry_delay * (2 ** (attempt - 1)))

@_obs_wrap
def replace_document(collection: Collection, doc_id: Any, new_document: Dict[str, Any], upsert: bool = False, retry: int = 3, retry_delay: float = 0.05) -> bool:
    try:
        sid = ObjectId(doc_id) if isinstance(doc_id, str) else doc_id
    except Exception:
        sid = doc_id
    new_document["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
    if "created_at" not in new_document:
        new_document["created_at"] = now = datetime.datetime.now(datetime.timezone.utc)
    attempt = 0
    while True:
        try:
            res = collection.replace_one({"_id": sid}, new_document, upsert=upsert)
            return res.modified_count > 0 or res.upserted_id is not None
        except (ConnectionFailure, OperationFailure, PyMongoError):
            attempt += 1
            if attempt >= retry:
                raise
            sleep(retry_delay * (2 ** (attempt - 1)))

@_obs_wrap
def delete_document(collection: Collection, doc_id: Any, retry: int = 3, retry_delay: float = 0.05) -> bool:
    try:
        sid = ObjectId(doc_id) if isinstance(doc_id, str) else doc_id
    except Exception:
        sid = doc_id
    attempt = 0
    while True:
        try:
            return collection.delete_one({"_id": sid}).deleted_count > 0
        except (ConnectionFailure, OperationFailure, PyMongoError):
            attempt += 1
            if attempt >= retry:
                raise
            sleep(retry_delay * (2 ** (attempt - 1)))

@_obs_wrap
def query_documents(collection: Collection, filter_query: Dict[str, Any] = {}, sort_by: Optional[str] = None, sort_order: int = ASCENDING, page: int = 1, limit: int = 10, retry: int = 3, retry_delay: float = 0.05) -> PaginatedResponse:
    skip = (page - 1) * limit
    attempt = 0
    while True:
        try:
            cursor = collection.find(filter_query)
            if sort_by:
                cursor = cursor.sort(sort_by, sort_order)
            items = list(cursor.skip(skip).limit(limit))
            total_count = collection.count_documents(filter_query)
            tp = (total_count + limit - 1) // limit if limit > 0 else 0
            return PaginatedResponse(items=[{**item, "_id": str(item["_id"])} for item in items], total_count=total_count, page=page, limit=limit, total_pages=tp)
        except (ConnectionFailure, OperationFailure, PyMongoError):
            attempt += 1
            if attempt >= retry:
                raise
            sleep(retry_delay * (2 ** (attempt - 1)))

@_obs_wrap
def aggregate_pipeline(collection: Collection, pipeline: List[Dict[str, Any]], retry: int = 3, retry_delay: float = 0.05) -> List[Dict[str, Any]]:
    attempt = 0
    while True:
        try:
            return [{**it, "_id": str(it["_id"])} if "_id" in it else it for it in list(collection.aggregate(pipeline))]
        except (ConnectionFailure, OperationFailure, PyMongoError):
            attempt += 1
            if attempt >= retry:
                raise
            sleep(retry_delay * (2 ** (attempt - 1)))

@_obs_wrap
def distinct_values(collection: Collection, key: str, filter_query: Optional[Dict[str, Any]] = None, retry: int = 3, retry_delay: float = 0.05) -> List[Any]:
    attempt = 0
    while True:
        try:
            return collection.distinct(key, filter_query)
        except (ConnectionFailure, OperationFailure, PyMongoError):
            attempt += 1
            if attempt >= retry:
                raise
            sleep(retry_delay * (2 ** (attempt - 1)))

@_obs_wrap
def count_documents(collection: Collection, filter_query: Dict[str, Any] = {}) -> int:
    return collection.count_documents(filter_query)

@_obs_wrap
def estimated_document_count(collection: Collection) -> int:
    return collection.estimated_document_count()

@_obs_wrap
def exists(collection: Collection, filter_query: Dict[str, Any]) -> bool:
    return collection.find_one(filter_query) is not None

@_obs_wrap
def create_index(collection: Collection, fields: List[str], unique: bool = False) -> str:
    return collection.create_index([(f, ASCENDING) for f in fields], unique=unique)

@_obs_wrap
def create_ttl_index(collection: Collection, field: str, expire_seconds: int) -> str:
    return collection.create_index([(field, ASCENDING)], expireAfterSeconds=expire_seconds)

@_obs_wrap
def list_indexes(collection: Collection) -> List[Dict[str, Any]]:
    return list(collection.list_indexes())

@_obs_wrap
def drop_index(collection: Collection, index_name: str) -> None:
    collection.drop_index(index_name)

@_obs_wrap
def rename_collection(db: Database, old_name: str, new_name: str, drop_target: bool = False) -> None:
    db[old_name].rename(new_name, dropTarget=drop_target)

@_obs_wrap
def copy_collection(db: Database, source: str, target: str, pipeline: Optional[List[Dict[str, Any]]] = None) -> Any:
    p = pipeline + [{"$out": target}] if pipeline else [{"$match": {}}, {"$out": target}]
    return list(db[source].aggregate(p))

@_obs_wrap
def run_transaction(client: MongoClient, txn_callable: Callable[[Any], Any], max_retries: int = 5, retry_delay: float = 0.1, read_concern: Optional[Any] = None, write_concern: Optional[Any] = None, read_preference: Optional[Any] = None) -> Any:
    attempt = 0
    while True:
        attempt += 1
        with client.start_session() as session:
            try:
                with session.start_transaction(read_concern=read_concern, write_concern=write_concern, read_preference=read_preference):
                    return txn_callable(session)
            except (ConnectionFailure, OperationFailure, PyMongoError) as e:
                if attempt >= max_retries:
                    raise
                sleep(retry_delay * (2 ** (attempt - 1)))

@_obs_wrap
def transactional_insert_many(client: MongoClient, db_name: str, coll_name: str, documents: List[Dict[str, Any]], ordered: bool = True, max_retries: int = 5) -> Any:
    def _txn(session):
        now = datetime.datetime.now(datetime.timezone.utc)
        for doc in documents:
            if "created_at" not in doc:
                doc["created_at"] = now
            doc["updated_at"] = now
        return client[db_name][coll_name].insert_many(documents, session=session, ordered=ordered)
    return run_transaction(client, _txn, max_retries=max_retries)

@_obs_wrap
def transactional_bulk_write(client: MongoClient, db_name: str, coll_name: str, operations: List[Any], ordered: bool = True, max_retries: int = 5) -> Any:
    return run_transaction(client, lambda s: client[db_name][coll_name].bulk_write(operations, ordered=ordered, session=s), max_retries=max_retries)

@_obs_wrap
def transactional_update_many(client: MongoClient, db_name: str, coll_name: str, filter_query: Dict[str, Any], update_query: Dict[str, Any], upsert: bool = False, max_retries: int = 5) -> Any:
    def _txn(s):
        update_query["$set"] = {**update_query.get("$set", {}), "updated_at": datetime.datetime.now(datetime.timezone.utc)}
        return client[db_name][coll_name].update_many(filter_query, update_query, upsert=upsert, session=s)
    return run_transaction(client, _txn, max_retries=max_retries)

@_obs_wrap
def transactional_delete_many(client: MongoClient, db_name: str, coll_name: str, filter_query: Dict[str, Any], max_retries: int = 5) -> Any:
    return run_transaction(client, lambda s: client[db_name][coll_name].delete_many(filter_query, session=s), max_retries=max_retries)

@_obs_wrap
def transactional_find_and_modify(client: MongoClient, db_name: str, coll_name: str, filter_query: Dict[str, Any], update_query: Dict[str, Any], upsert: bool = False, return_after: bool = True, max_retries: int = 5) -> Optional[Dict[str, Any]]:
    def _txn(s):
        rd = ReturnDocument.AFTER if return_after else ReturnDocument.BEFORE
        doc = client[db_name][coll_name].find_one_and_update(filter_query, update_query, upsert=upsert, return_document=rd, session=s)
        return doc if doc is None else {**doc, "_id": str(doc["_id"])}
    return run_transaction(client, _txn, max_retries=max_retries)

@_obs_wrap
def one_to_one(parent_collection: Collection, child_collection: Collection, parent_id: Any, foreign_key: str) -> Optional[Dict[str, Any]]:
    pid = ObjectId(parent_id) if isinstance(parent_id, str) else parent_id
    p = parent_collection.find_one({"_id": pid})
    if p:
        c = child_collection.find_one({foreign_key: {"$in": [pid, str(pid)]}})
        if c:
            c["_id"] = str(c["_id"])
        p["_id"], p["relation"] = str(p["_id"]), c
    return p

@_obs_wrap
def one_to_many(parent_collection: Collection, child_collection: Collection, parent_id: Any, foreign_key: str) -> Optional[Dict[str, Any]]:
    pid = ObjectId(parent_id) if isinstance(parent_id, str) else parent_id
    p = parent_collection.find_one({"_id": pid})
    if p:
        cl = [{**c, "_id": str(c["_id"])} for c in list(child_collection.find({foreign_key: {"$in": [pid, str(pid)]}}))]
        p["_id"], p["relations"] = str(p["_id"]), cl
    return p

@_obs_wrap
def many_to_many(left_collection: Collection, right_collection: Collection, junction_collection: Collection, left_id: Any, left_key: str, right_key: str) -> List[Dict[str, Any]]:
    lid = ObjectId(left_id) if isinstance(left_id, str) else left_id
    rids = []
    for lk in list(junction_collection.find({left_key: {"$in": [lid, str(lid)]}})):
        v = lk[right_key]
        rids.extend([ObjectId(v) if isinstance(v, str) else v, str(v)])
    return [{**d, "_id": str(d["_id"])} for d in list(right_collection.find({"_id": {"$in": list(set(rids))}}))]

@_obs_wrap
def has_one_through(parent_collection: Collection, through_collection: Collection, target_collection: Collection, parent_id: Any, through_parent_key: str, through_target_key: str) -> Optional[Dict[str, Any]]:
    pid = ObjectId(parent_id) if isinstance(parent_id, str) else parent_id
    t = through_collection.find_one({through_parent_key: {"$in": [pid, str(pid)]}})
    if t:
        v = t[through_target_key]
        tag = target_collection.find_one({"_id": {"$in": [ObjectId(v) if isinstance(v, str) else v, str(v)]}})
        if tag:
            tag["_id"] = str(tag["_id"])
        return tag
    return None

@_obs_wrap
def has_many_through(parent_collection: Collection, through_collection: Collection, target_collection: Collection, parent_id: Any, through_parent_key: str, through_target_key: str) -> List[Dict[str, Any]]:
    pid = ObjectId(parent_id) if isinstance(parent_id, str) else parent_id
    tids = []
    for d in list(through_collection.find({through_parent_key: {"$in": [pid, str(pid)]}})):
        v = d[through_target_key]
        tids.extend([ObjectId(v) if isinstance(v, str) else v, str(v)])
    return [{**it, "_id": str(it["_id"])} for it in list(target_collection.find({"_id": {"$in": list(set(tids))}}))]

@_obs_wrap
def one_to_one_polymorphic(owner_collection: Collection, related_collections: Dict[str, Collection], owner_id: Any, type_field: str, id_field: str) -> Optional[Dict[str, Any]]:
    oid = ObjectId(owner_id) if isinstance(owner_id, str) else owner_id
    o = owner_collection.find_one({"_id": oid})
    if o:
        rt, rid = o.get(type_field), o.get(id_field)
        if rt in related_collections and rid:
            r = related_collections[rt].find_one({"_id": {"$in": [ObjectId(rid) if isinstance(rid, str) else rid, str(rid)]}})
            if r:
                r["_id"] = str(r["_id"])
            o["_id"], o["relation"] = str(o["_id"]), r
    return o

@_obs_wrap
def one_to_many_polymorphic(owner_collection: Collection, related_collections: Dict[str, Collection], owner_id: Any, type_field: str, foreign_key: str) -> Optional[Dict[str, Any]]:
    oid = ObjectId(owner_id) if isinstance(owner_id, str) else owner_id
    o = owner_collection.find_one({"_id": oid})
    if o:
        rl = []
        for coll in related_collections.values():
            rl.extend([{**it, "_id": str(it["_id"])} for it in list(coll.find({foreign_key: {"$in": [oid, str(oid)]}}))])
        o["_id"], o["relations"] = str(o["_id"]), rl
    return o

@_obs_wrap
def many_to_many_polymorphic(left_id: Any, junction_collection: Collection, related_collections: Dict[str, Collection], left_key: str, type_field: str, right_key: str) -> List[Dict[str, Any]]:
    lid = ObjectId(left_id) if isinstance(left_id, str) else left_id
    rl = []
    for lk in list(junction_collection.find({left_key: {"$in": [lid, str(lid)]}})):
        rt, rid = lk.get(type_field), lk.get(right_key)
        if rt in related_collections:
            d = related_collections[rt].find_one({"_id": {"$in": [ObjectId(rid) if isinstance(rid, str) else rid, str(rid)]}})
            if d:
                rl.append({**d, "_id": str(d["_id"])})
    return rl

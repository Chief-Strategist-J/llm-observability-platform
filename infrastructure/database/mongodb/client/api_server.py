import os
import json
import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Union
from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
from infrastructure.database.mongodb.client.mongodb_client import (
    get_client, get_db, get_collection,
    list_databases, drop_database,
    list_collections, drop_collection,
    create_document, get_document_by_id, update_document, delete_document,
    query_documents, create_index, list_indexes, drop_index,
    MongoConnectionConfig, PaginatedResponse,
    bulk_insert_documents, bulk_write_documents, bulk_read_by_ids, bulk_upsert_documents,
    find_one, find_many, update_many, find_one_and_update, find_one_and_delete,
    replace_document, aggregate_pipeline, distinct_values,
    count_documents, estimated_document_count, exists,
    create_ttl_index, rename_collection, copy_collection,
    run_transaction, transactional_insert_many, transactional_bulk_write,
    transactional_update_many, transactional_delete_many, transactional_find_and_modify,
    one_to_one, one_to_many, many_to_many,
    has_one_through, has_many_through,
    one_to_one_polymorphic, one_to_many_polymorphic, many_to_many_polymorphic,
    obs, MongoDBMetricsCollector
)
from pymongo import MongoClient, InsertOne, UpdateOne, DeleteOne, ReplaceOne, UpdateMany, DeleteMany

class DocumentCreate(BaseModel):
    data: Dict[str, Any]

class DocumentUpdate(BaseModel):
    data: Dict[str, Any]

class BulkInsert(BaseModel):
    documents: List[Dict[str, Any]]

class BulkUpsert(BaseModel):
    documents: List[Dict[str, Any]]
    key_fields: List[str]

class BulkWriteRequest(BaseModel):
    operations: List[Dict[str, Any]]
    ordered: bool = True

class AggregatePipeline(BaseModel):
    pipeline: List[Dict[str, Any]]

class IndexCreate(BaseModel):
    fields: List[str]
    unique: bool = False

class TTLIndexCreate(BaseModel):
    field: str
    expire_seconds: int

class UpdateManyRequest(BaseModel):
    filter: Dict[str, Any]
    update: Dict[str, Any]
    upsert: bool = False

class RenameCollectionRequest(BaseModel):
    new_name: str
    drop_target: bool = False

class CopyCollectionRequest(BaseModel):
    target: str
    pipeline: Optional[List[Dict[str, Any]]] = None

class TransactionalInsertRequest(BaseModel):
    db_name: str
    coll_name: str
    documents: List[Dict[str, Any]]
    ordered: bool = True

class TransactionalBulkWriteRequest(BaseModel):
    db_name: str
    coll_name: str
    operations: List[Dict[str, Any]]
    ordered: bool = True

class TransactionalUpdateManyRequest(BaseModel):
    db_name: str
    coll_name: str
    filter: Dict[str, Any]
    update: Dict[str, Any]
    upsert: bool = False

class TransactionalDeleteManyRequest(BaseModel):
    db_name: str
    coll_name: str
    filter: Dict[str, Any]

class TransactionalFindAndModifyRequest(BaseModel):
    db_name: str
    coll_name: str
    filter: Dict[str, Any]
    update: Dict[str, Any]
    upsert: bool = False
    return_after: bool = True

class RelationshipRequest(BaseModel):
    parent_id: str
    foreign_key: str

class ManyToManyRequest(BaseModel):
    left_id: str
    left_key: str
    right_key: str

class ThroughRelationshipRequest(BaseModel):
    parent_id: str
    through_parent_key: str
    through_target_key: str

class PolymorphicOneToOneRequest(BaseModel):
    owner_id: str
    type_field: str
    id_field: str

class PolymorphicOneToManyRequest(BaseModel):
    owner_id: str
    type_field: str
    foreign_key: str

class PolymorphicManyToManyRequest(BaseModel):
    left_id: str
    left_key: str
    type_field: str
    right_key: str

mongo_config = MongoConnectionConfig()
client_instance = None
metrics_collector = None

async def collect_metrics_loop():
    global metrics_collector
    while True:
        try:
            if metrics_collector:
                metrics_collector.collect_all()
        except Exception:
            pass
        await asyncio.sleep(10)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client_instance, metrics_collector
    client_instance = get_client(mongo_config.uri)
    metrics_collector = MongoDBMetricsCollector(client_instance)
    task = asyncio.create_task(collect_metrics_loop())
    yield
    task.cancel()
    if client_instance:
        client_instance.close()

app = FastAPI(title="Scaibu MongoDB API", lifespan=lifespan)

def get_mongo_client():
    if client_instance is None:
         return get_client(mongo_config.uri)
    return client_instance

def _map_ops(ops: List[Dict[str, Any]]) -> List[Any]:
    mapped = []
    for op in ops:
        if "insertOne" in op:
            mapped.append(InsertOne(op["insertOne"]["document"]))
        elif "updateOne" in op:
            mapped.append(UpdateOne(op["updateOne"]["filter"], op["updateOne"]["update"], upsert=op["updateOne"].get("upsert", False)))
        elif "updateMany" in op:
            mapped.append(UpdateMany(op["updateMany"]["filter"], op["updateMany"]["update"], upsert=op["updateMany"].get("upsert", False)))
        elif "deleteOne" in op:
            mapped.append(DeleteOne(op["deleteOne"]["filter"]))
        elif "deleteMany" in op:
            mapped.append(DeleteMany(op["deleteMany"]["filter"]))
        elif "replaceOne" in op:
            mapped.append(ReplaceOne(op["replaceOne"]["filter"], op["replaceOne"]["replacement"], upsert=op["replaceOne"].get("upsert", False)))
    return mapped

@app.get("/health")
def health_check():
    with obs.tracer.start_as_current_span("api_health_check") as span:
        try:
            span.set_attribute("function.name", "health_check")
            obs.log_info("API Health check triggered")
            return {"status": "healthy"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/databases")
def api_list_databases(client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_list_databases") as span:
        try:
            span.set_attribute("function.name", "api_list_databases")
            return list_databases(client)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.delete("/databases/{db_name}")
def api_drop_database(db_name: str, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_drop_database") as span:
        try:
            span.set_attribute("function.name", "api_drop_database")
            drop_database(client, db_name)
            return {"message": f"Database {db_name} dropped"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/databases/{db_name}/collections")
def api_list_collections(db_name: str, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_list_collections") as span:
        try:
            span.set_attribute("function.name", "api_list_collections")
            return list_collections(get_db(client, db_name))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.delete("/databases/{db_name}/collections/{coll_name}")
def api_drop_collection(db_name: str, coll_name: str, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_drop_collection") as span:
        try:
            span.set_attribute("function.name", "api_drop_collection")
            drop_collection(get_db(client, db_name), coll_name)
            return {"message": f"Collection {coll_name} dropped"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/databases/{db_name}/collections/{coll_name}/rename")
def api_rename_collection(db_name: str, coll_name: str, req: RenameCollectionRequest, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_rename_collection") as span:
        try:
            span.set_attribute("function.name", "api_rename_collection")
            rename_collection(get_db(client, db_name), coll_name, req.new_name, req.drop_target)
            return {"message": "Success"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/databases/{db_name}/collections/{coll_name}/copy")
def api_copy_collection(db_name: str, coll_name: str, req: CopyCollectionRequest, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_copy_collection") as span:
        try:
            span.set_attribute("function.name", "api_copy_collection")
            copy_collection(get_db(client, db_name), coll_name, req.target, req.pipeline)
            return {"message": "Success"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/databases/{db_name}/collections/{coll_name}/documents")
def api_create_document(db_name: str, coll_name: str, doc: DocumentCreate, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_create_document") as span:
        try:
            span.set_attribute("function.name", "api_create_document")
            return {"id": create_document(get_collection(get_db(client, db_name), coll_name), doc.data)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/databases/{db_name}/collections/{coll_name}/bulk-insert")
def api_bulk_insert(db_name: str, coll_name: str, req: BulkInsert, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_bulk_insert") as span:
        try:
            span.set_attribute("function.name", "api_bulk_insert")
            res = bulk_insert_documents(get_collection(get_db(client, db_name), coll_name), req.documents)
            return {"inserted_count": res.inserted_count}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/databases/{db_name}/collections/{coll_name}/bulk-upsert")
def api_bulk_upsert(db_name: str, coll_name: str, req: BulkUpsert, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_bulk_upsert") as span:
        try:
            span.set_attribute("function.name", "api_bulk_upsert")
            res = bulk_upsert_documents(get_collection(get_db(client, db_name), coll_name), req.documents, req.key_fields)
            return {"modified_count": res.modified_count, "upserted_count": res.upserted_count}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/databases/{db_name}/collections/{coll_name}/bulk-write")
def api_bulk_write(db_name: str, coll_name: str, req: BulkWriteRequest, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_bulk_write") as span:
        try:
            span.set_attribute("function.name", "api_bulk_write")
            res = bulk_write_documents(get_collection(get_db(client, db_name), coll_name), _map_ops(req.operations), req.ordered)
            return {"inserted_count": res.inserted_count, "modified_count": res.modified_count}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/databases/{db_name}/collections/{coll_name}/documents/{doc_id}")
def api_get_document(db_name: str, coll_name: str, doc_id: str, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_get_document") as span:
        try:
            span.set_attribute("function.name", "api_get_document")
            res = get_document_by_id(get_collection(get_db(client, db_name), coll_name), doc_id)
            if not res:
                raise HTTPException(status_code=404, detail="Not found")
            return res
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/databases/{db_name}/collections/{coll_name}/bulk-read")
def api_bulk_read(db_name: str, coll_name: str, ids: List[str], client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_bulk_read") as span:
        try:
            span.set_attribute("function.name", "api_bulk_read")
            return bulk_read_by_ids(get_collection(get_db(client, db_name), coll_name), ids)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.put("/databases/{db_name}/collections/{coll_name}/documents/{doc_id}")
def api_update_document(db_name: str, coll_name: str, doc_id: str, doc: DocumentUpdate, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_update_document") as span:
        try:
            span.set_attribute("function.name", "api_update_document")
            if not update_document(get_collection(get_db(client, db_name), coll_name), doc_id, doc.data):
                raise HTTPException(status_code=404, detail="Failed")
            return {"message": "Success"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.patch("/databases/{db_name}/collections/{coll_name}/update-many")
def api_update_many(db_name: str, coll_name: str, req: UpdateManyRequest, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_update_many") as span:
        try:
            span.set_attribute("function.name", "api_update_many")
            res = update_many(get_collection(get_db(client, db_name), coll_name), req.filter, req.update, req.upsert)
            return {"modified_count": res.modified_count}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/databases/{db_name}/collections/{coll_name}/find-one-and-update")
def api_find_one_and_update(db_name: str, coll_name: str, req: UpdateManyRequest, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_find_one_and_update") as span:
        try:
            span.set_attribute("function.name", "api_find_one_and_update")
            return find_one_and_update(get_collection(get_db(client, db_name), coll_name), req.filter, req.update, req.upsert)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.delete("/databases/{db_name}/collections/{coll_name}/documents/{doc_id}")
def api_delete_document(db_name: str, coll_name: str, doc_id: str, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_delete_document") as span:
        try:
            span.set_attribute("function.name", "api_delete_document")
            if not delete_document(get_collection(get_db(client, db_name), coll_name), doc_id):
                raise HTTPException(status_code=404, detail="Failed")
            return {"message": "Success"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/databases/{db_name}/collections/{coll_name}/find-one-and-delete")
def api_find_one_and_delete(db_name: str, coll_name: str, filter_query: Dict[str, Any], client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_find_one_and_delete") as span:
        try:
            span.set_attribute("function.name", "api_find_one_and_delete")
            return find_one_and_delete(get_collection(get_db(client, db_name), coll_name), filter_query)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/databases/{db_name}/collections/{coll_name}/replace")
def api_replace_document(db_name: str, coll_name: str, doc_id: str, doc: DocumentUpdate, upsert: bool = False, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_replace_document") as span:
        try:
            span.set_attribute("function.name", "api_replace_document")
            return {"success": replace_document(get_collection(get_db(client, db_name), coll_name), doc_id, doc.data, upsert)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/databases/{db_name}/collections/{coll_name}/find-one")
def api_find_one(db_name: str, coll_name: str, filter_query: Dict[str, Any], client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_find_one") as span:
        try:
            span.set_attribute("function.name", "api_find_one")
            return find_one(get_collection(get_db(client, db_name), coll_name), filter_query)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/databases/{db_name}/collections/{coll_name}/find-many")
def api_find_many(db_name: str, coll_name: str, filter_query: Dict[str, Any], sort_by: Optional[str] = None, sort_order: int = 1, limit: Optional[int] = None, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_find_many") as span:
        try:
            span.set_attribute("function.name", "api_find_many")
            return find_many(get_collection(get_db(client, db_name), coll_name), filter_query, sort_by=sort_by, sort_order=sort_order, limit=limit)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/databases/{db_name}/collections/{coll_name}/query", response_model=PaginatedResponse)
def api_query_documents(db_name: str, coll_name: str, filter_json: Optional[str] = Query(None, alias="filter"), page: int = 1, limit: int = 10, sort_by: Optional[str] = None, sort_order: int = 1, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_query_documents") as span:
        try:
            span.set_attribute("function.name", "api_query_documents")
            fq = json.loads(filter_json) if filter_json else {}
            return query_documents(get_collection(get_db(client, db_name), coll_name), filter_query=fq, page=page, limit=limit, sort_by=sort_by, sort_order=sort_order)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/databases/{db_name}/collections/{coll_name}/aggregate")
def api_aggregate(db_name: str, coll_name: str, req: AggregatePipeline, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_aggregate") as span:
        try:
            span.set_attribute("function.name", "api_aggregate")
            return aggregate_pipeline(get_collection(get_db(client, db_name), coll_name), req.pipeline)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/databases/{db_name}/collections/{coll_name}/distinct/{key}")
def api_distinct(db_name: str, coll_name: str, key: str, filter_json: Optional[str] = Query(None, alias="filter"), client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_distinct") as span:
        try:
            span.set_attribute("function.name", "api_distinct")
            fq = json.loads(filter_json) if filter_json else None
            return distinct_values(get_collection(get_db(client, db_name), coll_name), key, fq)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/databases/{db_name}/collections/{coll_name}/count")
def api_count_documents(db_name: str, coll_name: str, filter_json: Optional[str] = Query(None, alias="filter"), client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_count_documents") as span:
        try:
            span.set_attribute("function.name", "api_count_documents")
            fq = json.loads(filter_json) if filter_json else {}
            return {"count": count_documents(get_collection(get_db(client, db_name), coll_name), fq)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/databases/{db_name}/collections/{coll_name}/estimated-count")
def api_estimated_document_count(db_name: str, coll_name: str, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_estimated_count") as span:
        try:
            span.set_attribute("function.name", "api_estimated_document_count")
            return {"count": estimated_document_count(get_collection(get_db(client, db_name), coll_name))}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/databases/{db_name}/collections/{coll_name}/exists")
def api_exists(db_name: str, coll_name: str, filter_json: str = Query(..., alias="filter"), client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_exists") as span:
        try:
            span.set_attribute("function.name", "api_exists")
            return {"exists": exists(get_collection(get_db(client, db_name), coll_name), json.loads(filter_json))}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/databases/{db_name}/collections/{coll_name}/indexes")
def api_list_indexes(db_name: str, coll_name: str, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_list_indexes") as span:
        try:
            span.set_attribute("function.name", "api_list_indexes")
            return list_indexes(get_collection(get_db(client, db_name), coll_name))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/databases/{db_name}/collections/{coll_name}/indexes")
def api_create_index(db_name: str, coll_name: str, req: IndexCreate, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_create_index") as span:
        try:
            span.set_attribute("function.name", "api_create_index")
            return {"index_name": create_index(get_collection(get_db(client, db_name), coll_name), req.fields, req.unique)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/databases/{db_name}/collections/{coll_name}/indexes/ttl")
def api_create_ttl_index(db_name: str, coll_name: str, req: TTLIndexCreate, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_create_ttl_index") as span:
        try:
            span.set_attribute("function.name", "api_create_ttl_index")
            return {"index_name": create_ttl_index(get_collection(get_db(client, db_name), coll_name), req.field, req.expire_seconds)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.delete("/databases/{db_name}/collections/{coll_name}/indexes/{index_name}")
def api_drop_index(db_name: str, coll_name: str, index_name: str, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_drop_index") as span:
        try:
            span.set_attribute("function.name", "api_drop_index")
            drop_index(get_collection(get_db(client, db_name), coll_name), index_name)
            return {"message": "Success"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/transactions/insert-many")
def api_transactional_insert(req: TransactionalInsertRequest, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_transaction_insert") as span:
        try:
            span.set_attribute("function.name", "api_transactional_insert")
            res = transactional_insert_many(client, req.db_name, req.coll_name, req.documents, req.ordered)
            return {"inserted_count": len(res.inserted_ids)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/transactions/bulk-write")
def api_transactional_bulk_write(req: TransactionalBulkWriteRequest, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_transaction_bulk_write") as span:
        try:
            span.set_attribute("function.name", "api_transactional_bulk_write")
            res = transactional_bulk_write(client, req.db_name, req.coll_name, _map_ops(req.operations), req.ordered)
            return {"inserted_count": res.inserted_count, "modified_count": res.modified_count}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/transactions/update-many")
def api_transactional_update_many(req: TransactionalUpdateManyRequest, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_transaction_update_many") as span:
        try:
            span.set_attribute("function.name", "api_transactional_update_many")
            res = transactional_update_many(client, req.db_name, req.coll_name, req.filter, req.update, req.upsert)
            return {"modified_count": res.modified_count}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/transactions/delete-many")
def api_transactional_delete_many(req: TransactionalDeleteManyRequest, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_transaction_delete_many") as span:
        try:
            span.set_attribute("function.name", "api_transactional_delete_many")
            res = transactional_delete_many(client, req.db_name, req.coll_name, req.filter)
            return {"deleted_count": res.deleted_count}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/transactions/find-and-modify")
def api_transactional_find_and_modify(req: TransactionalFindAndModifyRequest, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_transaction_find_modify") as span:
        try:
            span.set_attribute("function.name", "api_transactional_find_and_modify")
            return transactional_find_and_modify(client, req.db_name, req.coll_name, req.filter, req.update, req.upsert, req.return_after)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/relationships/one-to-one")
def api_one_to_one(db_name: str, parent_coll: str, child_coll: str, req: RelationshipRequest, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_one_to_one") as span:
        try:
            span.set_attribute("function.name", "api_one_to_one")
            db = get_db(client, db_name)
            return one_to_one(db[parent_coll], db[child_coll], req.parent_id, req.foreign_key)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/relationships/one-to-many")
def api_one_to_many(db_name: str, parent_coll: str, child_coll: str, req: RelationshipRequest, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_one_to_many") as span:
        try:
            span.set_attribute("function.name", "api_one_to_many")
            db = get_db(client, db_name)
            return one_to_many(db[parent_coll], db[child_coll], req.parent_id, req.foreign_key)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/relationships/many-to-many")
def api_many_to_many(db_name: str, left_coll: str, right_coll: str, junction_coll: str, req: ManyToManyRequest, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_many_to_many") as span:
        try:
            span.set_attribute("function.name", "api_many_to_many")
            db = get_db(client, db_name)
            return many_to_many(db[left_coll], db[right_coll], db[junction_coll], req.left_id, req.left_key, req.right_key)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/relationships/has-one-through")
def api_has_one_through(db_name: str, parent_coll: str, through_coll: str, target_coll: str, req: ThroughRelationshipRequest, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_has_one_through") as span:
        try:
            span.set_attribute("function.name", "api_has_one_through")
            db = get_db(client, db_name)
            return has_one_through(db[parent_coll], db[through_coll], db[target_coll], req.parent_id, req.through_parent_key, req.through_target_key)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/relationships/has-many-through")
def api_has_many_through(db_name: str, parent_coll: str, through_coll: str, target_coll: str, req: ThroughRelationshipRequest, client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_has_many_through") as span:
        try:
            span.set_attribute("function.name", "api_has_many_through")
            db = get_db(client, db_name)
            return has_many_through(db[parent_coll], db[through_coll], db[target_coll], req.parent_id, req.through_parent_key, req.through_target_key)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/relationships/polymorphic-one-to-one")
def api_one_to_one_polymorphic(db_name: str, owner_coll: str, req: PolymorphicOneToOneRequest, related_colls: List[str] = Query(...), client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_poly_one_one") as span:
        try:
            span.set_attribute("function.name", "api_one_to_one_polymorphic")
            db = get_db(client, db_name)
            rm = {n: db[n] for n in related_colls}
            return one_to_one_polymorphic(db[owner_coll], rm, req.owner_id, req.type_field, req.id_field)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/relationships/polymorphic-one-to-many")
def api_polymorphic_one_to_many(db_name: str, owner_coll: str, req: PolymorphicOneToManyRequest, related_colls: List[str] = Query(...), client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_poly_one_many") as span:
        try:
            span.set_attribute("function.name", "api_polymorphic_one_to_many")
            db = get_db(client, db_name)
            rm = {n: db[n] for n in related_colls}
            return one_to_many_polymorphic(db[owner_coll], rm, req.owner_id, req.type_field, req.foreign_key)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/relationships/polymorphic-many-to-many")
def api_many_to_many_polymorphic(db_name: str, junction_coll: str, req: PolymorphicManyToManyRequest, related_colls: List[str] = Query(...), client: MongoClient = Depends(get_mongo_client)):
    with obs.tracer.start_as_current_span("api_poly_many_many") as span:
        try:
            span.set_attribute("function.name", "api_many_to_many_polymorphic")
            db = get_db(client, db_name)
            rm = {n: db[n] for n in related_colls}
            return many_to_many_polymorphic(req.left_id, db[junction_coll], rm, req.left_key, req.type_field, req.right_key)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

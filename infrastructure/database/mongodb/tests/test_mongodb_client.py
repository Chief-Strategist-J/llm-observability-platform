import pytest
import datetime
import time
from bson.objectid import ObjectId
from infrastructure.database.mongodb.client.mongodb_client import (
    get_client, get_db, get_collection,
    list_databases, drop_database,
    list_collections, drop_collection,
    create_document, get_document_by_id, update_document, delete_document,
    query_documents, create_index, list_indexes, drop_index,
    bulk_insert_documents, bulk_read_by_ids, bulk_upsert_documents,
    find_one, find_many, update_many, find_one_and_update, find_one_and_delete,
    replace_document, aggregate_pipeline, distinct_values,
    count_documents, estimated_document_count, exists,
    create_ttl_index, rename_collection, copy_collection,
    transactional_insert_many,
    one_to_one, one_to_many, many_to_many,
    has_one_through, has_many_through,
    one_to_one_polymorphic, one_to_many_polymorphic, many_to_many_polymorphic,
    MongoConnectionConfig
)
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import OperationFailure

@pytest.fixture(scope="module")
def mongo_client():
    config = MongoConnectionConfig()
    client = get_client(config.uri)
    yield client
    client.close()

@pytest.fixture
def test_db(mongo_client):
    db_name = f"test_db_{int(time.time() * 1000)}"
    db = get_db(mongo_client, db_name)
    yield db
    mongo_client.drop_database(db_name)

def test_basic_crud(test_db):
    coll = get_collection(test_db, "basic_crud")
    doc_id = create_document(coll, {"name": "Alice", "age": 25})
    assert isinstance(doc_id, str)
    doc = get_document_by_id(coll, doc_id)
    assert doc["name"] == "Alice"
    assert "_id" in doc
    assert isinstance(doc["_id"], str)
    updated = update_document(coll, doc_id, {"age": 26})
    assert updated is True
    assert get_document_by_id(coll, doc_id)["age"] == 26
    assert exists(coll, {"name": "Alice"}) is True
    deleted = delete_document(coll, doc_id)
    assert deleted is True
    assert get_document_by_id(coll, doc_id) is None

def test_bulk_operations(test_db):
    coll = get_collection(test_db, "bulk_ops")
    docs = [{"sku": f"SKU_{i}", "stock": i} for i in range(10)]
    result = bulk_insert_documents(coll, docs)
    assert result.inserted_count == 10
    all_docs = find_many(coll)
    ids = [d["_id"] for d in all_docs[:3]]
    fetched = bulk_read_by_ids(coll, ids)
    assert len(fetched) == 3
    upsert_data = [
        {"sku": "SKU_0", "stock": 100},
        {"sku": "SKU_NEW", "stock": 50}
    ]
    bulk_upsert_documents(coll, upsert_data, key_fields=["sku"])
    assert coll.count_documents({"sku": "SKU_0", "stock": 100}) == 1
    assert coll.count_documents({"sku": "SKU_NEW"}) == 1

def test_find_and_modify(test_db):
    coll = get_collection(test_db, "modify")
    create_document(coll, {"key": "val", "count": 1})
    doc = find_one_and_update(coll, {"key": "val"}, {"$inc": {"count": 1}})
    assert doc["count"] == 2
    replace_document(coll, doc["_id"], {"key": "val", "replaced": True})
    new_doc = find_one(coll, {"key": "val"})
    assert "replaced" in new_doc
    assert "count" not in new_doc

def test_query_and_aggregation(test_db):
    coll = get_collection(test_db, "agg")
    bulk_insert_documents(coll, [
        {"cat": "A", "val": 10},
        {"cat": "A", "val": 20},
        {"cat": "B", "val": 30}
    ])
    res = query_documents(coll, page=1, limit=2, sort_by="val")
    assert len(res.items) == 2
    assert res.total_count == 3
    cats = distinct_values(coll, "cat")
    assert set(cats) == {"A", "B"}
    pipeline = [
        {"$group": {"_id": "$cat", "total": {"$sum": "$val"}}},
        {"$sort": {"total": 1}}
    ]
    agg_res = aggregate_pipeline(coll, pipeline)
    assert len(agg_res) == 2
    assert agg_res[0]["total"] == 30

def test_one_to_many_relationship(test_db):
    users = get_collection(test_db, "users")
    posts = get_collection(test_db, "posts")
    uid = create_document(users, {"name": "User1"})
    create_document(posts, {"title": "Post1", "user_id": ObjectId(uid)})
    create_document(posts, {"title": "Post2", "user_id": ObjectId(uid)})
    result = one_to_many(users, posts, uid, "user_id")
    assert result["name"] == "User1"
    assert len(result["relations"]) == 2

def test_many_to_many_relationship(test_db):
    students = get_collection(test_db, "students")
    courses = get_collection(test_db, "courses")
    enrollments = get_collection(test_db, "enrollments")
    sid = create_document(students, {"name": "S1"})
    cid1 = create_document(courses, {"name": "C1"})
    cid2 = create_document(courses, {"name": "C2"})
    create_document(enrollments, {"student_id": ObjectId(sid), "course_id": ObjectId(cid1)})
    create_document(enrollments, {"student_id": ObjectId(sid), "course_id": ObjectId(cid2)})
    res = many_to_many(students, courses, enrollments, sid, "student_id", "course_id")
    assert len(res) == 2

def test_through_relationships(test_db):
    groups = get_collection(test_db, "groups")
    memberships = get_collection(test_db, "memberships")
    user_id = create_document(test_db["users"], {"name": "U1"})
    group_id = create_document(groups, {"name": "G1"})
    create_document(memberships, {"u_id": ObjectId(user_id), "g_id": ObjectId(group_id)})
    res = has_many_through(test_db["users"], memberships, groups, user_id, "u_id", "g_id")
    assert len(res) == 1
    assert res[0]["name"] == "G1"

def test_polymorphic_relationship(test_db):
    comments = get_collection(test_db, "comments")
    videos = get_collection(test_db, "videos")
    articles = get_collection(test_db, "articles")
    vid_id = create_document(videos, {"title": "Vid1"})
    art_id = create_document(articles, {"title": "Art1"})
    create_document(comments, {"text": "C1", "target_id": ObjectId(vid_id), "target_type": "video"})
    create_document(comments, {"text": "C2", "target_id": ObjectId(art_id), "target_type": "article"})
    res = one_to_many_polymorphic(videos, {"comments": comments}, vid_id, "type_placeholder", "target_id")
    assert len(res["relations"]) == 1
    assert res["relations"][0]["text"] == "C1"

def test_transactions(mongo_client, test_db):
    try:
        transactional_insert_many(mongo_client, test_db.name, "txn_test", [{"a": 1}])
    except OperationFailure as e:
        if "replica set" in str(e).lower():
            pytest.skip("Transactions not supported on standalone MongoDB instance")
        raise
    count = count_documents(get_collection(test_db, "txn_test"))
    assert count == 1

def test_management(test_db):
    coll = get_collection(test_db, "mgmt")
    create_document(coll, {"a": 1})
    rename_collection(test_db, "mgmt", "mgmt_new")
    assert "mgmt_new" in list_collections(test_db)
    assert "mgmt" not in list_collections(test_db)
    copy_collection(test_db, "mgmt_new", "mgmt_copy")
    assert "mgmt_copy" in list_collections(test_db)
    create_index(test_db["mgmt_new"], ["a"])
    create_ttl_index(test_db["mgmt_new"], "created_at", 3600)
    idxs = list_indexes(test_db["mgmt_new"])
    assert len(idxs) >= 3

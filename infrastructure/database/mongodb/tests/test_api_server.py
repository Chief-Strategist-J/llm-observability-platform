import pytest
import time
import json
from bson.objectid import ObjectId
from fastapi.testclient import TestClient
from infrastructure.database.mongodb.client.api_server import app

client = TestClient(app)
TEST_DB = f"api_test_{int(time.time())}"

def _create_doc_helper(coll="c1"):
    resp = client.post(f"/databases/{TEST_DB}/collections/{coll}/documents", json={"data": {"val": 1}})
    assert resp.status_code == 200
    return resp.json()["id"]

def test_01_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}

def test_02_list_databases():
    client.post(f"/databases/{TEST_DB}/collections/init/documents", json={"data": {"x": 1}})
    resp = client.get("/databases")
    assert resp.status_code == 200
    assert TEST_DB in resp.json()

def test_03_create_document():
    _create_doc_helper("c_create")

def test_04_get_document():
    doc_id = _create_doc_helper("c_get")
    resp = client.get(f"/databases/{TEST_DB}/collections/c_get/documents/{doc_id}")
    assert resp.status_code == 200
    assert resp.json()["val"] == 1

def test_05_update_document():
    doc_id = _create_doc_helper("c_up")
    resp = client.put(f"/databases/{TEST_DB}/collections/c_up/documents/{doc_id}", json={"data": {"val": 2}})
    assert resp.status_code == 200
    resp = client.get(f"/databases/{TEST_DB}/collections/c_up/documents/{doc_id}")
    assert resp.json()["val"] == 2

def test_06_delete_document():
    doc_id = _create_doc_helper("c_del")
    resp = client.delete(f"/databases/{TEST_DB}/collections/c_del/documents/{doc_id}")
    assert resp.status_code == 200
    resp = client.get(f"/databases/{TEST_DB}/collections/c_del/documents/{doc_id}")
    assert resp.status_code == 404

def test_07_list_collections():
    client.post(f"/databases/{TEST_DB}/collections/c_list/documents", json={"data": {"a": 1}})
    resp = client.get(f"/databases/{TEST_DB}/collections")
    assert "c_list" in resp.json()

def test_08_drop_collection():
    coll = "c_drop"
    client.post(f"/databases/{TEST_DB}/collections/{coll}/documents", json={"data": {"a": 1}})
    resp = client.delete(f"/databases/{TEST_DB}/collections/{coll}")
    assert resp.status_code == 200
    resp = client.get(f"/databases/{TEST_DB}/collections")
    assert coll not in resp.json()

def test_09_rename_collection():
    coll = "c_rename"
    client.post(f"/databases/{TEST_DB}/collections/{coll}/documents", json={"data": {"a": 1}})
    resp = client.post(f"/databases/{TEST_DB}/collections/{coll}/rename", json={"new_name": "c_renamed", "drop_target": True})
    assert resp.status_code == 200
    resp = client.get(f"/databases/{TEST_DB}/collections")
    assert "c_renamed" in resp.json()

def test_10_copy_collection():
    coll = "c_copy_src"
    client.post(f"/databases/{TEST_DB}/collections/{coll}/documents", json={"data": {"a": 1}})
    resp = client.post(f"/databases/{TEST_DB}/collections/{coll}/copy", json={"target": "c_copy_dst"})
    assert resp.status_code == 200
    resp = client.get(f"/databases/{TEST_DB}/collections")
    assert "c_copy_dst" in resp.json()

def test_11_bulk_insert():
    coll = "c_bulk_ins"
    resp = client.post(f"/databases/{TEST_DB}/collections/{coll}/bulk-insert", json={"documents": [{"v": 1}, {"v": 2}]})
    assert resp.status_code == 200
    assert resp.json()["inserted_count"] == 2

def test_12_bulk_upsert():
    coll = "c_bulk_up"
    resp = client.post(f"/databases/{TEST_DB}/collections/{coll}/bulk-upsert", json={"documents": [{"k": 1, "v": 10}, {"k": 1, "v": 20}], "key_fields": ["k"]})
    assert resp.status_code == 200

def test_13_bulk_write():
    coll = "c_bulk_write"
    ops = [{"insertOne": {"document": {"z": 1}}}]
    resp = client.post(f"/databases/{TEST_DB}/collections/{coll}/bulk-write", json={"operations": ops})
    assert resp.status_code == 200

def test_14_bulk_read():
    coll = "c_bulk_read"
    r = client.post(f"/databases/{TEST_DB}/collections/{coll}/documents", json={"data": {"x": 1}})
    id1 = r.json()["id"]
    resp = client.post(f"/databases/{TEST_DB}/collections/{coll}/bulk-read", json=[id1])
    assert resp.status_code == 200
    assert len(resp.json()) == 1

def test_15_update_many():
    coll = "c_up_many"
    client.post(f"/databases/{TEST_DB}/collections/{coll}/bulk-insert", json={"documents": [{"x": 1}, {"x": 1}]})
    resp = client.patch(f"/databases/{TEST_DB}/collections/{coll}/update-many", json={"filter": {"x": 1}, "update": {"$set": {"y": 2}}})
    assert resp.status_code == 200
    assert resp.json()["modified_count"] == 2

def test_16_find_one_and_update():
    coll = "c_f1_up"
    client.post(f"/databases/{TEST_DB}/collections/{coll}/documents", json={"data": {"x": 10}})
    resp = client.post(f"/databases/{TEST_DB}/collections/{coll}/find-one-and-update", json={"filter": {"x": 10}, "update": {"$set": {"x": 20}}})
    assert resp.status_code == 200
    assert resp.json()["x"] == 20

def test_17_find_one_and_delete():
    coll = "c_f1_del"
    client.post(f"/databases/{TEST_DB}/collections/{coll}/documents", json={"data": {"x": 100}})
    resp = client.post(f"/databases/{TEST_DB}/collections/{coll}/find-one-and-delete", json={"x": 100})
    assert resp.status_code == 200
    assert resp.json()["x"] == 100

def test_18_replace_document():
    coll = "c_replace"
    r = client.post(f"/databases/{TEST_DB}/collections/{coll}/documents", json={"data": {"a": 1}})
    doc_id = r.json()["id"]
    resp = client.post(f"/databases/{TEST_DB}/collections/{coll}/replace", params={"doc_id": doc_id}, json={"data": {"b": 2}})
    assert resp.status_code == 200
    assert resp.json()["success"] is True

def test_19_find_one():
    coll = "c_f1"
    client.post(f"/databases/{TEST_DB}/collections/{coll}/documents", json={"data": {"name": "target"}})
    resp = client.post(f"/databases/{TEST_DB}/collections/{coll}/find-one", json={"name": "target"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "target"

def test_20_find_many():
    coll = "c_fm"
    client.post(f"/databases/{TEST_DB}/collections/{coll}/bulk-insert", json={"documents": [{"tag": "a"}, {"tag": "a"}]})
    resp = client.post(f"/databases/{TEST_DB}/collections/{coll}/find-many", json={"tag": "a"})
    assert resp.status_code == 200
    assert len(resp.json()) == 2

def test_21_query_documents():
    coll = "c_query"
    client.post(f"/databases/{TEST_DB}/collections/{coll}/documents", json={"data": {"q": 1}})
    resp = client.get(f"/databases/{TEST_DB}/collections/{coll}/query", params={"filter": json.dumps({"q": 1})})
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1

def test_22_aggregate():
    coll = "c_agg"
    client.post(f"/databases/{TEST_DB}/collections/{coll}/documents", json={"data": {"v": 10}})
    resp = client.post(f"/databases/{TEST_DB}/collections/{coll}/aggregate", json={"pipeline": [{"$match": {"v": 10}}]})
    assert resp.status_code == 200
    assert len(resp.json()) == 1

def test_23_distinct():
    coll = "c_dist"
    client.post(f"/databases/{TEST_DB}/collections/{coll}/bulk-insert", json={"documents": [{"d": 1}, {"d": 1}, {"d": 2}]})
    resp = client.get(f"/databases/{TEST_DB}/collections/{coll}/distinct/d")
    assert set(resp.json()) == {1, 2}

def test_24_count_documents():
    coll = "c_count"
    client.post(f"/databases/{TEST_DB}/collections/{coll}/documents", json={"data": {"c": 1}})
    resp = client.get(f"/databases/{TEST_DB}/collections/{coll}/count")
    assert resp.json()["count"] == 1

def test_25_estimated_document_count():
    coll = "c_est_count"
    client.post(f"/databases/{TEST_DB}/collections/{coll}/documents", json={"data": {"e": 1}})
    resp = client.get(f"/databases/{TEST_DB}/collections/{coll}/estimated-count")
    assert resp.json()["count"] >= 0

def test_26_exists():
    coll = "c_exists"
    client.post(f"/databases/{TEST_DB}/collections/{coll}/documents", json={"data": {"ex": True}})
    resp = client.get(f"/databases/{TEST_DB}/collections/{coll}/exists", params={"filter": json.dumps({"ex": True})})
    assert resp.json()["exists"] is True

def test_27_create_index():
    coll = "c_idx"
    resp = client.post(f"/databases/{TEST_DB}/collections/{coll}/indexes", json={"fields": ["idx_f"], "unique": False})
    assert resp.status_code == 200
    assert "index_name" in resp.json()

def test_28_list_indexes():
    coll = "c_idx"
    resp = client.get(f"/databases/{TEST_DB}/collections/{coll}/indexes")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

def test_29_create_ttl_index():
    coll = "c_ttl"
    resp = client.post(f"/databases/{TEST_DB}/collections/{coll}/indexes/ttl", json={"field": "created_at", "expire_seconds": 3600})
    assert resp.status_code == 200

def test_30_drop_index():
    coll = "c_idx_drop"
    r = client.post(f"/databases/{TEST_DB}/collections/{coll}/indexes", json={"fields": ["drop_f"], "unique": False})
    name = r.json()["index_name"]
    resp = client.delete(f"/databases/{TEST_DB}/collections/{coll}/indexes/{name}")
    assert resp.status_code == 200

def test_31_transactional_insert():
    db, coll = f"{TEST_DB}_txn", "t1"
    resp = client.post("/transactions/insert-many", json={"db_name": db, "coll_name": coll, "documents": [{"a": 1}]})
    if resp.status_code == 500 and "replica set" in resp.json()["detail"].lower():
        pytest.skip("Standalone")
    assert resp.status_code == 200

def test_32_transactional_bulk_write():
    db, coll = f"{TEST_DB}_txn", "t2"
    ops = [{"insertOne": {"document": {"b": 1}}}]
    resp = client.post("/transactions/bulk-write", json={"db_name": db, "coll_name": coll, "operations": ops})
    if resp.status_code == 500 and "replica set" in resp.json()["detail"].lower():
        pytest.skip("Standalone")
    assert resp.status_code == 200

def test_33_transactional_update_many():
    db, coll = f"{TEST_DB}_txn", "t3"
    resp = client.post("/transactions/update-many", json={"db_name": db, "coll_name": coll, "filter": {"x": 1}, "update": {"$set": {"y": 2}}})
    if resp.status_code == 500 and "replica set" in resp.json()["detail"].lower():
        pytest.skip("Standalone")
    assert resp.status_code == 200

def test_34_transactional_delete_many():
    db, coll = f"{TEST_DB}_txn", "t4"
    resp = client.post("/transactions/delete-many", json={"db_name": db, "coll_name": coll, "filter": {"x": 1}})
    if resp.status_code == 500 and "replica set" in resp.json()["detail"].lower():
        pytest.skip("Standalone")
    assert resp.status_code == 200

def test_35_transactional_find_and_modify():
    db, coll = f"{TEST_DB}_txn", "t5"
    resp = client.post("/transactions/find-and-modify", json={"db_name": db, "coll_name": coll, "filter": {"x": 1}, "update": {"$set": {"y": 2}}, "upsert": True})
    if resp.status_code == 500 and "replica set" in resp.json()["detail"].lower():
        pytest.skip("Standalone")
    assert resp.status_code == 200

def test_36_one_to_one():
    parent_id = client.post(f"/databases/{TEST_DB}/collections/p1/documents", json={"data": {"name": "P1"}}).json()["id"]
    client.post(f"/databases/{TEST_DB}/collections/c1/documents", json={"data": {"p_id": parent_id, "v": 100}})
    resp = client.post("/relationships/one-to-one", params={"db_name": TEST_DB, "parent_coll": "p1", "child_coll": "c1"}, json={"parent_id": parent_id, "foreign_key": "p_id"})
    assert resp.status_code == 200
    assert resp.json()["relation"]["v"] == 100

def test_37_one_to_many():
    parent_id = client.post(f"/databases/{TEST_DB}/collections/p2/documents", json={"data": {"name": "P2"}}).json()["id"]
    client.post(f"/databases/{TEST_DB}/collections/c2/documents", json={"data": {"p_id": parent_id, "v": 1}})
    client.post(f"/databases/{TEST_DB}/collections/c2/documents", json={"data": {"p_id": parent_id, "v": 2}})
    resp = client.post("/relationships/one-to-many", params={"db_name": TEST_DB, "parent_coll": "p2", "child_coll": "c2"}, json={"parent_id": parent_id, "foreign_key": "p_id"})
    assert resp.status_code == 200
    assert len(resp.json()["relations"]) == 2

def test_38_many_to_many():
    l_id = client.post(f"/databases/{TEST_DB}/collections/l/documents", json={"data": {"name": "L1"}}).json()["id"]
    r_id = client.post(f"/databases/{TEST_DB}/collections/r/documents", json={"data": {"name": "R1"}}).json()["id"]
    client.post(f"/databases/{TEST_DB}/collections/j/documents", json={"data": {"lk": l_id, "rk": r_id}})
    resp = client.post("/relationships/many-to-many", params={"db_name": TEST_DB, "left_coll": "l", "right_coll": "r", "junction_coll": "j"}, json={"left_id": l_id, "left_key": "lk", "right_key": "rk"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1

def test_39_has_one_through():
    p_id = client.post(f"/databases/{TEST_DB}/collections/hp/documents", json={"data": {"name": "HP"}}).json()["id"]
    t_id = client.post(f"/databases/{TEST_DB}/collections/ht/documents", json={"data": {"name": "HT"}}).json()["id"]
    client.post(f"/databases/{TEST_DB}/collections/hth/documents", json={"data": {"pk": p_id, "tk": t_id}})
    resp = client.post("/relationships/has-one-through", params={"db_name": TEST_DB, "parent_coll": "hp", "through_coll": "hth", "target_coll": "ht"}, json={"parent_id": p_id, "through_parent_key": "pk", "through_target_key": "tk"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "HT"

def test_40_has_many_through():
    p_id = client.post(f"/databases/{TEST_DB}/collections/hmp/documents", json={"data": {"name": "HMP"}}).json()["id"]
    t_id = client.post(f"/databases/{TEST_DB}/collections/hmt/documents", json={"data": {"name": "HMT"}}).json()["id"]
    client.post(f"/databases/{TEST_DB}/collections/hmth/documents", json={"data": {"pk": p_id, "tk": t_id}})
    resp = client.post("/relationships/has-many-through", params={"db_name": TEST_DB, "parent_coll": "hmp", "through_coll": "hmth", "target_coll": "hmt"}, json={"parent_id": p_id, "through_parent_key": "pk", "through_target_key": "tk"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1

def test_41_one_to_one_polymorphic():
    target_id = client.post(f"/databases/{TEST_DB}/collections/poly1/documents", json={"data": {"v": 99}}).json()["id"]
    o_id = client.post(f"/databases/{TEST_DB}/collections/owners1/documents", json={"data": {"t": "poly1", "tid": target_id}}).json()["id"]
    resp = client.post("/relationships/polymorphic-one-to-one", params={"db_name": TEST_DB, "owner_coll": "owners1", "related_colls": ["poly1"]}, json={"owner_id": o_id, "type_field": "t", "id_field": "tid"})
    assert resp.status_code == 200
    assert resp.json()["relation"]["v"] == 99

def test_42_one_to_many_polymorphic():
    o_id = client.post(f"/databases/{TEST_DB}/collections/owners2/documents", json={"data": {"name": "O2"}}).json()["id"]
    client.post(f"/databases/{TEST_DB}/collections/poly2/documents", json={"data": {"oid": o_id, "v": 1}})
    resp = client.post("/relationships/polymorphic-one-to-many", params={"db_name": TEST_DB, "owner_coll": "owners2", "related_colls": ["poly2"]}, json={"owner_id": o_id, "type_field": "unused", "foreign_key": "oid"})
    assert resp.status_code == 200
    assert len(resp.json()["relations"]) == 1

def test_43_many_to_many_polymorphic():
    l_id = client.post(f"/databases/{TEST_DB}/collections/l_poly/documents", json={"data": {"n": "L"}}).json()["id"]
    r_id = client.post(f"/databases/{TEST_DB}/collections/r_poly/documents", json={"data": {"n": "R"}}).json()["id"]
    client.post(f"/databases/{TEST_DB}/collections/j_poly/documents", json={"data": {"lk": l_id, "rk": r_id, "rt": "r_poly"}})
    resp = client.post("/relationships/polymorphic-many-to-many", params={"db_name": TEST_DB, "junction_coll": "j_poly", "related_colls": ["r_poly"]}, json={"left_id": l_id, "left_key": "lk", "type_field": "rt", "right_key": "rk"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1

def test_44_drop_database():
    db = f"{TEST_DB}_drop"
    client.post(f"/databases/{db}/collections/c/documents", json={"data": {"a": 1}})
    resp = client.delete(f"/databases/{db}")
    assert resp.status_code == 200
    assert db not in client.get("/databases").json()

def test_45_cleanup():
    client.delete(f"/databases/{TEST_DB}")
    client.delete(f"/databases/{TEST_DB}_txn")

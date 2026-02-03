import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING
from pymongo.database import Database
from pymongo.collection import Collection

from infrastructure.observability.scripts.observability_client import ObservabilityClient, trace_with_details
from ..config.credentials import MongoDBConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

obs = ObservabilityClient(service_name="endpoint-repository")
tracer = obs.tracer


class EndpointRepository:
    def __init__(self):
        logger.info("event=endpoint_repository_init uri=%s database=%s", MongoDBConfig.URI, MongoDBConfig.DATABASE)
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None
        self._collection: Optional[Collection] = None

    def _get_collection(self) -> Collection:
        if self._collection is None:
            logger.info("event=endpoint_repository_connect")
            self._client = MongoClient(MongoDBConfig.URI)
            self._db = self._client[MongoDBConfig.DATABASE]
            self._collection = self._db[MongoDBConfig.ENDPOINTS_COLLECTION]
            self._ensure_indexes()
            logger.info("event=endpoint_repository_connected collection=%s", MongoDBConfig.ENDPOINTS_COLLECTION)
        return self._collection

    def _ensure_indexes(self) -> None:
        logger.info("event=endpoint_repository_ensure_indexes")
        self._collection.create_index([("name", ASCENDING)], unique=True)
        self._collection.create_index([("endpoint_path", ASCENDING)], unique=True)
        self._collection.create_index([("model_id", ASCENDING)])
        self._collection.create_index([("is_active", ASCENDING)])
        logger.info("event=endpoint_repository_indexes_created")

    @trace_with_details(tracer)
    def create_endpoint(self, endpoint_data: Dict[str, Any]) -> str:
        logger.info("event=create_endpoint name=%s path=%s", endpoint_data.get("name"), endpoint_data.get("endpoint_path"))
        collection = self._get_collection()
        now = datetime.now(timezone.utc)
        endpoint_data["created_at"] = now
        endpoint_data["updated_at"] = now
        result = collection.insert_one(endpoint_data)
        endpoint_id = str(result.inserted_id)
        logger.info("event=create_endpoint_complete id=%s", endpoint_id)
        obs.increment_counter("endpoint_repository.create", 1, {"status": "success"})
        return endpoint_id

    @trace_with_details(tracer)
    def get_endpoint_by_id(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        logger.info("event=get_endpoint_by_id id=%s", endpoint_id)
        collection = self._get_collection()
        from bson.objectid import ObjectId
        try:
            doc = collection.find_one({"_id": ObjectId(endpoint_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
                logger.info("event=get_endpoint_by_id_found id=%s", endpoint_id)
                return doc
            logger.info("event=get_endpoint_by_id_not_found id=%s", endpoint_id)
            return None
        except Exception as e:
            logger.error("event=get_endpoint_by_id_error id=%s error=%s", endpoint_id, str(e))
            obs.log_error(f"get_endpoint_by_id failed: {e}")
            raise

    @trace_with_details(tracer)
    def get_endpoint_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        logger.info("event=get_endpoint_by_path path=%s", path)
        collection = self._get_collection()
        doc = collection.find_one({"endpoint_path": path})
        if doc:
            doc["_id"] = str(doc["_id"])
            logger.info("event=get_endpoint_by_path_found path=%s", path)
            return doc
        logger.info("event=get_endpoint_by_path_not_found path=%s", path)
        return None

    @trace_with_details(tracer)
    def get_endpoint_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        logger.info("event=get_endpoint_by_name name=%s", name)
        collection = self._get_collection()
        doc = collection.find_one({"name": name})
        if doc:
            doc["_id"] = str(doc["_id"])
            logger.info("event=get_endpoint_by_name_found name=%s", name)
            return doc
        logger.info("event=get_endpoint_by_name_not_found name=%s", name)
        return None

    @trace_with_details(tracer)
    def list_endpoints(self, filter_query: Optional[Dict[str, Any]] = None, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        logger.info("event=list_endpoints page=%d limit=%d filter=%s", page, limit, filter_query)
        collection = self._get_collection()
        filter_query = filter_query or {}
        skip = (page - 1) * limit
        cursor = collection.find(filter_query).skip(skip).limit(limit)
        items = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            items.append(doc)
        total_count = collection.count_documents(filter_query)
        total_pages = (total_count + limit - 1) // limit if limit > 0 else 0
        logger.info("event=list_endpoints_complete count=%d total=%d", len(items), total_count)
        return {
            "items": items,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }

    @trace_with_details(tracer)
    def update_endpoint(self, endpoint_id: str, update_data: Dict[str, Any]) -> bool:
        logger.info("event=update_endpoint id=%s fields=%s", endpoint_id, list(update_data.keys()))
        collection = self._get_collection()
        from bson.objectid import ObjectId
        update_data["updated_at"] = datetime.now(timezone.utc)
        result = collection.update_one(
            {"_id": ObjectId(endpoint_id)},
            {"$set": update_data}
        )
        success = result.modified_count > 0
        logger.info("event=update_endpoint_complete id=%s success=%s", endpoint_id, success)
        obs.increment_counter("endpoint_repository.update", 1, {"status": "success" if success else "not_found"})
        return success

    @trace_with_details(tracer)
    def delete_endpoint(self, endpoint_id: str) -> bool:
        logger.info("event=delete_endpoint id=%s", endpoint_id)
        collection = self._get_collection()
        from bson.objectid import ObjectId
        result = collection.delete_one({"_id": ObjectId(endpoint_id)})
        success = result.deleted_count > 0
        logger.info("event=delete_endpoint_complete id=%s success=%s", endpoint_id, success)
        obs.increment_counter("endpoint_repository.delete", 1, {"status": "success" if success else "not_found"})
        return success

    @trace_with_details(tracer)
    def get_active_endpoints(self) -> List[Dict[str, Any]]:
        logger.info("event=get_active_endpoints")
        return self.list_endpoints(filter_query={"is_active": True}, page=1, limit=1000)["items"]

    @trace_with_details(tracer)
    def get_endpoints_by_model(self, model_id: str) -> List[Dict[str, Any]]:
        logger.info("event=get_endpoints_by_model model_id=%s", model_id)
        return self.list_endpoints(filter_query={"model_id": model_id}, page=1, limit=1000)["items"]

    def close(self) -> None:
        if self._client:
            logger.info("event=endpoint_repository_close")
            self._client.close()
            self._client = None
            self._db = None
            self._collection = None


endpoint_repository = EndpointRepository()

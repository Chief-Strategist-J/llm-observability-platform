import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from services.shared.cloudflare_catalog import build_cloudflare_virtual_records


class ModelRegistryRepository:
    """Model metadata source supporting filesystem and MongoDB backends."""

    def __init__(self):
        self.backend = os.getenv("MODEL_REGISTRY_BACKEND", "filesystem").strip().lower()
        self._mongo_collection = None

        if self.backend == "mongodb":
            self._mongo_collection = self._init_mongo_collection()

    def _init_mongo_collection(self):
        try:
            from pymongo import MongoClient
        except Exception as exc:  # pragma: no cover - import guarded for optional dependency
            raise RuntimeError("pymongo is required when MODEL_REGISTRY_BACKEND=mongodb") from exc

        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        database = os.getenv("MONGODB_DB", "llm_observability")
        collection_name = os.getenv("MONGODB_MODEL_COLLECTION", "model_configs")

        client = MongoClient(uri)
        collection = client[database][collection_name]
        collection.create_index([("key", 1)], unique=True)
        collection.create_index([("provider", 1), ("name", 1)])
        return collection

    @staticmethod
    def _project_root() -> Path:
        return Path(__file__).resolve().parents[2]

    @staticmethod
    def _normalize_record(config: Dict[str, Any], key: str, source: str = "filesystem") -> Dict[str, Any]:
        model = config.get("model", {}) if isinstance(config, dict) else {}
        return {
            "key": key,
            "source": source,
            "provider": model.get("provider"),
            "id": model.get("id"),
            "name": model.get("name"),
            "config": config,
        }


    @staticmethod
    def _dedupe(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: set[tuple[str, str]] = set()
        deduped: List[Dict[str, Any]] = []
        for record in records:
            identity = (str(record.get("provider") or ""), str(record.get("id") or ""))
            if identity in seen:
                continue
            seen.add(identity)
            deduped.append(record)
        return deduped

    def get_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        key = (key or "").strip()
        if not key:
            return None

        if self.backend == "mongodb":
            doc = self._mongo_collection.find_one({"key": key}, {"_id": 0})
            return doc

        for record in build_cloudflare_virtual_records():
            if record.get("key") == key:
                return record

        path = self._project_root() / key
        if not path.exists() or path.suffix.lower() not in {".yaml", ".yml"}:
            return None
        with open(path, "r") as f:
            config = yaml.safe_load(f) or {}
        return self._normalize_record(config=config, key=key)

    def list_models(self, provider: Optional[str] = None, limit: int = 100, offset: int = 0) -> Tuple[int, List[Dict[str, Any]]]:
        limit = max(1, min(int(limit), 1000))
        offset = max(0, int(offset))

        if self.backend == "mongodb":
            query = {}
            if provider:
                query["provider"] = provider
            total = self._mongo_collection.count_documents(query)
            docs = list(
                self._mongo_collection.find(query, {"_id": 0})
                .sort("name", 1)
                .skip(offset)
                .limit(limit)
            )
            return total, docs

        base = self._project_root() / "configs" / "models"
        records: List[Dict[str, Any]] = []
        for yaml_path in sorted(base.rglob("*.yaml")):
            rel_key = str(yaml_path.relative_to(self._project_root()))
            with open(yaml_path, "r") as f:
                config = yaml.safe_load(f) or {}
            record = self._normalize_record(config=config, key=rel_key)
            if not record.get("provider") or not record.get("id"):
                continue
            if provider and record.get("provider") != provider:
                continue
            records.append(record)

        records.extend(build_cloudflare_virtual_records())
        if provider:
            records = [r for r in records if r.get("provider") == provider]

        records = self._dedupe(records)
        total = len(records)
        return total, records[offset: offset + limit]

    def upsert_many(self, records: List[Dict[str, Any]]) -> int:
        if self.backend != "mongodb":
            raise RuntimeError("upsert_many is only supported for mongodb backend")

        from pymongo import UpdateOne

        operations = []
        for record in records:
            key = record.get("key")
            if not key:
                continue
            normalized = {
                "key": key,
                "source": record.get("source", "filesystem"),
                "provider": record.get("provider"),
                "id": record.get("id"),
                "name": record.get("name"),
                "config": record.get("config", {}),
            }
            operations.append(UpdateOne({"key": key}, {"$set": normalized}, upsert=True))

        if not operations:
            return 0

        result = self._mongo_collection.bulk_write(operations)
        return result.upserted_count + result.modified_count

    def build_records_from_filesystem(self, root: str = "configs/models") -> List[Dict[str, Any]]:
        records = []
        base = self._project_root() / root
        for yaml_path in sorted(base.rglob("*.yaml")):
            with open(yaml_path, "r") as f:
                config = yaml.safe_load(f) or {}
            rel_key = str(yaml_path.relative_to(self._project_root()))
            record = self._normalize_record(config=config, key=rel_key, source="filesystem")
            if not record.get("provider") or not record.get("id"):
                continue
            records.append(record)
        records.extend(build_cloudflare_virtual_records())
        return self._dedupe(records)


model_registry = ModelRegistryRepository()

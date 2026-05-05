from typing import Any, Dict, List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne, ASCENDING
from domain.ports.database_port import DatabasePort, EventRecord, ConsumerOffset


class AsyncMongoDatabaseAdapter(DatabasePort):
    def __init__(self, uri: str, database_name: str = "kafka_events"):
        self._uri = uri
        self._database_name = database_name
        self._client = None
        self._db = None
        self._events_collection = None
        self._offsets_collection = None

    async def initialize(self):
        self._client = AsyncIOMotorClient(
            self._uri,
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000,
        )
        self._db = self._client[self._database_name]
        self._events_collection = self._db["kafka_events"]
        self._offsets_collection = self._db["consumer_offsets"]
        await self._ensure_indexes()

    async def _ensure_indexes(self):
        await self._events_collection.create_index([(("topic", ASCENDING))])
        await self._events_collection.create_index([(("processed", ASCENDING))])
        await self._events_collection.create_index(
            [("topic", ASCENDING), ("partition", ASCENDING), ("offset", ASCENDING)], unique=True
        )
        await self._offsets_collection.create_index([(("consumer_group", ASCENDING))])
        await self._offsets_collection.create_index(
            [("consumer_group", ASCENDING), ("topic", ASCENDING), ("partition", ASCENDING)], unique=True
        )

    async def save_event(self, event: EventRecord) -> str:
        doc = self._event_to_dict(event)
        result = await self._events_collection.update_one(
            {"topic": event.topic, "partition": event.partition, "offset": event.offset},
            {"$set": doc},
            upsert=True
        )
        if result.upserted_id:
            return str(result.upserted_id)
        existing = await self._events_collection.find_one(
            {"topic": event.topic, "partition": event.partition, "offset": event.offset},
            {"_id": 1}
        )
        return str(existing["_id"]) if existing else ""

    async def save_events_batch(self, events: List[EventRecord]) -> List[str]:
        if not events:
            return []
        ops = [
            UpdateOne(
                {"topic": e.topic, "partition": e.partition, "offset": e.offset},
                {"$set": self._event_to_dict(e)},
                upsert=True
            )
            for e in events
        ]
        await self._events_collection.bulk_write(ops, ordered=False)
        return [f"batch-{i}" for i in range(len(events))]

    async def get_event(self, event_id: str) -> Optional[EventRecord]:
        from bson.objectid import ObjectId
        try:
            doc = await self._events_collection.find_one({"_id": ObjectId(event_id)})
        except Exception:
            doc = await self._events_collection.find_one({"_id": event_id})
        return self._dict_to_event(doc) if doc else None

    async def get_events_by_topic(self, topic: str, limit: int = 100, offset: int = 0) -> List[EventRecord]:
        cursor = self._events_collection.find({"topic": topic}).sort("created_at", -1).skip(offset).limit(limit)
        return [self._dict_to_event(doc) for doc in await cursor.to_list(length=limit)]

    async def get_unprocessed_events(self, limit: int = 100) -> List[EventRecord]:
        cursor = self._events_collection.find({"processed": False}).sort("created_at", 1).limit(limit)
        return [self._dict_to_event(doc) for doc in await cursor.to_list(length=limit)]

    async def mark_event_processed(self, event_id: str, error: Optional[str] = None) -> bool:
        from bson.objectid import ObjectId
        update_data = {"processed": True, "error": error}
        try:
            result = await self._events_collection.update_one({"_id": ObjectId(event_id)}, {"$set": update_data})
        except Exception:
            result = await self._events_collection.update_one({"_id": event_id}, {"$set": update_data})
        return result.modified_count > 0

    async def save_consumer_offset(self, offset: ConsumerOffset) -> bool:
        doc = {
            "consumer_group": offset.consumer_group, "topic": offset.topic,
            "partition": offset.partition, "offset": offset.offset, "updated_at": offset.updated_at
        }
        result = await self._offsets_collection.update_one(
            {"consumer_group": offset.consumer_group, "topic": offset.topic, "partition": offset.partition},
            {"$set": doc}, upsert=True
        )
        return result.acknowledged

    async def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> Optional[ConsumerOffset]:
        doc = await self._offsets_collection.find_one(
            {"consumer_group": consumer_group, "topic": topic, "partition": partition}
        )
        if doc:
            return ConsumerOffset(
                consumer_group=doc["consumer_group"], topic=doc["topic"],
                partition=doc["partition"], offset=doc["offset"], updated_at=doc["updated_at"]
            )
        return None

    async def delete_events_by_topic(self, topic: str) -> int:
        result = await self._events_collection.delete_many({"topic": topic})
        return result.deleted_count

    async def get_event_count(self, topic: Optional[str] = None) -> int:
        if topic:
            return await self._events_collection.count_documents({"topic": topic})
        return await self._events_collection.estimated_document_count()

    async def close(self) -> None:
        if self._client:
            self._client.close()

    def _event_to_dict(self, event: EventRecord) -> Dict[str, Any]:
        return {
            "topic": event.topic, "partition": event.partition, "offset": event.offset,
            "key": event.key, "value": event.value, "timestamp": event.timestamp,
            "headers": event.headers, "processed": event.processed,
            "error": event.error, "created_at": event.created_at
        }

    def _dict_to_event(self, doc: Dict[str, Any]) -> EventRecord:
        return EventRecord(
            topic=doc["topic"], partition=doc["partition"], offset=doc["offset"],
            key=doc.get("key"), value=doc.get("value"), timestamp=doc["timestamp"],
            headers=doc.get("headers"), processed=doc.get("processed", False),
            error=doc.get("error"), created_at=doc.get("created_at")
        )

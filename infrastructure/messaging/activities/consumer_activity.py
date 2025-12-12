import sys
import time
from pathlib import Path
from typing import Dict, List
from temporalio import activity

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.logql_logger import LogQLLogger
from infrastructure.orchestrator.kafka.clients.kafka_consumer_client import (
    KafkaConsumerClient,
    ConsumerConfig
)
from infrastructure.orchestrator.kafka.utils.serializers import StringDeserializer, JSONDeserializer
from kafka.structs import TopicPartition, OffsetAndMetadata


_consumer_instances: Dict[str, KafkaConsumerClient] = {}
logger = LogQLLogger(__name__)


def _get_or_create_consumer(bootstrap_servers: List[str], group_id: str, client_id: str, **kwargs) -> KafkaConsumerClient:
    key = f"{','.join(bootstrap_servers)}:{group_id}:{client_id}"
    
    if key not in _consumer_instances:
        logger.info("consumer_create_new", group_id=group_id, client_id=client_id)
        
        config = ConsumerConfig(
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            client_id=client_id,
            **kwargs
        )
        _consumer_instances[key] = KafkaConsumerClient(config)
    
    return _consumer_instances[key]


@activity.defn(name="poll_messages_activity")
async def poll_messages_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    start_time = time.time()
    
    logger.info(
        "activity_start",
        activity="poll_messages",
        group_id=params.get("group_id"),
        trace_id=trace_id
    )
    
    try:
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        group_id = params["group_id"]
        topics = params["topics"]
        client_id = params.get("client_id", "kafka-consumer")
        timeout_ms = params.get("timeout_ms", 1000)
        max_records = params.get("max_records", 500)
        
        value_deserializer_type = params.get("value_deserializer", "string")
        key_deserializer_type = params.get("key_deserializer", "string")
        
        value_deserializer = JSONDeserializer() if value_deserializer_type == "json" else StringDeserializer()
        key_deserializer = JSONDeserializer() if key_deserializer_type == "json" else StringDeserializer()
        
        consumer = _get_or_create_consumer(
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            client_id=client_id,
            value_deserializer=value_deserializer,
            key_deserializer=key_deserializer,
            enable_auto_commit=params.get("enable_auto_commit", True),
            auto_offset_reset=params.get("auto_offset_reset", "latest")
        )
        
        if not consumer.subscription():
            consumer.subscribe(topics)
        
        records = consumer.poll(timeout_ms=timeout_ms, max_records=max_records)
        
        messages = []
        for record in records:
            messages.append({
                "topic": record.topic,
                "partition": record.partition,
                "offset": record.offset,
                "timestamp": record.timestamp,
                "key": record.key,
                "value": record.value,
                "headers": record.headers
            })
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "activity_complete",
            activity="poll_messages",
            messages_count=len(messages),
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        
        return {
            "success": True,
            "messages_count": len(messages),
            "messages": messages
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "activity_failed",
            activity="poll_messages",
            error=e,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn(name="commit_offsets_activity")
async def commit_offsets_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    start_time = time.time()
    
    logger.info("activity_start", activity="commit_offsets", trace_id=trace_id)
    
    try:
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        group_id = params["group_id"]
        client_id = params.get("client_id", "kafka-consumer")
        offsets = params.get("offsets")
        
        key = f"{','.join(bootstrap_servers)}:{group_id}:{client_id}"
        
        if key not in _consumer_instances:
            return {
                "success": False,
                "error": "Consumer not found"
            }
        
        consumer = _consumer_instances[key]
        
        if offsets:
            offset_dict = {}
            for offset_info in offsets:
                tp = TopicPartition(offset_info["topic"], offset_info["partition"])
                offset_dict[tp] = OffsetAndMetadata(offset_info["offset"], None)
            consumer.commit(offsets=offset_dict)
        else:
            consumer.commit()
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "activity_complete",
            activity="commit_offsets",
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        
        return {
            "success": True,
            "committed": True
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "activity_failed",
            activity="commit_offsets",
            error=e,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn(name="seek_offset_activity")
async def seek_offset_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    
    logger.info("activity_start", activity="seek_offset", trace_id=trace_id)
    
    try:
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        group_id = params["group_id"]
        client_id = params.get("client_id", "kafka-consumer")
        topic = params["topic"]
        partition = params["partition"]
        offset = params.get("offset")
        seek_to = params.get("seek_to", "offset")
        
        key = f"{','.join(bootstrap_servers)}:{group_id}:{client_id}"
        
        if key not in _consumer_instances:
            return {
                "success": False,
                "error": "Consumer not found"
            }
        
        consumer = _consumer_instances[key]
        tp = TopicPartition(topic, partition)
        
        if seek_to == "beginning":
            consumer.seek_to_beginning(tp)
        elif seek_to == "end":
            consumer.seek_to_end(tp)
        else:
            consumer.seek(tp, offset)
        
        logger.info(
            "activity_complete",
            activity="seek_offset",
            topic=topic,
            partition=partition,
            seek_to=seek_to,
            trace_id=trace_id
        )
        
        return {
            "success": True,
            "topic": topic,
            "partition": partition,
            "seek_to": seek_to
        }
        
    except Exception as e:
        logger.error("activity_failed", activity="seek_offset", error=e, trace_id=trace_id)
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn(name="close_consumer_activity")
async def close_consumer_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    
    logger.info("activity_start", activity="close_consumer", trace_id=trace_id)
    
    try:
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        group_id = params["group_id"]
        client_id = params.get("client_id", "kafka-consumer")
        autocommit = params.get("autocommit", True)
        
        key = f"{','.join(bootstrap_servers)}:{group_id}:{client_id}"
        
        if key in _consumer_instances:
            consumer = _consumer_instances.pop(key)
            consumer.close(autocommit=autocommit)
            
            logger.info("activity_complete", activity="close_consumer", trace_id=trace_id)
            
            return {
                "success": True,
                "closed": True
            }
        else:
            return {
                "success": True,
                "closed": False,
                "message": "No consumer instance found"
            }
        
    except Exception as e:
        logger.error("activity_failed", activity="close_consumer", error=e, trace_id=trace_id)
        return {
            "success": False,
            "error": str(e)
        }

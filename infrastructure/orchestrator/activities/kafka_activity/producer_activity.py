import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from temporalio import activity

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.logql_logger import LogQLLogger
from infrastructure.orchestrator.kafka.clients.kafka_producer_client import (
    KafkaProducerClient,
    ProducerConfig,
    ProducerRecord
)
from infrastructure.orchestrator.kafka.utils.serializers import StringSerializer, JSONSerializer


_producer_instances: Dict[str, KafkaProducerClient] = {}
logger = LogQLLogger(__name__)


def _get_or_create_producer(bootstrap_servers: List[str], client_id: str, **kwargs) -> KafkaProducerClient:
    key = f"{','.join(bootstrap_servers)}:{client_id}"
    
    if key not in _producer_instances:
        logger.info("producer_create_new", client_id=client_id)
        
        config = ProducerConfig(
            bootstrap_servers=bootstrap_servers,
            client_id=client_id,
            **kwargs
        )
        _producer_instances[key] = KafkaProducerClient(config)
    
    return _producer_instances[key]


@activity.defn(name="send_message_activity")
async def send_message_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    start_time = time.time()
    
    logger.info(
        "activity_start",
        activity="send_message",
        topic=params.get("topic"),
        trace_id=trace_id
    )
    
    try:
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        topic = params["topic"]
        value = params["value"]
        key = params.get("key")
        partition = params.get("partition")
        headers = params.get("headers")
        client_id = params.get("client_id", "kafka-producer")
        
        value_serializer_type = params.get("value_serializer", "string")
        key_serializer_type = params.get("key_serializer", "string")
        
        value_serializer = JSONSerializer() if value_serializer_type == "json" else StringSerializer()
        key_serializer = JSONSerializer() if key_serializer_type == "json" else StringSerializer()
        
        producer = _get_or_create_producer(
            bootstrap_servers=bootstrap_servers,
            client_id=client_id,
            value_serializer=value_serializer,
            key_serializer=key_serializer
        )
        
        record = ProducerRecord(
            topic=topic,
            value=value,
            key=key,
            partition=partition,
            headers=headers
        )
        
        future = producer.send(record)
        metadata = future.get(timeout=30)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "activity_complete",
            activity="send_message",
            topic=topic,
            partition=metadata.partition,
            offset=metadata.offset,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        
        return {
            "success": True,
            "topic": metadata.topic,
            "partition": metadata.partition,
            "offset": metadata.offset,
            "timestamp": metadata.timestamp
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "activity_failed",
            activity="send_message",
            error=e,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn(name="send_batch_activity")
async def send_batch_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    start_time = time.time()
    
    logger.info(
        "activity_start",
        activity="send_batch",
        messages_count=len(params.get("messages", [])),
        trace_id=trace_id
    )
    
    try:
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        messages = params["messages"]
        client_id = params.get("client_id", "kafka-producer-batch")
        
        value_serializer_type = params.get("value_serializer", "string")
        key_serializer_type = params.get("key_serializer", "string")
        
        value_serializer = JSONSerializer() if value_serializer_type == "json" else StringSerializer()
        key_serializer = JSONSerializer() if key_serializer_type == "json" else StringSerializer()
        
        producer = _get_or_create_producer(
            bootstrap_servers=bootstrap_servers,
            client_id=client_id,
            value_serializer=value_serializer,
            key_serializer=key_serializer
        )
        
        futures = []
        for msg in messages:
            record = ProducerRecord(
                topic=msg["topic"],
                value=msg["value"],
                key=msg.get("key"),
                partition=msg.get("partition"),
                headers=msg.get("headers")
            )
            future = producer.send(record)
            futures.append(future)
        
        results = []
        for future in futures:
            try:
                metadata = future.get(timeout=30)
                results.append({
                    "success": True,
                    "topic": metadata.topic,
                    "partition": metadata.partition,
                    "offset": metadata.offset
                })
            except Exception as e:
                results.append({
                    "success": False,
                    "error": str(e)
                })
        
        duration_ms = int((time.time() - start_time) * 1000)
        successful = sum(1 for r in results if r["success"])
        
        logger.info(
            "activity_complete",
            activity="send_batch",
            total_messages=len(messages),
            successful=successful,
            failed=len(messages) - successful,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        
        return {
            "success": True,
            "total": len(messages),
            "successful": successful,
            "failed": len(messages) - successful,
            "results": results
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "activity_failed",
            activity="send_batch",
            error=e,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn(name="flush_producer_activity")
async def flush_producer_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    start_time = time.time()
    
    logger.info("activity_start", activity="flush_producer", trace_id=trace_id)
    
    try:
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        client_id = params.get("client_id", "kafka-producer")
        timeout = params.get("timeout", 30)
        
        key = f"{','.join(bootstrap_servers)}:{client_id}"
        
        if key in _producer_instances:
            producer = _producer_instances[key]
            producer.flush(timeout=timeout)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                "activity_complete",
                activity="flush_producer",
                duration_ms=duration_ms,
                trace_id=trace_id
            )
            
            return {
                "success": True,
                "flushed": True
            }
        else:
            logger.warning("activity_warning", activity="flush_producer", message="No producer found")
            return {
                "success": True,
                "flushed": False,
                "message": "No producer instance found"
            }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "activity_failed",
            activity="flush_producer",
            error=e,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn(name="close_producer_activity")
async def close_producer_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    
    logger.info("activity_start", activity="close_producer", trace_id=trace_id)
    
    try:
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        client_id = params.get("client_id", "kafka-producer")
        timeout = params.get("timeout", 30)
        
        key = f"{','.join(bootstrap_servers)}:{client_id}"
        
        if key in _producer_instances:
            producer = _producer_instances.pop(key)
            producer.close(timeout=timeout)
            
            logger.info("activity_complete", activity="close_producer", trace_id=trace_id)
            
            return {
                "success": True,
                "closed": True
            }
        else:
            return {
                "success": True,
                "closed": False,
                "message": "No producer instance found"
            }
        
    except Exception as e:
        logger.error("activity_failed", activity="close_producer", error=e, trace_id=trace_id)
        return {
            "success": False,
            "error": str(e)
        }

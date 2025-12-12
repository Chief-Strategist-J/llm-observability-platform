import sys
import time
from pathlib import Path
from temporalio import activity

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.logql_logger import LogQLLogger
from infrastructure.orchestrator.kafka.clients.kafka_transaction_client import (
    KafkaTransactionClient,
    TransactionalConfig,
    TransactionState
)
from infrastructure.orchestrator.kafka.clients.kafka_producer_client import (
    ProducerConfig,
    ProducerRecord
)


logger = LogQLLogger(__name__)
_transaction_clients = {}


@activity.defn(name="begin_transaction_activity")
async def begin_transaction_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    start_time = time.time()
    
    logger.info(
        "activity_start",
        activity="begin_transaction",
        transactional_id=params.get("transactional_id"),
        trace_id=trace_id
    )
    
    try:
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        transactional_id = params["transactional_id"]
        timeout_ms = params.get("timeout_ms", 60000)
        
        if transactional_id not in _transaction_clients:
            producer_config = ProducerConfig(
                bootstrap_servers=bootstrap_servers,
                transactional_id=transactional_id
            )
            
            txn_config = TransactionalConfig(
                transactional_id=transactional_id,
                transaction_timeout_ms=timeout_ms,
                producer_config=producer_config
            )
            
            _transaction_clients[transactional_id] = KafkaTransactionClient(txn_config)
        
        client = _transaction_clients[transactional_id]
        client.begin_transaction()
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "activity_complete",
            activity="begin_transaction",
            transactional_id=transactional_id,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        
        return {
            "success": True,
            "transactional_id": transactional_id,
            "state": client.state.value
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "activity_failed",
            activity="begin_transaction",
            error=e,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn(name="send_transactional_message_activity")
async def send_transactional_message_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    start_time = time.time()
    
    logger.info(
        "activity_start",
        activity="send_transactional_message",
        transactional_id=params.get("transactional_id"),
        topic=params.get("topic"),
        trace_id=trace_id
    )
    
    try:
        transactional_id = params["transactional_id"]
        topic = params["topic"]
        value = params["value"]
        key = params.get("key")
        partition = params.get("partition")
        headers = params.get("headers")
        
        if transactional_id not in _transaction_clients:
            return {
                "success": False,
                "error": "Transaction not initialized"
            }
        
        client = _transaction_clients[transactional_id]
        
        record = ProducerRecord(
            topic=topic,
            value=value,
            key=key,
            partition=partition,
            headers=headers
        )
        
        future = client.send(record)
        metadata = future.get(timeout=30)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "activity_complete",
            activity="send_transactional_message",
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
            "offset": metadata.offset
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "activity_failed",
            activity="send_transactional_message",
            error=e,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn(name="commit_transaction_activity")
async def commit_transaction_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    start_time = time.time()
    
    logger.info(
        "activity_start",
        activity="commit_transaction",
        transactional_id=params.get("transactional_id"),
        trace_id=trace_id
    )
    
    try:
        transactional_id = params["transactional_id"]
        
        if transactional_id not in _transaction_clients:
            return {
                "success": False,
                "error": "Transaction not found"
            }
        
        client = _transaction_clients[transactional_id]
        client.commit_transaction()
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "activity_complete",
            activity="commit_transaction",
            transactional_id=transactional_id,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        
        return {
            "success": True,
            "transactional_id": transactional_id,
            "state": client.state.value
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "activity_failed",
            activity="commit_transaction",
            error=e,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn(name="abort_transaction_activity")
async def abort_transaction_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    start_time = time.time()
    
    logger.info(
        "activity_start",
        activity="abort_transaction",
        transactional_id=params.get("transactional_id"),
        trace_id=trace_id
    )
    
    try:
        transactional_id = params["transactional_id"]
        
        if transactional_id not in _transaction_clients:
            return {
                "success": False,
                "error": "Transaction not found"
            }
        
        client = _transaction_clients[transactional_id]
        client.abort_transaction()
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "activity_complete",
            activity="abort_transaction",
            transactional_id=transactional_id,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        
        return {
            "success": True,
            "transactional_id": transactional_id,
            "state": client.state.value
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "activity_failed",
            activity="abort_transaction",
            error=e,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn(name="close_transaction_client_activity")
async def close_transaction_client_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    
    logger.info(
        "activity_start",
        activity="close_transaction_client",
        transactional_id=params.get("transactional_id"),
        trace_id=trace_id
    )
    
    try:
        transactional_id = params["transactional_id"]
        
        if transactional_id in _transaction_clients:
            client = _transaction_clients.pop(transactional_id)
            client.close()
            
            logger.info(
                "activity_complete",
                activity="close_transaction_client",
                transactional_id=transactional_id,
                trace_id=trace_id
            )
            
            return {
                "success": True,
                "closed": True
            }
        else:
            return {
                "success": True,
                "closed": False,
                "message": "Transaction client not found"
            }
        
    except Exception as e:
        logger.error(
            "activity_failed",
            activity="close_transaction_client",
            error=e,
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }

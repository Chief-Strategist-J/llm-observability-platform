import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.logql_logger import LogQLLogger
from infrastructure.orchestrator.kafka.clients.kafka_producer_client import (
    KafkaProducerClient, ProducerConfig, ProducerRecord
)


class TransactionState(Enum):
    READY = "ready"
    IN_TRANSACTION = "in_transaction"
    COMMITTING = "committing"
    ABORTING = "aborting"
    ABORTED = "aborted"
    COMMITTED = "committed"


@dataclass
class TransactionalConfig:
    transactional_id: str
    transaction_timeout_ms: int = 60000
    producer_config: Optional[ProducerConfig] = None


class KafkaTransactionClient:
    __slots__ = ('_config', '_producer', '_logger', '_state', '_trace_id', 
                 '_transaction_partitions', '_transaction_start_time')
    
    def __init__(self, config: TransactionalConfig):
        self._config = config
        self._logger = LogQLLogger(__name__)
        self._trace_id = self._logger.set_trace_id()
        self._state = TransactionState.READY
        self._transaction_partitions: set = set()
        self._transaction_start_time: Optional[float] = None
        
        self._logger.info(
            "transaction_client_init_start",
            transactional_id=config.transactional_id,
            timeout_ms=config.transaction_timeout_ms
        )
        
        try:
            producer_config = config.producer_config or ProducerConfig(
                bootstrap_servers=["localhost:9092"],
                transactional_id=config.transactional_id,
                enable_idempotence=True,
                acks="all",
                max_in_flight_requests=1
            )
            
            if not producer_config.transactional_id:
                producer_config.transactional_id = config.transactional_id
            
            producer_config.enable_idempotence = True
            producer_config.acks = "all"
            
            self._producer = KafkaProducerClient(producer_config)
            
            self._init_transactions()
            
            self._logger.info("transaction_client_init_complete")
            
        except Exception as e:
            self._logger.error("transaction_client_init_failed", error=e)
            raise
    
    def _init_transactions(self) -> None:
        self._logger.info("transaction_init_start")
        
        try:
            self._producer._producer.init_transactions()
            self._state = TransactionState.READY
            self._logger.info("transaction_init_complete")
        except Exception as e:
            self._logger.error("transaction_init_error", error=e)
            raise
    
    def begin_transaction(self) -> None:
        if self._state != TransactionState.READY:
            raise RuntimeError(f"Cannot begin transaction in state: {self._state}")
        
        self._logger.info("transaction_begin")
        
        try:
            self._producer._producer.begin_transaction()
            self._state = TransactionState.IN_TRANSACTION
            self._transaction_partitions.clear()
            self._transaction_start_time = time.time()
            
            self._logger.info("transaction_begin_complete")
            
        except Exception as e:
            self._logger.error("transaction_begin_error", error=e)
            raise
    
    def send(self, record: ProducerRecord) -> Any:
        if self._state != TransactionState.IN_TRANSACTION:
            raise RuntimeError(f"Cannot send in state: {self._state}")
        
        start_time = time.time()
        
        try:
            future = self._producer.send(record)
            
            partition_key = (record.topic, record.partition) if record.partition is not None else (record.topic, None)
            self._transaction_partitions.add(partition_key)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            self._logger.debug(
                "transaction_send",
                topic=record.topic,
                partition=record.partition,
                duration_ms=duration_ms
            )
            
            return future
            
        except Exception as e:
            self._logger.error("transaction_send_error", error=e, topic=record.topic)
            raise
    
    def send_offsets_to_transaction(self, offsets: Dict[Any, Any], group_id: str) -> None:
        if self._state != TransactionState.IN_TRANSACTION:
            raise RuntimeError(f"Cannot send offsets in state: {self._state}")
        
        self._logger.info("transaction_send_offsets", group_id=group_id, offsets_count=len(offsets))
        
        try:
            self._producer._producer.send_offsets_to_transaction(
                offsets=offsets,
                consumer_group_metadata=group_id
            )
            
            self._logger.info("transaction_send_offsets_complete", group_id=group_id)
            
        except Exception as e:
            self._logger.error("transaction_send_offsets_error", error=e, group_id=group_id)
            raise
    
    def commit_transaction(self) -> None:
        if self._state != TransactionState.IN_TRANSACTION:
            raise RuntimeError(f"Cannot commit in state: {self._state}")
        
        self._state = TransactionState.COMMITTING
        
        start_time = time.time()
        duration_from_begin = int((time.time() - self._transaction_start_time) * 1000) if self._transaction_start_time else 0
        
        self._logger.info(
            "transaction_commit_start",
            partitions_count=len(self._transaction_partitions),
            transaction_duration_ms=duration_from_begin
        )
        
        try:
            self._producer._producer.commit_transaction()
            
            commit_duration_ms = int((time.time() - start_time) * 1000)
            
            self._state = TransactionState.COMMITTED
            self._state = TransactionState.READY
            
            self._logger.info(
                "transaction_commit_complete",
                commit_duration_ms=commit_duration_ms,
                total_duration_ms=duration_from_begin
            )
            
        except Exception as e:
            self._state = TransactionState.READY
            self._logger.error("transaction_commit_error", error=e)
            raise
    
    def abort_transaction(self) -> None:
        if self._state != TransactionState.IN_TRANSACTION:
            raise RuntimeError(f"Cannot abort in state: {self._state}")
        
        self._state = TransactionState.ABORTING
        
        start_time = time.time()
        duration_from_begin = int((time.time() - self._transaction_start_time) * 1000) if self._transaction_start_time else 0
        
        self._logger.info(
            "transaction_abort_start",
            partitions_count=len(self._transaction_partitions),
            transaction_duration_ms=duration_from_begin
        )
        
        try:
            self._producer._producer.abort_transaction()
            
            abort_duration_ms = int((time.time() - start_time) * 1000)
            
            self._state = TransactionState.ABORTED
            self._state = TransactionState.READY
            
            self._logger.info(
                "transaction_abort_complete",
                abort_duration_ms=abort_duration_ms,
                total_duration_ms=duration_from_begin
            )
            
        except Exception as e:
            self._state = TransactionState.READY
            self._logger.error("transaction_abort_error", error=e)
            raise
    
    def flush(self, timeout: Optional[float] = None) -> None:
        self._producer.flush(timeout=timeout)
    
    def close(self, timeout: Optional[float] = None) -> None:
        self._logger.info("transaction_client_close_start")
        
        try:
            if self._state == TransactionState.IN_TRANSACTION:
                self._logger.warning("transaction_client_close_with_active_transaction")
                self.abort_transaction()
            
            self._producer.close(timeout=timeout)
            self._logger.info("transaction_client_close_complete")
            
        except Exception as e:
            self._logger.error("transaction_client_close_error", error=e)
            raise
    
    @property
    def state(self) -> TransactionState:
        return self._state

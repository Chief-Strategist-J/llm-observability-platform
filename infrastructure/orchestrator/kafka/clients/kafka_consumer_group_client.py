import time
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.logql_logger import LogQLLogger
from infrastructure.orchestrator.kafka.clients.kafka_consumer_client import KafkaConsumerClient, ConsumerConfig


class GroupState(Enum):
    PREPARING_REBALANCE = "preparing_rebalance"
    COMPLETING_REBALANCE = "completing_rebalance"
    STABLE = "stable"
    DEAD = "dead"
    EMPTY = "empty"


@dataclass
class ConsumerGroupMember:
    member_id: str
    client_id: str
    client_host: str
    metadata: Dict[str, Any]
    assignment: Dict[str, Any]


@dataclass
class ConsumerGroupInfo:
    group_id: str
    state: str
    protocol_type: str
    protocol: str
    members: List[ConsumerGroupMember]
    coordinator: Optional[str] = None


class KafkaConsumerGroupClient:
    __slots__ = ('_consumer', '_logger', '_group_id', '_trace_id', '_is_leader',
                 '_generation_id', '_member_id', '_assigned_partitions')
    
    def __init__(self, consumer: KafkaConsumerClient, group_id: str):
        self._consumer = consumer
        self._group_id = group_id
        self._logger = LogQLLogger(__name__)
        self._trace_id = self._logger.set_trace_id()
        
        self._is_leader = False
        self._generation_id: Optional[int] = None
        self._member_id: Optional[str] = None
        self._assigned_partitions: Set = set()
        
        self._logger.info("consumer_group_init", group_id=group_id)
    
    def join_group(self, topics: List[str]) -> Dict[str, Any]:
        self._logger.info("consumer_group_join_start", group_id=self._group_id, topics=','.join(topics))
        
        start_time = time.time()
        
        try:
            self._consumer.subscribe(topics)
            
            self._consumer.poll(timeout_ms=1000, max_records=0)
            
            assignment = self._consumer.assignment()
            self._assigned_partitions = assignment
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            self._logger.info(
                "consumer_group_join_complete",
                group_id=self._group_id,
                partitions_count=len(assignment),
                duration_ms=duration_ms
            )
            
            return {
                "group_id": self._group_id,
                "assignment": [{"topic": tp.topic, "partition": tp.partition} for tp in assignment],
                "generation_id": self._generation_id,
                "member_id": self._member_id
            }
            
        except Exception as e:
            self._logger.error("consumer_group_join_error", error=e, group_id=self._group_id)
            raise
    
    def leave_group(self) -> None:
        self._logger.info("consumer_group_leave_start", group_id=self._group_id)
        
        try:
            self._consumer.close(autocommit=True)
            
            self._assigned_partitions.clear()
            self._generation_id = None
            self._member_id = None
            self._is_leader = False
            
            self._logger.info("consumer_group_leave_complete", group_id=self._group_id)
            
        except Exception as e:
            self._logger.error("consumer_group_leave_error", error=e, group_id=self._group_id)
            raise
    
    def heartbeat(self) -> bool:
        try:
            self._consumer.poll(timeout_ms=0, max_records=0)
            return True
        except Exception as e:
            self._logger.error("consumer_group_heartbeat_error", error=e, group_id=self._group_id)
            return False
    
    def get_assignment(self) -> Set[Any]:
        return self._consumer.assignment()
    
    def sync_group(self) -> Dict[str, Any]:
        self._logger.debug("consumer_group_sync", group_id=self._group_id)
        
        try:
            assignment = self._consumer.assignment()
            
            return {
                "group_id": self._group_id,
                "assignment": [{"topic": tp.topic, "partition": tp.partition} for tp in assignment]
            }
            
        except Exception as e:
            self._logger.error("consumer_group_sync_error", error=e, group_id=self._group_id)
            raise
    
    @property
    def group_id(self) -> str:
        return self._group_id
    
    @property
    def member_id(self) -> Optional[str]:
        return self._member_id
    
    @property
    def generation_id(self) -> Optional[int]:
        return self._generation_id
    
    @property
    def is_leader(self) -> bool:
        return self._is_leader

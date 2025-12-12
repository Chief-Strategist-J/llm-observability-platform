import time
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from kafka.admin import KafkaAdminClient, NewTopic, ConfigResource, ConfigResourceType
from kafka.errors import KafkaError
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.logql_logger import LogQLLogger


@dataclass
class AdminConfig:
    bootstrap_servers: List[str]
    client_id: str = "kafka-admin"
    request_timeout_ms: int = 30000


@dataclass
class TopicConfig:
    name: str
    num_partitions: int = 1
    replication_factor: int = 1
    config: Optional[Dict[str, str]] = None


class KafkaAdminClientWrapper:
    __slots__ = ('_config', '_admin', '_logger', '_closed', '_trace_id')
    
    def __init__(self, config: AdminConfig):
        self._config = config
        self._logger = LogQLLogger(__name__)
        self._trace_id = self._logger.set_trace_id()
        self._closed = False
        
        self._logger.info(
            "admin_init_start",
            bootstrap_servers=','.join(config.bootstrap_servers),
            client_id=config.client_id
        )
        
        try:
            self._admin = KafkaAdminClient(
                bootstrap_servers=config.bootstrap_servers,
                client_id=config.client_id,
                request_timeout_ms=config.request_timeout_ms
            )
            
            self._logger.info("admin_init_complete")
            
        except Exception as e:
            self._logger.error("admin_init_failed", error=e)
            raise
    
    def create_topics(self, topics: List[TopicConfig], validate_only: bool = False) -> Dict[str, Any]:
        if self._closed:
            raise RuntimeError("Admin client is closed")
        
        self._logger.info(
            "admin_create_topics_start",
            topics_count=len(topics),
            validate_only=validate_only
        )
        
        start_time = time.time()
        
        try:
            new_topics = []
            for topic in topics:
                new_topic = NewTopic(
                    name=topic.name,
                    num_partitions=topic.num_partitions,
                    replication_factor=topic.replication_factor,
                    topic_configs=topic.config or {}
                )
                new_topics.append(new_topic)
            
            result = self._admin.create_topics(new_topics=new_topics, validate_only=validate_only)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            self._logger.info(
                "admin_create_topics_complete",
                topics_count=len(topics),
                duration_ms=duration_ms
            )
            
            return result
            
        except Exception as e:
            self._logger.error("admin_create_topics_error", error=e)
            raise
    
    def delete_topics(self, topics: List[str], timeout_ms: Optional[int] = None) -> Dict[str, Any]:
        if self._closed:
            raise RuntimeError("Admin client is closed")
        
        self._logger.info(
            "admin_delete_topics_start",
            topics_count=len(topics),
            topics=','.join(topics)
        )
        
        start_time = time.time()
        
        try:
            result = self._admin.delete_topics(topics=topics, timeout_ms=timeout_ms)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            self._logger.info(
                "admin_delete_topics_complete",
                topics_count=len(topics),
                duration_ms=duration_ms
            )
            
            return result
            
        except Exception as e:
            self._logger.error("admin_delete_topics_error", error=e)
            raise
    
    def list_topics(self) -> Set[str]:
        if self._closed:
            raise RuntimeError("Admin client is closed")
        
        self._logger.debug("admin_list_topics_start")
        
        try:
            metadata = self._admin.list_topics()
            topics = set(metadata)
            
            self._logger.info("admin_list_topics_complete", topics_count=len(topics))
            
            return topics
            
        except Exception as e:
            self._logger.error("admin_list_topics_error", error=e)
            raise
    
    def describe_topics(self, topics: List[str]) -> Dict[str, Any]:
        if self._closed:
            raise RuntimeError("Admin client is closed")
        
        self._logger.debug("admin_describe_topics_start", topics_count=len(topics))
        
        try:
            metadata = self._admin._client.cluster
            
            result = {}
            for topic in topics:
                if topic in metadata.topics():
                    topic_metadata = metadata.topic_metadata(topic)
                    partitions_info = []
                    
                    for partition in metadata.partitions_for_topic(topic) or []:
                        partition_metadata = metadata.partition_metadata(topic, partition)
                        partitions_info.append({
                            'partition': partition,
                            'leader': partition_metadata.leader,
                            'replicas': list(partition_metadata.replicas),
                            'isr': list(partition_metadata.isr)
                        })
                    
                    result[topic] = {
                        'partitions': partitions_info,
                        'partition_count': len(partitions_info)
                    }
            
            self._logger.info("admin_describe_topics_complete", topics_count=len(result))
            
            return result
            
        except Exception as e:
            self._logger.error("admin_describe_topics_error", error=e)
            raise
    
    def create_partitions(self, topic_partitions: Dict[str, int], validate_only: bool = False) -> Dict[str, Any]:
        if self._closed:
            raise RuntimeError("Admin client is closed")
        
        self._logger.info(
            "admin_create_partitions_start",
            topics_count=len(topic_partitions),
            validate_only=validate_only
        )
        
        start_time = time.time()
        
        try:
            result = self._admin.create_partitions(
                topic_partitions=topic_partitions,
                validate_only=validate_only
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            self._logger.info(
                "admin_create_partitions_complete",
                topics_count=len(topic_partitions),
                duration_ms=duration_ms
            )
            
            return result
            
        except Exception as e:
            self._logger.error("admin_create_partitions_error", error=e)
            raise
    
    def describe_configs(self, resources: List[ConfigResource]) -> Dict[ConfigResource, Any]:
        if self._closed:
            raise RuntimeError("Admin client is closed")
        
        self._logger.debug("admin_describe_configs_start", resources_count=len(resources))
        
        try:
            result = self._admin.describe_configs(config_resources=resources)
            
            self._logger.info("admin_describe_configs_complete", resources_count=len(result))
            
            return result
            
        except Exception as e:
            self._logger.error("admin_describe_configs_error", error=e)
            raise
    
    def alter_configs(self, resources: List[ConfigResource]) -> Dict[ConfigResource, Any]:
        if self._closed:
            raise RuntimeError("Admin client is closed")
        
        self._logger.info("admin_alter_configs_start", resources_count=len(resources))
        
        start_time = time.time()
        
        try:
            result = self._admin.alter_configs(config_resources=resources)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            self._logger.info(
                "admin_alter_configs_complete",
                resources_count=len(resources),
                duration_ms=duration_ms
            )
            
            return result
            
        except Exception as e:
            self._logger.error("admin_alter_configs_error", error=e)
            raise
    
    def list_consumer_groups(self) -> List[str]:
        if self._closed:
            raise RuntimeError("Admin client is closed")
        
        self._logger.debug("admin_list_consumer_groups_start")
        
        try:
            result = self._admin.list_consumer_groups()
            groups = [group[0] for group in result]
            
            self._logger.info("admin_list_consumer_groups_complete", groups_count=len(groups))
            
            return groups
            
        except Exception as e:
            self._logger.error("admin_list_consumer_groups_error", error=e)
            raise
    
    def describe_consumer_groups(self, group_ids: List[str]) -> Dict[str, Any]:
        if self._closed:
            raise RuntimeError("Admin client is closed")
        
        self._logger.debug("admin_describe_consumer_groups_start", groups_count=len(group_ids))
        
        try:
            result = self._admin.describe_consumer_groups(group_ids=group_ids)
            
            self._logger.info("admin_describe_consumer_groups_complete", groups_count=len(result))
            
            return result
            
        except Exception as e:
            self._logger.error("admin_describe_consumer_groups_error", error=e)
            raise
    
    def close(self) -> None:
        if self._closed:
            return
        
        self._logger.info("admin_close_start")
        
        try:
            self._admin.close()
            self._closed = True
            self._logger.info("admin_close_complete")
        except Exception as e:
            self._logger.error("admin_close_error", error=e)
            raise

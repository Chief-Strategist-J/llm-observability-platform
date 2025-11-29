import sys
import time
from pathlib import Path
from typing import List
from temporalio import activity

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.logql_logger import LogQLLogger
from infrastructure.orchestrator.kafka.clients.kafka_admin_client import (
    KafkaAdminClientWrapper,
    AdminConfig,
    TopicConfig
)


logger = LogQLLogger(__name__)


@activity.defn(name="create_topic_activity")
async def create_topic_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    start_time = time.time()
    
    logger.info(
        "activity_start",
        activity="create_topic",
        topic=params.get("topic_name"),
        trace_id=trace_id
    )
    
    admin = None
    try:
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        topic_name = params["topic_name"]
        num_partitions = params.get("num_partitions", 1)
        replication_factor = params.get("replication_factor", 1)
        topic_config = params.get("config", {})
        
        admin_config = AdminConfig(bootstrap_servers=bootstrap_servers)
        admin = KafkaAdminClientWrapper(admin_config)
        
        topic = TopicConfig(
            name=topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor,
            config=topic_config
        )
        
        result = admin.create_topics([topic])
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "activity_complete",
            activity="create_topic",
            topic=topic_name,
            partitions=num_partitions,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        
        return {
            "success": True,
            "topic": topic_name,
            "num_partitions": num_partitions,
            "replication_factor": replication_factor
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "activity_failed",
            activity="create_topic",
            error=e,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        if admin:
            admin.close()


@activity.defn(name="delete_topic_activity")
async def delete_topic_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    start_time = time.time()
    
    logger.info(
        "activity_start",
        activity="delete_topic",
        topics=params.get("topics"),
        trace_id=trace_id
    )
    
    admin = None
    try:
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        topics = params["topics"]
        
        if isinstance(topics, str):
            topics = [topics]
        
        admin_config = AdminConfig(bootstrap_servers=bootstrap_servers)
        admin = KafkaAdminClientWrapper(admin_config)
        
        result = admin.delete_topics(topics)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "activity_complete",
            activity="delete_topic",
            topics_count=len(topics),
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        
        return {
            "success": True,
            "deleted_topics": topics
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "activity_failed",
            activity="delete_topic",
            error=e,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        if admin:
            admin.close()


@activity.defn(name="list_topics_activity")
async def list_topics_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    start_time = time.time()
    
    logger.info("activity_start", activity="list_topics", trace_id=trace_id)
    
    admin = None
    try:
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        
        admin_config = AdminConfig(bootstrap_servers=bootstrap_servers)
        admin = KafkaAdminClientWrapper(admin_config)
        
        topics = admin.list_topics()
        topics_list = list(topics)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "activity_complete",
            activity="list_topics",
            topics_count=len(topics_list),
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        
        return {
            "success": True,
            "topics": topics_list,
            "count": len(topics_list)
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "activity_failed",
            activity="list_topics",
            error=e,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        if admin:
            admin.close()


@activity.defn(name="describe_topic_activity")
async def describe_topic_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    start_time = time.time()
    
    logger.info(
        "activity_start",
        activity="describe_topic",
        topics=params.get("topics"),
        trace_id=trace_id
    )
    
    admin = None
    try:
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        topics = params["topics"]
        
        if isinstance(topics, str):
            topics = [topics]
        
        admin_config = AdminConfig(bootstrap_servers=bootstrap_servers)
        admin = KafkaAdminClientWrapper(admin_config)
        
        metadata = admin.describe_topics(topics)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "activity_complete",
            activity="describe_topic",
            topics_count=len(metadata),
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        
        return {
            "success": True,
            "metadata": metadata
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "activity_failed",
            activity="describe_topic",
            error=e,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        if admin:
            admin.close()


@activity.defn(name="list_consumer_groups_activity")
async def list_consumer_groups_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    start_time = time.time()
    
    logger.info("activity_start", activity="list_consumer_groups", trace_id=trace_id)
    
    admin = None
    try:
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        
        admin_config = AdminConfig(bootstrap_servers=bootstrap_servers)
        admin = KafkaAdminClientWrapper(admin_config)
        
        groups = admin.list_consumer_groups()
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "activity_complete",
            activity="list_consumer_groups",
            groups_count=len(groups),
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        
        return {
            "success": True,
            "groups": groups,
            "count": len(groups)
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "activity_failed",
            activity="list_consumer_groups",
            error=e,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        if admin:
            admin.close()


@activity.defn(name="describe_consumer_group_activity")
async def describe_consumer_group_activity(params: dict) -> dict:
    trace_id = logger.set_trace_id()
    start_time = time.time()
    
    logger.info(
        "activity_start",
        activity="describe_consumer_group",
        groups=params.get("group_ids"),
        trace_id=trace_id
    )
    
    admin = None
    try:
        bootstrap_servers = params.get("bootstrap_servers", ["localhost:9092"])
        group_ids = params["group_ids"]
        
        if isinstance(group_ids, str):
            group_ids = [group_ids]
        
        admin_config = AdminConfig(bootstrap_servers=bootstrap_servers)
        admin = KafkaAdminClientWrapper(admin_config)
        
        metadata = admin.describe_consumer_groups(group_ids)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            "activity_complete",
            activity="describe_consumer_group",
            groups_count=len(metadata),
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        
        return {
            "success": True,
            "metadata": str(metadata)
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "activity_failed",
            activity="describe_consumer_group",
            error=e,
            duration_ms=duration_ms,
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        if admin:
            admin.close()

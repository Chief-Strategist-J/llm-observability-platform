from typing import List, Dict, Any, Optional

from infrastructure.messaging.application.clients.base_client import BaseClient, ClientConfig


class ProducerClient(BaseClient):
    def __init__(self, config: ClientConfig):
        super().__init__(config)
        self.base_path = "/api/v1/producer"
    
    def produce_message(self, topic: str, value: Any, key: Optional[str] = None,
                       partition: Optional[int] = None, 
                       headers: Optional[Dict] = None) -> Dict[str, Any]:
        data = {
            "topic": topic,
            "key": key,
            "value": value,
            "partition": partition,
            "headers": headers or {}
        }
        return self.post(f"{self.base_path}/produce", data)
    
    def produce_messages_batch(self, messages: List[Dict]) -> Dict[str, Any]:
        data = {"messages": messages}
        return self.post(f"{self.base_path}/produce/batch", data)
    
    def list_topics(self) -> Dict[str, List[str]]:
        return self.get(f"{self.base_path}/topics")
    
    def create_topic(self, topic_name: str, partitions: int = 1,
                    replication_factor: int = 1) -> Dict[str, Any]:
        params = {
            "topic_name": topic_name,
            "partitions": partitions,
            "replication_factor": replication_factor
        }
        return self.post(f"{self.base_path}/topics/{topic_name}", params)

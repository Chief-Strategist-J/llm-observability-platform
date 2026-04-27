from typing import List, Dict, Any, Optional

from application.clients.base_client import BaseClient, ClientConfig


class ConsumerClient(BaseClient):
    def __init__(self, config: ClientConfig):
        super().__init__(config)
        self.base_path = "/api/v1/consumer"
    
    def consume_messages(self, topic: str, consumer_group: str,
                         partition: Optional[int] = None,
                         max_messages: int = 10,
                         timeout_ms: int = 1000) -> Dict[str, Any]:
        data = {
            "topic": topic,
            "consumer_group": consumer_group,
            "partition": partition,
            "max_messages": max_messages,
            "timeout_ms": timeout_ms
        }
        return self.post(f"{self.base_path}/consume", data)
    
    def commit_offset(self, consumer_group: str, topic: str,
                     partition: int, offset: int) -> Dict[str, bool]:
        data = {
            "consumer_group": consumer_group,
            "topic": topic,
            "partition": partition,
            "offset": offset
        }
        return self.post(f"{self.base_path}/offsets", data)
    
    def get_offset(self, consumer_group: str, topic: str,
                  partition: int) -> Dict[str, Any]:
        return self.get(f"{self.base_path}/offsets/{consumer_group}/{topic}/{partition}")
    
    def subscribe(self, topic: str, consumer_group: str) -> Dict[str, bool]:
        params = {"topic": topic, "consumer_group": consumer_group}
        return self.post(f"{self.base_path}/subscribe", params)
    
    def unsubscribe(self, topic: str, consumer_group: str) -> Dict[str, bool]:
        params = {"topic": topic, "consumer_group": consumer_group}
        return self.post(f"{self.base_path}/unsubscribe", params)
    
    def list_subscriptions(self, consumer_group: str) -> Dict[str, List[str]]:
        return self.get(f"{self.base_path}/subscriptions/{consumer_group}")

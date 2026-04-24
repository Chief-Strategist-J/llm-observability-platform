from typing import List, Dict, Any

from infrastructure.messaging.application.clients.base_client import BaseClient, ClientConfig


class BrokerClient(BaseClient):
    def __init__(self, config: ClientConfig):
        super().__init__(config)
        self.base_path = "/api/v1/broker"
    
    def get_broker_metadata(self) -> Dict[str, Any]:
        return self.get(f"{self.base_path}/metadata")
    
    def list_brokers(self) -> List[Dict[str, Any]]:
        return self.get(f"{self.base_path}/brokers")
    
    def get_broker_info(self, broker_id: int) -> Dict[str, Any]:
        return self.get(f"{self.base_path}/brokers/{broker_id}")
    
    def list_topics(self) -> Dict[str, List[str]]:
        return self.get(f"{self.base_path}/topics")
    
    def get_topic_metadata(self, topic_name: str) -> Dict[str, Any]:
        return self.get(f"{self.base_path}/topics/{topic_name}/metadata")
    
    def get_consumer_groups(self) -> List[Dict[str, Any]]:
        return self.get(f"{self.base_path}/consumer-groups")
    
    def get_consumer_group_lag(self, group_id: str) -> List[Dict[str, Any]]:
        return self.get(f"{self.base_path}/consumer-groups/{group_id}/lag")
    
    def get_cluster_config(self) -> Dict[str, str]:
        return self.get(f"{self.base_path}/config")

from typing import List, Dict, Any

from infrastructure.messaging.domain.ports.broker_port import BrokerPort


class BrokerDomainClient:
    def __init__(self, broker_port: BrokerPort):
        self._broker = broker_port
    
    def get_broker_metadata(self) -> Dict[str, Any]:
        return self._broker.get_broker_metadata()
    
    def list_brokers(self) -> List[Dict[str, Any]]:
        return self._broker.list_brokers()
    
    def get_broker_info(self, broker_id: int) -> Dict[str, Any]:
        return self._broker.get_broker_info(broker_id)
    
    def list_topics(self) -> List[str]:
        return self._broker.list_topics()
    
    def get_topic_metadata(self, topic_name: str) -> Dict[str, Any]:
        return self._broker.get_topic_metadata(topic_name)
    
    def get_consumer_groups(self) -> List[Dict[str, Any]]:
        return self._broker.get_consumer_groups()
    
    def get_consumer_group_lag(self, group_id: str) -> List[Dict[str, Any]]:
        return self._broker.get_consumer_group_lag(group_id)
    
    def get_cluster_config(self) -> Dict[str, str]:
        return self._broker.get_cluster_config()
    
    def close(self):
        if hasattr(self._broker, 'close'):
            self._broker.close()

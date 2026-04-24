from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BrokerPort(ABC):
    @abstractmethod
    def get_broker_metadata(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def list_brokers(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_broker_info(self, broker_id: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def list_topics(self) -> List[str]:
        pass

    @abstractmethod
    def get_topic_metadata(self, topic_name: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_consumer_groups(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_consumer_group_lag(self, group_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_cluster_config(self) -> Dict[str, Any]:
        pass

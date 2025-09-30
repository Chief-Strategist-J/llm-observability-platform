from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from core.domain.models import GraphNode, GraphRelation

class GraphStorePort(ABC):
    @abstractmethod
    async def create_node(self, node: GraphNode) -> str:
        pass
    
    @abstractmethod
    async def create_relation(self, relation: GraphRelation) -> bool:
        pass
    
    @abstractmethod
    async def find_similar_nodes(self, embedding: List[float], limit: int) -> List[GraphNode]:
        pass
    
    @abstractmethod
    async def traverse_graph(self, start_node_id: str, max_hops: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        pass
    
    @abstractmethod
    async def query_cypher(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

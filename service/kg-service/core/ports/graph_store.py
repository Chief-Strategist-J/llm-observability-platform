from abc import ABC, abstractmethod
from typing import Any

from ..domain.models import GraphNode, GraphRelation


class GraphStorePort(ABC):
    @abstractmethod
    async def create_node(self, node: GraphNode) -> str:
        pass

    @abstractmethod
    async def create_relation(self, relation: GraphRelation) -> bool:
        pass

    @abstractmethod
    async def find_similar_nodes(
        self, embedding: list[float], limit: int
    ) -> list[GraphNode]:
        pass

    @abstractmethod
    async def traverse_graph(
        self, start_node_id: str, max_hops: int, filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def get_node(self, node_id: str) -> GraphNode | None:
        pass

    @abstractmethod
    async def query_cypher(
        self, query: str, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        pass

from neo4j import AsyncGraphDatabase
from typing import List, Dict, Any, Optional
from core.ports.graph_store import GraphStorePort
from core.domain.models import GraphNode, GraphRelation

class Neo4jGraphStore(GraphStorePort):
    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    
    async def create_node(self, node: GraphNode) -> str:
        async with self.driver.session() as session:
            query = f"""
            CREATE (n:{node.label.value} $props)
            SET n.embedding = $embedding
            RETURN n.id as id
            """
            result = await session.run(
                query,
                props={**node.properties, "id": node.id},
                embedding=node.embedding
            )
            record = await result.single()
            return record["id"] if record else node.id
    
    async def create_relation(self, relation: GraphRelation) -> bool:
        async with self.driver.session() as session:
            query = f"""
            MATCH (a {{id: $source_id}})
            MATCH (b {{id: $target_id}})
            CREATE (a)-[r:`{relation.relation_type}` $props]->(b)
            RETURN r
            """
            result = await session.run(
                query,
                source_id=relation.source_id,
                target_id=relation.target_id,
                props=relation.properties
            )
            return await result.single() is not None
    
    async def find_similar_nodes(self, embedding: List[float], limit: int) -> List[GraphNode]:
        async with self.driver.session() as session:
            query = """
            MATCH (n)
            WHERE n.embedding IS NOT NULL
            RETURN n
            LIMIT $limit
            """
            result = await session.run(query, limit=limit)
            
            nodes = []
            async for record in result:
                node_data = dict(record["n"])
                nodes.append(GraphNode(
                    id=node_data.get("id", ""),
                    label=node_data.get("label", "Entity"),
                    properties=node_data,
                    embedding=node_data.get("embedding")
                ))
            return nodes
    
    async def traverse_graph(self, start_node_id: str, max_hops: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        async with self.driver.session() as session:
            query = f"""
            MATCH path = (start {{id: $start_id}})-[*1..{max_hops}]-(end)
            RETURN path
            LIMIT 50
            """
            result = await session.run(query, start_id=start_node_id)
            
            paths = []
            async for record in result:
                paths.append({"path": str(record["path"])})
            return paths
    
    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        async with self.driver.session() as session:
            query = "MATCH (n {id: $node_id}) RETURN n"
            result = await session.run(query, node_id=node_id)
            record = await result.single()
            
            if record:
                node_data = dict(record["n"])
                return GraphNode(
                    id=node_data.get("id", ""),
                    label=node_data.get("label", "Entity"),
                    properties=node_data,
                    embedding=node_data.get("embedding")
                )
            return None
    
    async def query_cypher(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        async with self.driver.session() as session:
            result = await session.run(query, **params)
            return [dict(record) async for record in result]
    
    async def close(self):
        await self.driver.close()

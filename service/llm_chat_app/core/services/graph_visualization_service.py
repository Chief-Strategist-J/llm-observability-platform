import logging
import json
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path
import networkx as nx
from pyvis.network import Network
from core.config.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
    _NEO4J_AVAILABLE = True
except Exception as e:
    _NEO4J_AVAILABLE = False
    logger.warning("event=neo4j_import_failed error=%s", str(e))


class GraphVisualizationService:
    @staticmethod
    def generate_cypher_query(user_query: str, query_type: str = "general") -> str:
        logger.info("event=cypher_generation_start query_type=%s query_len=%s", query_type, len(user_query))
        
        query_lower = user_query.lower()
        
        if any(word in query_lower for word in ["topic", "about", "discuss", "related"]):
            words = user_query.split()
            topic = words[-1].strip('?.,!') if len(words) > 0 else "python"
            cypher = f"""
            MATCH (c:Conversation)-[:ABOUT]->(t:Topic {{name: '{topic}'}})
            MATCH (u:User)-[:ASKED]->(c)
            OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity)
            OPTIONAL MATCH (c)-[:FEELS]->(em:Emotion)
            RETURN u, c, t, e, em
            LIMIT 50
            """
            logger.info("event=cypher_topic_query topic=%s", topic)
            return cypher.strip()
        
        if any(word in query_lower for word in ["entity", "mention", "what", "who"]):
            cypher = """
            MATCH (c:Conversation)-[:MENTIONS]->(e:Entity)
            MATCH (u:User)-[:ASKED]->(c)
            OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
            RETURN u, c, e, t
            LIMIT 50
            """
            logger.info("event=cypher_entity_query")
            return cypher.strip()
        
        if any(word in query_lower for word in ["chain", "sequence", "flow", "progression", "history"]):
            cypher = """
            MATCH (u:User)-[:ASKED]->(c1:Conversation)
            OPTIONAL MATCH (c1)-[:FOLLOWED_BY]->(c2:Conversation)
            OPTIONAL MATCH (c1)-[:FEELS]->(em1:Emotion)
            OPTIONAL MATCH (c2)-[:FEELS]->(em2:Emotion)
            RETURN u, c1, c2, em1, em2
            ORDER BY c1.ts DESC
            LIMIT 50
            """
            logger.info("event=cypher_chain_query")
            return cypher.strip()
        
        if any(word in query_lower for word in ["emotion", "feel", "sentiment", "mood"]):
            cypher = """
            MATCH (c:Conversation)-[:FEELS]->(em:Emotion)
            MATCH (u:User)-[:ASKED]->(c)
            OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
            RETURN u, c, em, t
            ORDER BY c.ts DESC
            LIMIT 50
            """
            logger.info("event=cypher_emotion_query")
            return cypher.strip()
        
        cypher = """
        MATCH (u:User)-[:ASKED]->(c:Conversation)
        OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
        OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity)
        OPTIONAL MATCH (c)-[:FEELS]->(em:Emotion)
        OPTIONAL MATCH (m:Model)-[:RESPONDED_TO]->(c)
        RETURN u, c, t, e, em, m
        ORDER BY c.ts DESC
        LIMIT 50
        """
        logger.info("event=cypher_default_query")
        return cypher.strip()
    
    @staticmethod
    def fetch_graph_data(cypher_query: str) -> Tuple[Optional[Dict], Optional[str]]:
        logger.info("event=fetch_graph_data_start query_len=%s", len(cypher_query))
        
        if not _NEO4J_AVAILABLE or not NEO4J_URI:
            error_msg = "Neo4j not available"
            logger.warning("event=fetch_graph_data_unavailable")
            return None, error_msg
        
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            
            try:
                with driver.session() as session:
                    result = session.run(cypher_query)
                    records = list(result)
                    
                    if not records:
                        logger.info("event=fetch_graph_data_empty")
                        return {"nodes": [], "edges": []}, None
                    
                    nodes = []
                    edges = []
                    node_ids = set()
                    
                    for record in records:
                        for key, value in record.items():
                            if value is None:
                                continue
                            
                            if hasattr(value, 'id') and hasattr(value, 'labels'):
                                node_id = str(value.id)
                                if node_id not in node_ids:
                                    node_ids.add(node_id)
                                    node_label = list(value.labels)[0] if value.labels else "Node"
                                    node_props = dict(value)
                                    
                                    nodes.append({
                                        "id": node_id,
                                        "label": node_label,
                                        "title": f"{node_label}: {node_props.get('name', node_props.get('id', ''))}",
                                        "properties": node_props
                                    })
                            
                            elif hasattr(value, 'start_node') and hasattr(value, 'end_node'):
                                start_id = str(value.start_node.id)
                                end_id = str(value.end_node.id)
                                rel_type = value.type
                                
                                edges.append({
                                    "from": start_id,
                                    "to": end_id,
                                    "label": rel_type,
                                    "properties": dict(value)
                                })
                    
                    graph_data = {
                        "nodes": nodes,
                        "edges": edges,
                        "record_count": len(records)
                    }
                    
                    logger.info("event=fetch_graph_data_success nodes=%s edges=%s", len(nodes), len(edges))
                    return graph_data, None
                    
            except Exception as e:
                error_msg = f"Query execution failed: {str(e)}"
                logger.error("event=fetch_graph_data_query_failed error=%s", str(e))
                return None, error_msg
            finally:
                try:
                    driver.close()
                except Exception:
                    pass
                    
        except Exception as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error("event=fetch_graph_data_connection_failed error=%s", str(e))
            return None, error_msg
    
    @staticmethod
    def create_visualization(
        graph_data: Dict,
        output_file: str = "graph_visualization.html",
        title: str = "Knowledge Graph Visualization"
    ) -> Tuple[str, Optional[str]]:
        logger.info("event=create_visualization_start nodes=%s edges=%s", 
                   len(graph_data.get("nodes", [])), len(graph_data.get("edges", [])))
        
        try:
            g = nx.DiGraph()
            
            for node in graph_data.get("nodes", []):
                node_id = node["id"]
                label = node.get("label", "Node")
                title = node.get("title", "")
                
                g.add_node(node_id, label=label, title=title)
            
            for edge in graph_data.get("edges", []):
                g.add_edge(edge["from"], edge["to"], label=edge.get("label", ""))
            
            net = Network(
                directed=True,
                height="750px",
                width="100%",
                notebook=False
            )
            
            net.from_nx(g)
            
            net.toggle_physics(True)
            net.set_options("""
            {
                "physics": {
                    "enabled": true,
                    "stabilization": {
                        "iterations": 200
                    },
                    "barnesHut": {
                        "gravitationalConstant": -26000,
                        "centralGravity": 0.3,
                        "springLength": 200,
                        "springConstant": 0.04
                    }
                },
                "interaction": {
                    "navigationButtons": true,
                    "keyboard": true
                }
            }
            """)
            
            net.show(output_file)
            
            logger.info("event=create_visualization_success file=%s", output_file)
            return output_file, None
            
        except Exception as e:
            error_msg = f"Visualization creation failed: {str(e)}"
            logger.error("event=create_visualization_failed error=%s", str(e))
            return "", error_msg
    
    @staticmethod
    def get_graph_statistics(graph_data: Dict) -> Dict[str, Any]:
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        
        node_types = {}
        for node in nodes:
            label = node.get("label", "Unknown")
            node_types[label] = node_types.get(label, 0) + 1
        
        edge_types = {}
        for edge in edges:
            label = edge.get("label", "Unknown")
            edge_types[label] = edge_types.get(label, 0) + 1
        
        stats = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_types": node_types,
            "edge_types": edge_types,
            "density": len(edges) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0
        }
        
        logger.info("event=graph_statistics stats=%s", stats)
        return stats

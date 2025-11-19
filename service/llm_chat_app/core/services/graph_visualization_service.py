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
    
    NODE_COLORS = {
        "User": "#8B5CF6",
        "Conversation": "#3B82F6",
        "Topic": "#EC4899",
        "Entity": "#10B981",
        "Emotion": "#F59E0B",
        "Model": "#EF4444"
    }
    
    NODE_SIZES = {
        "User": 35,
        "Conversation": 25,
        "Topic": 20,
        "Entity": 20,
        "Emotion": 20,
        "Model": 20
    }
    
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
        title: str = "Knowledge Graph Visualization",
        view_mode: str = "full"
    ) -> Tuple[str, Optional[str]]:
        logger.info(
            "event=create_visualization_start nodes=%s edges=%s output_file=%s view_mode=%s",
            len(graph_data.get("nodes", [])),
            len(graph_data.get("edges", [])),
            output_file,
            view_mode
        )

        try:
            net = Network(
                directed=True,
                height="820px",
                width="100%",
                notebook=False,
                bgcolor="#1E1E1E",
                font_color="#E4E4E7"
            )

            layout_user = []
            layout_conversation = []
            layout_other = []

            for node in graph_data.get("nodes", []):
                label = node.get("label", "Node")
                if label == "User":
                    layout_user.append(node)
                elif label == "Conversation":
                    layout_conversation.append(node)
                else:
                    layout_other.append(node)

            def add_node_to_net(node, label_override):
                node_id = node["id"]
                props = node.get("properties", {})
                label = node.get("label", "")
                color = GraphVisualizationService.NODE_COLORS.get(label, "#6B7280")
                size = GraphVisualizationService.NODE_SIZES.get(label, 20)
                title_html = "<b>" + label + "</b><br>"
                for k, v in props.items():
                    if k != "id":
                        title_html += f"{k}: {v}<br>"
                net.add_node(
                    node_id,
                    label=label_override,
                    title=title_html,
                    size=size,
                    color=color,
                    shape="dot",
                    borderWidth=2,
                    borderWidthSelected=4,
                    font={"size": 14, "color": "#FFFFFF"}
                )

            for node in layout_user:
                props = node.get("properties", {})
                add_node_to_net(node, props.get("name", "User"))

            for node in layout_conversation:
                add_node_to_net(node, "")

            for node in layout_other:
                props = node.get("properties", {})
                add_node_to_net(node, props.get("name", ""))

            for edge in graph_data.get("edges", []):
                net.add_edge(
                    edge["from"],
                    edge["to"],
                    title=edge.get("label", ""),
                    width=1.4,
                    color={"color": "#A1A1AA", "highlight": "#FAFAFA"},
                    arrows={"to": {"enabled": True, "scaleFactor": 0.6}},
                    smooth={"enabled": True, "type": "dynamic"}
                )

            physics = {
                "enabled": True,
                "stabilization": {"enabled": True, "iterations": 300},
                "forceAtlas2Based": {
                    "gravitationalConstant": -60,
                    "centralGravity": 0.015,
                    "springLength": 140,
                    "springConstant": 0.10,
                    "damping": 0.4,
                    "avoidOverlap": 1
                },
                "solver": "forceAtlas2Based"
            }

            net.set_options(json.dumps({
                "physics": physics,
                "interaction": {
                    "hover": True,
                    "navigationButtons": True,
                    "keyboard": True,
                    "tooltipDelay": 100,
                    "zoomView": True,
                    "dragNodes": True
                },
                "nodes": {
                    "shape": "dot"
                },
                "edges": {
                    "smooth": {"enabled": True, "type": "dynamic"},
                    "color": {"inherit": False}
                }
            }))

            net.write_html(output_file)

            logger.info(
                "event=create_visualization_success output_file=%s size=%s",
                output_file,
                Path(output_file).stat().st_size if Path(output_file).exists() else -1
            )

            return output_file, None

        except Exception as e:
            logger.error("event=create_visualization_error error=%s", str(e))
            return "", str(e)

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
    
    @staticmethod
    def generate_ai_insights(graph_data: Dict, username: str) -> Dict[str, Any]:
        logger.info("event=generate_ai_insights_start user=%s nodes=%s", 
                   username, len(graph_data.get("nodes", [])))
        
        insights = {}
        
        try:
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])
            
            topic_counts = {}
            entity_counts = {}
            emotion_counts = {}
            
            for node in nodes:
                label = node.get("label", "")
                props = node.get("properties", {})
                name = props.get("name", "")
                
                if label == "Topic" and name:
                    topic_counts[name] = topic_counts.get(name, 0) + 1
                elif label == "Entity" and name:
                    entity_counts[name] = entity_counts.get(name, 0) + 1
                elif label == "Emotion" and name:
                    emotion_counts[name] = emotion_counts.get(name, 0) + 1
            
            if topic_counts:
                sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
                insights["frequent_topics"] = [f"{topic} ({count} times)" for topic, count in sorted_topics[:5]]
                logger.info("event=insights_frequent_topics count=%s top_topic=%s", 
                           len(sorted_topics), sorted_topics[0][0] if sorted_topics else None)
            
            if entity_counts:
                sorted_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)
                insights["frequent_entities"] = [f"{entity} ({count} times)" for entity, count in sorted_entities[:5]]
                logger.info("event=insights_frequent_entities count=%s top_entity=%s", 
                           len(sorted_entities), sorted_entities[0][0] if sorted_entities else None)
            
            if emotion_counts:
                sorted_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)
                insights["emotional_patterns"] = [f"{emotion} ({count} times)" for emotion, count in sorted_emotions[:5]]
                logger.info("event=insights_emotional_patterns count=%s primary_emotion=%s", 
                           len(sorted_emotions), sorted_emotions[0][0] if sorted_emotions else None)
            
            conversation_nodes = [n for n in nodes if n.get("label") == "Conversation"]
            if conversation_nodes:
                insights["conversation_summary"] = f"You have {len(conversation_nodes)} conversations in this view"
                logger.info("event=insights_conversation_summary count=%s", len(conversation_nodes))
            
            topic_entity_pairs = {}
            for edge in edges:
                if edge.get("label") == "MENTIONS":
                    from_node = next((n for n in nodes if n["id"] == edge["from"]), None)
                    to_node = next((n for n in nodes if n["id"] == edge["to"]), None)
                    if from_node and to_node:
                        from_label = from_node.get("label", "")
                        to_label = to_node.get("label", "")
                        if from_label == "Conversation" and to_label == "Entity":
                            for about_edge in edges:
                                if about_edge["from"] == edge["from"] and about_edge.get("label") == "ABOUT":
                                    topic_node = next((n for n in nodes if n["id"] == about_edge["to"]), None)
                                    if topic_node and topic_node.get("label") == "Topic":
                                        topic_name = topic_node.get("properties", {}).get("name", "")
                                        entity_name = to_node.get("properties", {}).get("name", "")
                                        if topic_name and entity_name:
                                            pair = f"{topic_name} → {entity_name}"
                                            topic_entity_pairs[pair] = topic_entity_pairs.get(pair, 0) + 1
            
            if topic_entity_pairs:
                sorted_pairs = sorted(topic_entity_pairs.items(), key=lambda x: x[1], reverse=True)
                insights["topic_clusters"] = [f"{pair} ({count} times)" for pair, count in sorted_pairs[:5]]
                logger.info("event=insights_topic_clusters count=%s top_cluster=%s", 
                           len(sorted_pairs), sorted_pairs[0][0] if sorted_pairs else None)
            
            logger.info("event=generate_ai_insights_success user=%s insight_types=%s", 
                       username, list(insights.keys()))
            
        except Exception as e:
            logger.error("event=generate_ai_insights_failed user=%s error=%s", username, str(e))
        
        return insights 
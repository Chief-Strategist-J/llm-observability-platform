import os
import json
import logging
import socket
from pathlib import Path
from typing import Optional, List, Dict, Any
from core.config.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

logger = logging.getLogger(__name__)

_BACKUP_DIR = Path.cwd() / "chat_backups"
_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
_LOCAL_STORE = _BACKUP_DIR / "conversations.json"
if not _LOCAL_STORE.exists():
    _LOCAL_STORE.write_text("[]")

try:
    from neo4j import GraphDatabase
    _NEO4J_AVAILABLE = True
    logger.info("event=neo4j_import_success")
except Exception as e:
    _NEO4J_AVAILABLE = False
    logger.warning("event=neo4j_import_failed error=%s", str(e))

def _host_resolves(uri: Optional[str]) -> bool:
    if not uri:
        logger.debug("event=host_resolve_check result=empty_uri")
        return False
    try:
        if uri.startswith("bolt://") or uri.startswith("neo4j://") or uri.startswith("neo4j+s://"):
            if uri.startswith("bolt://"):
                hostport = uri[len("bolt://"):]
            elif uri.startswith("neo4j://"):
                hostport = uri[len("neo4j://"):]
            elif uri.startswith("neo4j+s://"):
                hostport = uri[len("neo4j+s://"):]
            else:
                hostport = uri
            host = hostport.split(":")[0]
        else:
            host = uri.split(":")[0]
        socket.getaddrinfo(host, None)
        logger.debug("event=host_resolve_success host=%s", host)
        return True
    except Exception as e:
        logger.debug("event=host_resolve_failed uri=%s error=%s", uri, str(e)[:50])
        return False

def _extract_entities_and_topics(prompt: str, response: str, model: str) -> Dict[str, Any]:
    logger.info("event=extract_entities_start prompt_len=%s response_len=%s", len(prompt), len(response))
    
    entities = []
    topics = []
    
    prompt_lower = prompt.lower()
    response_lower = response.lower()
    
    common_topics = ["weather", "code", "help", "question", "python", "ai", "data", "api", "error", "fix"]
    for topic in common_topics:
        if topic in prompt_lower or topic in response_lower:
            topics.append(topic)
    
    if len(prompt.split()) > 5:
        words = prompt.split()[:5]
        entities.append(" ".join(words))
    
    logger.info("event=extract_entities_complete entities=%s topics=%s", len(entities), len(topics))
    
    return {
        "entities": entities,
        "topics": topics
    }

def store_conversation_as_knowledge_graph(
    user: str, 
    prompt: str, 
    response: str, 
    model: str = "unknown", 
    version: str = "unknown",
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    ts = int(__import__("time").time())
    
    logger.info("event=kg_store_start user=%s model=%s prompt_len=%s response_len=%s ts=%s", 
                user, model, len(prompt), len(response), ts)
    
    extracted = _extract_entities_and_topics(prompt, response, model)
    entities = extracted["entities"]
    topics = extracted["topics"]
    
    logger.info("event=kg_extracted entities=%s topics=%s", entities, topics)
    
    try:
        if _NEO4J_AVAILABLE and NEO4J_URI and _host_resolves(NEO4J_URI):
            logger.info("event=kg_neo4j_connecting uri=%s", NEO4J_URI[:20] + "...")
            
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            
            try:
                with driver.session() as session:
                    logger.info("event=kg_neo4j_session_open user=%s", user)
                    
                    session.run(
                        "MERGE (u:User {name: $user})",
                        {"user": user}
                    )
                    logger.debug("event=kg_user_merged user=%s", user)
                    
                    session.run(
                        "MERGE (m:Model {name: $model})",
                        {"model": model}
                    )
                    logger.debug("event=kg_model_merged model=%s", model)
                    
                    conv_result = session.run(
                        """
                        CREATE (c:Conversation {
                            id: $id,
                            prompt: $prompt,
                            response: $response,
                            model: $model,
                            version: $version,
                            ts: $ts
                        })
                        RETURN id(c) as conv_id
                        """,
                        {
                            "id": f"{user}_{ts}",
                            "prompt": prompt,
                            "response": response,
                            "model": model,
                            "version": version,
                            "ts": ts
                        }
                    )
                    conv_id = conv_result.single()["conv_id"]
                    logger.info("event=kg_conversation_created conv_id=%s", conv_id)
                    
                    session.run(
                        """
                        MATCH (u:User {name: $user})
                        MATCH (c:Conversation {id: $conv_id})
                        MERGE (u)-[:ASKED]->(c)
                        """,
                        {"user": user, "conv_id": f"{user}_{ts}"}
                    )
                    logger.debug("event=kg_user_asked_relation user=%s", user)
                    
                    session.run(
                        """
                        MATCH (m:Model {name: $model})
                        MATCH (c:Conversation {id: $conv_id})
                        MERGE (m)-[:RESPONDED_TO]->(c)
                        """,
                        {"model": model, "conv_id": f"{user}_{ts}"}
                    )
                    logger.debug("event=kg_model_responded_relation model=%s", model)
                    
                    for topic in topics:
                        session.run(
                            """
                            MERGE (t:Topic {name: $topic})
                            WITH t
                            MATCH (c:Conversation {id: $conv_id})
                            MERGE (c)-[:ABOUT]->(t)
                            """,
                            {"topic": topic, "conv_id": f"{user}_{ts}"}
                        )
                        logger.debug("event=kg_topic_linked topic=%s", topic)
                    
                    for entity in entities:
                        session.run(
                            """
                            MERGE (e:Entity {name: $entity})
                            WITH e
                            MATCH (c:Conversation {id: $conv_id})
                            MERGE (c)-[:MENTIONS]->(e)
                            """,
                            {"entity": entity, "conv_id": f"{user}_{ts}"}
                        )
                        logger.debug("event=kg_entity_linked entity=%s", entity[:30])
                    
                    prev_conversations = session.run(
                        """
                        MATCH (u:User {name: $user})-[:ASKED]->(prev:Conversation)
                        WHERE prev.ts < $ts
                        RETURN prev.id as prev_id
                        ORDER BY prev.ts DESC
                        LIMIT 1
                        """,
                        {"user": user, "ts": ts}
                    )
                    
                    prev_record = prev_conversations.single()
                    if prev_record:
                        prev_id = prev_record["prev_id"]
                        session.run(
                            """
                            MATCH (prev:Conversation {id: $prev_id})
                            MATCH (curr:Conversation {id: $curr_id})
                            MERGE (prev)-[:FOLLOWED_BY]->(curr)
                            """,
                            {"prev_id": prev_id, "curr_id": f"{user}_{ts}"}
                        )
                        logger.info("event=kg_conversation_chain prev=%s curr=%s", prev_id, f"{user}_{ts}")
                
                try:
                    driver.close()
                    logger.debug("event=kg_neo4j_driver_closed")
                except Exception:
                    pass
                
                logger.info("event=kg_neo4j_success user=%s model=%s entities=%s topics=%s", 
                           user, model, len(entities), len(topics))
                return
                
            except Exception as e:
                logger.error("event=kg_neo4j_failed user=%s model=%s error=%s", user, model, str(e))
                try:
                    driver.close()
                except Exception:
                    pass
    except Exception as e:
        logger.error("event=kg_neo4j_unavailable error=%s", str(e))
    
    logger.info("event=kg_fallback_file_start user=%s", user)
    
    try:
        data = json.loads(_LOCAL_STORE.read_text())
        
        payload = {
            "user": user,
            "prompt": prompt,
            "response": response,
            "model": model,
            "version": version,
            "ts": ts,
            "entities": entities,
            "topics": topics
        }
        
        data.append(payload)
        _LOCAL_STORE.write_text(json.dumps(data, indent=2))
        
        logger.info("event=kg_file_success user=%s model=%s path=%s", user, model, str(_LOCAL_STORE))
        
    except Exception as e:
        logger.error("event=kg_file_failed user=%s error=%s", user, str(e))

def get_conversation_context(user: str, limit: int = 10) -> List[Dict]:
    results: List[Dict] = []
    
    logger.info("event=kg_get_context_start user=%s limit=%s", user, limit)
    
    try:
        if _NEO4J_AVAILABLE and NEO4J_URI and _host_resolves(NEO4J_URI):
            logger.info("event=kg_query_neo4j_start user=%s", user)
            
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            
            try:
                with driver.session() as session:
                    rows = session.run(
                        """
                        MATCH (u:User {name: $user})-[:ASKED]->(c:Conversation)
                        OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
                        OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity)
                        RETURN c.prompt as prompt, 
                               c.response as response, 
                               c.model as model, 
                               c.ts as ts,
                               collect(DISTINCT t.name) as topics,
                               collect(DISTINCT e.name) as entities
                        ORDER BY c.ts ASC
                        """,
                        {"user": user}
                    )
                    
                    for r in rows:
                        results.append({
                            "role": "user",
                            "text": r["prompt"],
                            "model": r.get("model"),
                            "ts": r.get("ts"),
                            "topics": r.get("topics", []),
                            "entities": r.get("entities", [])
                        })
                        results.append({
                            "role": "assistant",
                            "text": r["response"],
                            "model": r.get("model"),
                            "ts": r.get("ts"),
                            "topics": r.get("topics", []),
                            "entities": r.get("entities", [])
                        })
                
                try:
                    driver.close()
                except Exception:
                    pass
                
                logger.info("event=kg_query_neo4j_success user=%s count=%s", user, len(results))
                return results[-limit * 2:]
                
            except Exception as e:
                logger.error("event=kg_query_neo4j_failed user=%s error=%s", user, str(e))
                try:
                    driver.close()
                except Exception:
                    pass
    except Exception as e:
        logger.error("event=kg_query_neo4j_unavailable error=%s", str(e))
    
    logger.info("event=kg_query_file_start user=%s", user)
    
    try:
        data = json.loads(_LOCAL_STORE.read_text())
        
        for item in data:
            if item.get("user") == user:
                results.append({
                    "role": "user",
                    "text": item.get("prompt", ""),
                    "model": item.get("model"),
                    "ts": item.get("ts"),
                    "topics": item.get("topics", []),
                    "entities": item.get("entities", [])
                })
                results.append({
                    "role": "assistant",
                    "text": item.get("response", ""),
                    "model": item.get("model"),
                    "ts": item.get("ts"),
                    "topics": item.get("topics", []),
                    "entities": item.get("entities", [])
                })
        
        logger.info("event=kg_query_file_success user=%s count=%s path=%s", user, len(results), str(_LOCAL_STORE))
        
    except Exception as e:
        logger.error("event=kg_query_file_failed user=%s error=%s", user, str(e))
    
    return results[-limit * 2:]

def query_by_topic(topic: str, limit: int = 10) -> List[Dict]:
    logger.info("event=kg_query_topic_start topic=%s limit=%s", topic, limit)
    
    results = []
    
    try:
        if _NEO4J_AVAILABLE and NEO4J_URI and _host_resolves(NEO4J_URI):
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            
            try:
                with driver.session() as session:
                    rows = session.run(
                        """
                        MATCH (c:Conversation)-[:ABOUT]->(t:Topic {name: $topic})
                        MATCH (u:User)-[:ASKED]->(c)
                        RETURN u.name as user,
                               c.prompt as prompt,
                               c.response as response,
                               c.model as model,
                               c.ts as ts
                        ORDER BY c.ts DESC
                        LIMIT $limit
                        """,
                        {"topic": topic, "limit": limit}
                    )
                    
                    for r in rows:
                        results.append({
                            "user": r["user"],
                            "prompt": r["prompt"],
                            "response": r["response"],
                            "model": r["model"],
                            "ts": r["ts"]
                        })
                
                try:
                    driver.close()
                except Exception:
                    pass
                
                logger.info("event=kg_query_topic_success topic=%s count=%s", topic, len(results))
                
            except Exception as e:
                logger.error("event=kg_query_topic_failed topic=%s error=%s", topic, str(e))
                try:
                    driver.close()
                except Exception:
                    pass
    except Exception as e:
        logger.error("event=kg_query_topic_unavailable error=%s", str(e))
    
    return results

def get_user_statistics(user: str) -> Dict[str, Any]:
    logger.info("event=kg_stats_start user=%s", user)
    
    stats = {
        "total_conversations": 0,
        "models_used": [],
        "top_topics": [],
        "total_entities": 0
    }
    
    try:
        if _NEO4J_AVAILABLE and NEO4J_URI and _host_resolves(NEO4J_URI):
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            
            try:
                with driver.session() as session:
                    result = session.run(
                        """
                        MATCH (u:User {name: $user})-[:ASKED]->(c:Conversation)
                        OPTIONAL MATCH (c)-[:ABOUT]->(t:Topic)
                        OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity)
                        RETURN count(DISTINCT c) as total_conv,
                               collect(DISTINCT c.model) as models,
                               collect(DISTINCT t.name) as topics,
                               count(DISTINCT e) as entities
                        """,
                        {"user": user}
                    )
                    
                    record = result.single()
                    if record:
                        stats["total_conversations"] = record["total_conv"]
                        stats["models_used"] = [m for m in record["models"] if m]
                        stats["top_topics"] = [t for t in record["topics"] if t]
                        stats["total_entities"] = record["entities"]
                
                try:
                    driver.close()
                except Exception:
                    pass
                
                logger.info("event=kg_stats_success user=%s stats=%s", user, stats)
                
            except Exception as e:
                logger.error("event=kg_stats_failed user=%s error=%s", user, str(e))
                try:
                    driver.close()
                except Exception:
                    pass
    except Exception as e:
        logger.error("event=kg_stats_unavailable error=%s", str(e))
    
    return stats
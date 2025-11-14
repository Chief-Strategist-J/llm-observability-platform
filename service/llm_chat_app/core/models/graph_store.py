import os
import json
import logging
import socket
from pathlib import Path
from typing import Optional, List, Dict
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
except Exception:
    _NEO4J_AVAILABLE = False

def _host_resolves(uri: Optional[str]) -> bool:
    if not uri:
        return False
    try:
        if uri.startswith("bolt://"):
            hostport = uri[len("bolt://"):]
            host = hostport.split(":")[0]
        else:
            host = uri.split(":")[0]
        socket.getaddrinfo(host, None)
        return True
    except Exception:
        return False

def store_conversation(user: str, prompt: str, response: str, model: str = "unknown", version: str = "unknown") -> None:
    ts = int(__import__("time").time())
    payload = {"user": user, "prompt": prompt, "response": response, "model": model, "version": version, "ts": ts}

    logger.info("event=store_conversation_start user=%s model=%s prompt_len=%s response_len=%s", user, model, len(prompt), len(response))

    try:
        if _NEO4J_AVAILABLE and NEO4J_URI and _host_resolves(NEO4J_URI):
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            try:
                with driver.session() as session:
                    session.run(
                        "MERGE (u:User {name:$user}) "
                        "CREATE (c:Conversation {prompt:$prompt, response:$response, model:$model, version:$version, ts:$ts}) "
                        "CREATE (u)-[:HAD]->(c)",
                        payload
                    )
                try:
                    driver.close()
                except Exception:
                    pass
                logger.info("event=store_conversation_neo4j_success user=%s model=%s", user, model)
                return
            except Exception as e:
                logger.error("event=store_conversation_neo4j_failed user=%s model=%s error=%s", user, model, str(e))
                try:
                    driver.close()
                except Exception:
                    pass
    except Exception as e:
        logger.error("event=store_conversation_neo4j_unavailable error=%s", str(e))

    try:
        data = json.loads(_LOCAL_STORE.read_text())
        data.append(payload)
        _LOCAL_STORE.write_text(json.dumps(data, indent=2))
        logger.info("event=store_conversation_file_success user=%s model=%s path=%s", user, model, str(_LOCAL_STORE))
    except Exception as e:
        logger.error("event=store_conversation_file_failed error=%s", str(e))

def get_user_conversations(user: str, limit: int = 100) -> List[Dict]:
    results: List[Dict] = []
    
    logger.info("event=get_conversations_start user=%s limit=%s", user, limit)
    
    try:
        if _NEO4J_AVAILABLE and NEO4J_URI and _host_resolves(NEO4J_URI):
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            try:
                with driver.session() as session:
                    rows = session.run(
                        "MATCH (u:User {name:$user})-[:HAD]->(c:Conversation) RETURN c.prompt as prompt, c.response as response, c.model as model, c.version as version, c.ts as ts ORDER BY c.ts ASC",
                        {"user": user}
                    )
                    for r in rows:
                        results.append({"role": "user", "text": r["prompt"], "model": r.get("model"), "ts": r.get("ts")})
                        results.append({"role": "assistant", "text": r["response"], "model": r.get("model"), "ts": r.get("ts")})
                try:
                    driver.close()
                except Exception:
                    pass
                logger.info("event=get_conversations_neo4j_success user=%s count=%s", user, len(results))
                return results[-limit:]
            except Exception as e:
                logger.error("event=get_conversations_neo4j_failed user=%s error=%s", user, str(e))
                try:
                    driver.close()
                except Exception:
                    pass
    except Exception as e:
        logger.error("event=get_conversations_neo4j_unavailable error=%s", str(e))

    try:
        data = json.loads(_LOCAL_STORE.read_text())
        for item in data:
            if item.get("user") == user:
                results.append({"role": "user", "text": item.get("prompt", ""), "model": item.get("model"), "ts": item.get("ts")})
                results.append({"role": "assistant", "text": item.get("response", ""), "model": item.get("model"), "ts": item.get("ts")})
        logger.info("event=get_conversations_file_success user=%s count=%s path=%s", user, len(results), str(_LOCAL_STORE))
    except Exception as e:
        logger.error("event=get_conversations_file_failed error=%s", str(e))

    return results[-limit:]
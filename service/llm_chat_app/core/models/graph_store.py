import os
import json
import logging
import socket
from pathlib import Path
from typing import Optional
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
                logger.info("store_conversation neo4j write user=%s model=%s", user, model)
                return
            except Exception as e:
                logger.exception("store_conversation neo4j write failed error=%s", e)
                try:
                    driver.close()
                except Exception:
                    pass
    except Exception as e:
        logger.exception("store_conversation neo4j unavailable error=%s falling back to file store", e)

    try:
        data = json.loads(_LOCAL_STORE.read_text())
        data.append(payload)
        _LOCAL_STORE.write_text(json.dumps(data, indent=2))
        logger.info("store_conversation file write user=%s model=%s path=%s", user, model, str(_LOCAL_STORE))
    except Exception as e:
        logger.exception("store_conversation file write failed error=%s", e)

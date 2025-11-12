import logging
from neo4j import GraphDatabase
from config.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
logger = logging.getLogger(__name__)

_driver = None

def _driver():
    global _driver
    
    if _driver is None:
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return _driver

def store_conversation(user: str, message: str, response: str, model: str = "unknown", version: str = "unknown"):
    logger.info("graph_store.store_conversation user=%s message_len=%d", user, len(message) if message else 0)
    drv = _driver()
    with drv.session() as session:
        session.run("MERGE (u:User {name: $user}) CREATE (m:Message {text: $message, response: $response, ts: timestamp(), model:$model, model_version:$version}) MERGE (u)-[:SENT]->(m)", user=user, message=message, response=response, model=model, version=version)

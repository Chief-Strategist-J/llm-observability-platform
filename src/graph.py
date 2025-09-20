import os, uuid, datetime
from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph

load_dotenv()

def get_graph():
    uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    auth = os.getenv("NEO4J_AUTH", "neo4j/Scaibu@123")

    user, password = auth.split("/", 1)
    g = Neo4jGraph(url=uri, username=user, password=password)
    _ = g.query("RETURN 1 AS ok")
    return g

graph = get_graph()

# --- Conversation memory helpers ---

def init_chat(chat_id: str) -> None:
    """Ensure a chat session node exists."""
    cypher = """
    MERGE (c:Chat {id: $chat_id})
    ON CREATE SET c.started_at = datetime()
    """
    graph.query(cypher, {"chat_id": chat_id})


def store_message(chat_id: str, role: str, content: str) -> str:
    """Store a message node and link it in sequence."""
    msg_id = str(uuid.uuid4())
    # Ensure Neo4j-compatible ISO format (seconds precision)
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    cypher = """
    MERGE (c:Chat {id: $chat_id})
      ON CREATE SET c.started_at = datetime()
    CREATE (m:Message {
        id: $msg_id,
        role: $role,
        content: $content,
        timestamp: datetime($timestamp)
    })
    MERGE (c)-[:HAS_MESSAGE]->(m)
    WITH c,m
    OPTIONAL MATCH (c)-[:HAS_MESSAGE]->(prev:Message)
      WHERE NOT (prev)-[:NEXT]->() AND prev.id <> m.id
    FOREACH (_ IN CASE WHEN prev IS NULL THEN [] ELSE [1] END |
      MERGE (prev)-[:NEXT]->(m)
    )
    RETURN m.id AS id
    """
    graph.query(cypher, {
        "chat_id": chat_id,
        "msg_id": msg_id,
        "role": role,
        "content": content,
        "timestamp": timestamp,
    })
    return msg_id


def fetch_conversation(chat_id: str):
    """Fetch ordered messages for a chat in correct sequence."""
    cypher = """
    MATCH (c:Chat {id:$chat_id})-[:HAS_MESSAGE]->(start:Message)
    WHERE NOT ()-[:NEXT]->(start)   // find first message (no incoming NEXT)
    OPTIONAL MATCH path=(start)-[:NEXT*0..]->(m:Message)
    WITH m
    RETURN m.id AS id, m.role AS role, m.content AS content, m.timestamp AS ts
    ORDER BY ts ASC
    """
    return graph.query(cypher, {"chat_id": chat_id})

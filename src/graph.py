import os
import re
import uuid
import datetime
from typing import List, Dict, Tuple

from dotenv import load_dotenv
from langchain_neo4j import Neo4jGraph

load_dotenv()


# ----------------------------
# Connection & Constraints
# ----------------------------

def get_graph():
    uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    auth = os.getenv("NEO4J_AUTH", "neo4j/Scaibu@123")

    user, password = auth.split("/", 1)
    g = Neo4jGraph(url=uri, username=user, password=password)
    _ = g.query("RETURN 1 AS ok")
    return g


graph = get_graph()


def ensure_constraints() -> None:
    """Create required uniqueness constraints (runs safely on Neo4j 4.x/5.x)."""
    v5 = [
        "CREATE CONSTRAINT chat_id IF NOT EXISTS FOR (c:Chat) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT message_id IF NOT EXISTS FOR (m:Message) REQUIRE m.id IS UNIQUE",
        "CREATE CONSTRAINT topic_name IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE",
        "CREATE CONSTRAINT ent_name_type IF NOT EXISTS FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE",
    ]
    v44 = [
        "CREATE CONSTRAINT chat_id IF NOT EXISTS ON (c:Chat) ASSERT c.id IS UNIQUE",
        "CREATE CONSTRAINT message_id IF NOT EXISTS ON (m:Message) ASSERT m.id IS UNIQUE",
        "CREATE CONSTRAINT topic_name IF NOT EXISTS ON (t:Topic) ASSERT t.name IS UNIQUE",
        "CREATE CONSTRAINT ent_name_type IF NOT EXISTS ON (e:Entity) ASSERT (e.name, e.type) IS UNIQUE",
    ]

    for i in range(len(v5)):
        try:
            graph.query(v5[i])   # Neo4j 5.x / 4.4+ style
        except Exception:
            try:
                graph.query(v44[i])  # Neo4j 4.x fallback
            except Exception:
                # Ignore if constraint already exists or syntax unsupported.
                pass


ensure_constraints()


# ----------------------------
# Conversation memory helpers
# ----------------------------

def init_chat(chat_id: str) -> None:
    """Ensure a chat session node exists."""
    cypher = """
    MERGE (c:Chat {id: $chat_id})
    ON CREATE SET c.started_at = datetime()
    """
    graph.query(cypher, {"chat_id": chat_id})


def store_message(chat_id: str, role: str, content: str) -> str:
    """Store a message node and link it in sequence (unchanged signature)."""
    msg_id = str(uuid.uuid4())
    # Neo4j-friendly ISO (seconds precision)
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
    graph.query(
        cypher,
        {
            "chat_id": chat_id,
            "msg_id": msg_id,
            "role": role,
            "content": content,
            "timestamp": timestamp,
        },
    )
    return msg_id


def fetch_conversation(chat_id: str):
    """Fetch ordered messages for a chat in correct sequence."""
    cypher = """
    MATCH (c:Chat {id:$chat_id})-[:HAS_MESSAGE]->(start:Message)
    WHERE NOT ()-[:NEXT]->(start)   // first message has no incoming NEXT
    OPTIONAL MATCH path=(start)-[:NEXT*0..]->(m:Message)
    WITH m
    RETURN m.id AS id, m.role AS role, m.content AS content, m.timestamp AS ts
    ORDER BY ts ASC
    """
    return graph.query(cypher, {"chat_id": chat_id})


# -------------------------------------------------
# Enrichment (Topics & Entities) - Additive helpers
# -------------------------------------------------

def tag_message_topics(msg_id: str, topics: List[str]) -> None:
    """Attach topics to message and chat; count usage per chat."""
    if not topics:
        return
    cypher = """
    MATCH (m:Message {id:$msg_id})<-[:HAS_MESSAGE]-(c:Chat)
    UNWIND $topics AS topicName
    WITH m, c, trim(toLower(topicName)) AS tn
    WHERE tn <> ""
    MERGE (t:Topic {name: tn})
    MERGE (m)-[r1:OF_TOPIC]->(t)
      ON CREATE SET r1.first_seen = datetime()
    MERGE (c)-[r2:HAS_TOPIC]->(t)
      ON CREATE SET r2.first_seen = datetime(), r2.count = 1
      ON MATCH  SET r2.last_seen  = datetime(), r2.count = coalesce(r2.count,0) + 1
    """
    graph.query(cypher, {"msg_id": msg_id, "topics": topics})


def tag_message_entities(msg_id: str, entities: List[Dict[str, str]]) -> None:
    """Attach entities to message and chat; count usage per chat."""
    if not entities:
        return
    cypher = """
    MATCH (m:Message {id:$msg_id})<-[:HAS_MESSAGE]-(c:Chat)
    UNWIND $entities AS e
    WITH m, c, trim(e.name) AS n, toUpper(trim(e.type)) AS t
    WHERE n <> "" AND t <> ""
    MERGE (ent:Entity {name:n, type:t})
    MERGE (m)-[r:MENTIONS]->(ent)
      ON CREATE SET r.first_seen = datetime()
    MERGE (c)-[r2:HAS_ENTITY]->(ent)
      ON CREATE SET r2.first_seen = datetime(), r2.count = 1
      ON MATCH  SET r2.last_seen  = datetime(), r2.count = coalesce(r2.count,0) + 1
    """
    graph.query(cypher, {"msg_id": msg_id, "entities": entities})


# ----------------------------
# Lightweight auto extraction
# ----------------------------

_GENRES = {
    "action", "adventure", "animation", "anime", "biopic", "comedy", "crime",
    "documentary", "drama", "family", "fantasy", "horror", "mystery",
    "romance", "sci-fi", "science fiction", "sports", "thriller", "war",
    "western", "superhero", "musical"
}

_THEMES = {
    "box office", "awards", "oscars", "soundtrack", "cinematography",
    "trailer", "release date", "streaming", "imax", "remake", "sequel",
    "prequel", "cast", "director", "screenplay"
}

_PLATFORMS = {
    "netflix", "prime video", "amazon prime", "disney+", "hulu", "max",
    "apple tv+", "hotstar"
}

_STOPWORDS = {
    "The", "A", "An", "And", "Or", "But", "If", "In", "On", "At", "To", "Of",
    "For", "By", "With", "From", "As", "Is", "Are", "Be", "It", "This", "That",
    "These", "Those", "I", "You", "We", "They", "He", "She", "Them", "Us"
}


def _guess_topics(text: str) -> List[str]:
    s = text.lower()
    topics = set()

    # multi-word themes/platforms first (to catch phrases)
    for phrase in _THEMES | _PLATFORMS:
        if phrase in s:
            topics.add(phrase)

    # genres (single tokens)
    tokens = re.findall(r"[a-zA-Z][a-zA-Z\-\+]+", s)
    for tok in tokens:
        if tok in _GENRES:
            topics.add(tok)

    return sorted(topics)


def _extract_entities(text: str) -> List[Dict[str, str]]:
    entities: List[Dict[str, str]] = []
    seen: set[Tuple[str, str]] = set()

    # quoted titles -> MOVIE (heuristic)
    for m in re.finditer(r"[“\"']([^\"“”']{2,})[\"”']", text):
        name = m.group(1).strip()
        if len(name) > 1:
            key = (name, "MOVIE")
            if key not in seen:
                entities.append({"name": name, "type": "MOVIE"})
                seen.add(key)

    # Title Case sequences (2–6 words) -> PERSON/MOVIE (weak heuristic)
    # We'll default to MOVIE unless a role word is nearby
    role_words = {"director", "actor", "actress", "writer", "composer"}
    words = text.split()
    # scan window
    i = 0
    while i < len(words):
        w = re.sub(r"[^\w\-]", "", words[i])
        if w and w[0].isupper() and w not in _STOPWORDS:
            j = i + 1
            chunk = [w]
            while j < len(words):
                wj = re.sub(r"[^\w\-]", "", words[j])
                if wj and wj[0].isupper() and wj not in _STOPWORDS:
                    chunk.append(wj)
                    j += 1
                    if len(chunk) >= 6:
                        break
                else:
                    break
            if len(chunk) >= 2:
                name = " ".join(chunk)
                # decide type by context (very light)
                window = " ".join(words[max(0, i-3):min(len(words), j+3)]).lower()
                etype = "PERSON" if any(rw in window for rw in role_words) else "MOVIE"
                key = (name, etype)
                if key not in seen:
                    entities.append({"name": name, "type": etype})
                    seen.add(key)
                i = j
                continue
        i += 1

    return entities


def enrich_message(msg_id: str, content: str) -> None:
    """
    Heuristic enrichment: detect topics & entities from content and upsert
    into the graph. Safe no-op on error.
    """
    try:
        topics = _guess_topics(content)
        entities = _extract_entities(content)
        if topics:
            tag_message_topics(msg_id, topics)
        if entities:
            tag_message_entities(msg_id, entities)
    except Exception:
        # Never break chat if enrichment fails
        pass

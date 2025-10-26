"""Knowledge Graph Service API.

This module provides a FastAPI-based REST API for the Knowledge Graph service, including
endpoints for content ingestion, querying, and memory management.

"""

from datetime import datetime
import logging
import os
import sys
from typing import Any

from adapters.chunking.semantic_chunker import SemanticChunker
from adapters.embedding_model.sentence_transformer import SentenceTransformerEmbedding
from adapters.entity_extractor.spacy_extractor import SpacyEntityExtractor
from adapters.graph_store.neo4j_store import Neo4jGraphStore
from adapters.memory_store.neo4j_memory import Neo4jMemoryStore
from core.domain.models import IngestionRequest, QueryContext
from core.usecases.ingest_content import ingest_content
from core.usecases.manage_memory import decay_old_memories, store_interaction
from core.usecases.reason_query import reason_query
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("logs/app.log")],
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Knowledge Graph SDK",
    description="Scalable Knowledge Graph with Memory & Reasoning",
    version="1.0.0",
)

# Global adapters
GRAPH_STORE = None
EMBEDDING_MODEL = None
CHUNKING_ADAPTER = None
ENTITY_EXTRACTOR = None
MEMORY_STORE = None
CONFIG = {}


@app.on_event("startup")
async def startup():
    """
    Initialize the Knowledge Graph SDK on startup.
    """
    global \
        GRAPH_STORE, \
        EMBEDDING_MODEL, \
        CHUNKING_ADAPTER, \
        ENTITY_EXTRACTOR, \
        MEMORY_STORE, \
        CONFIG

    logger.info("Starting Knowledge Graph SDK...")

    # Load configuration
    with open("config/kg_config.yaml") as f:
        CONFIG = yaml.safe_load(f)

    # Initialize adapters
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "changeme123")

    GRAPH_STORE = Neo4jGraphStore(neo4j_uri, neo4j_user, neo4j_password)
    logger.info("Neo4j Graph Store initialized")

    embedding_model_name = os.getenv("EMBEDDING_MODEL", CONFIG["embedding"]["model"])
    EMBEDDING_MODEL = SentenceTransformerEmbedding(embedding_model_name)
    logger.info(f"Embedding model loaded: {embedding_model_name}")

    CHUNKING_ADAPTER = SemanticChunker(
        chunk_size=CONFIG["chunking"]["chunk_size"],
        overlap=CONFIG["chunking"]["chunk_overlap"],
    )
    logger.info("Chunking adapter initialized")

    ENTITY_EXTRACTOR = SpacyEntityExtractor(
        model_name=CONFIG["entity_extraction"]["spacy_model"],
        entity_types=CONFIG["entity_extraction"]["entity_types"],
    )
    logger.info("Entity extractor initialized")

    MEMORY_STORE = Neo4jMemoryStore(neo4j_uri, neo4j_user, neo4j_password)
    logger.info("Memory store initialized")

    logger.info("Knowledge Graph SDK ready!")


@app.on_event("shutdown")
async def shutdown():
    """
    Clean up resources on application shutdown.
    """
    if GRAPH_STORE:
        await GRAPH_STORE.close()
    if MEMORY_STORE:
        await MEMORY_STORE.close()
    logger.info("Knowledge Graph SDK shutdown complete")


@app.get("/health")
async def health():
    """
    Get the health status of the Knowledge Graph service.
    """
    return {
        "status": "healthy",
        "service": "kg-service",
        "timestamp": datetime.utcnow().isoformat(),
        "config": {
            "embedding_dim": EMBEDDING_MODEL.get_dimension() if EMBEDDING_MODEL else 0,
            "chunk_size": CONFIG.get("chunking", {}).get("chunk_size", 0),
        },
    }


class IngestContentRequest(BaseModel):
    content: str = Field(..., description="Content to ingest into knowledge graph")
    source_id: str = Field(..., description="Unique identifier for the content source")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


@app.post("/ingest")
async def ingest_endpoint(request: IngestContentRequest):
    """
    Ingest content into the knowledge graph.
    """
    try:
        logger.info(f"Ingesting content from source: {request.source_id}")

        ingestion_request = IngestionRequest(
            content=request.content,
            source_id=request.source_id,
            metadata=request.metadata,
        )

        response = await ingest_content(
            ingestion_request,
            CHUNKING_ADAPTER,
            EMBEDDING_MODEL,
            ENTITY_EXTRACTOR,
            GRAPH_STORE,
            MEMORY_STORE,
        )

        logger.info(f"Ingestion complete: {response.chunks_created} chunks")

        return {
            "status": response.status,
            "source_id": response.source_id,
            "chunks_created": response.chunks_created,
            "entities_extracted": response.entities_extracted,
            "relations_extracted": response.relations_extracted,
        }

    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class QueryRequest(BaseModel):
    query: str = Field(..., description="Query text")
    max_hops: int = Field(default=3, description="Maximum graph traversal hops")
    limit: int = Field(default=10, description="Maximum results to return")
    filters: dict[str, Any] = Field(default_factory=dict, description="Query filters")


@app.post("/query")
async def query_endpoint(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    Query the knowledge graph for information.
    """
    try:
        logger.info(f"Processing query: {request.query[:100]}...")

        query_context = QueryContext(
            query=request.query,
            max_hops=request.max_hops,
            limit=request.limit,
            filters=request.filters,
        )

        result = await reason_query(
            query_context, EMBEDDING_MODEL, GRAPH_STORE, MEMORY_STORE
        )

        background_tasks.add_task(
            store_interaction,
            request.query,
            result.answer,
            MEMORY_STORE,
            EMBEDDING_MODEL,
        )

        logger.info(f"Query processed with confidence: {result.confidence}")

        return {
            "answer": result.answer,
            "confidence": result.confidence,
            "entities": [
                {"name": e.name, "type": e.entity_type, "confidence": e.confidence}
                for e in result.entities
            ],
            "relations": [
                {
                    "source": r.source,
                    "target": r.target,
                    "type": r.relation_type,
                    "confidence": r.confidence,
                }
                for r in result.relations
            ],
            "reasoning_path": result.reasoning_path,
            "sources": result.sources,
        }

    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class CypherQueryRequest(BaseModel):
    query: str = Field(..., description="Cypher query to execute")
    params: dict[str, Any] = Field(default_factory=dict, description="Query parameters")


@app.post("/cypher")
async def cypher_query(request: CypherQueryRequest):
    """
    Execute a raw Cypher query against the graph database.
    """
    try:
        logger.info("Executing Cypher query")
        results = await GRAPH_STORE.query_cypher(request.query, request.params)
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Cypher query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/decay")
async def decay_memory():
    """
    Decay old memories to maintain memory store efficiency.
    """
    try:
        count = await decay_old_memories(MEMORY_STORE)
        logger.info(f"Decayed {count} old memories")
        return {"status": "success", "decayed_count": count}
    except Exception as e:
        logger.error(f"Memory decay failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """
    Get statistics about the knowledge graph.
    """
    try:
        node_count_query = "MATCH (n) RETURN count(n) as count"
        relation_count_query = "MATCH ()-[r]->() RETURN count(r) as count"
        memory_count_query = "MATCH (m:Memory) RETURN count(m) as count"

        node_result = await GRAPH_STORE.query_cypher(node_count_query, {})
        relation_result = await GRAPH_STORE.query_cypher(relation_count_query, {})
        memory_result = await GRAPH_STORE.query_cypher(memory_count_query, {})

        return {
            "nodes": node_result[0]["count"] if node_result else 0,
            "relations": relation_result[0]["count"] if relation_result else 0,
            "memories": memory_result[0]["count"] if memory_result else 0,
            "embedding_dimension": EMBEDDING_MODEL.get_dimension(),
        }
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class EmbedRequest(BaseModel):
    text: str = Field(..., description="Text to embed")


@app.post("/embed")
async def embed_text(request: EmbedRequest):
    """
    Generate embeddings for the given text.
    """
    try:
        embedding = await EMBEDDING_MODEL.embed_text(request.text)
        return {"embedding": embedding, "dimension": len(embedding)}
    except Exception as e:
        logger.error(f"Embedding failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import yaml
import logging
import sys
from datetime import datetime

from core.domain.models import IngestionRequest, QueryContext
from core.usecases.ingest_content import ingest_content
from core.usecases.reason_query import reason_query
from core.usecases.manage_memory import store_interaction, decay_old_memories

from adapters.graph_store.neo4j_store import Neo4jGraphStore
from adapters.embedding_model.sentence_transformer import SentenceTransformerEmbedding
from adapters.chunking.semantic_chunker import SemanticChunker
from adapters.entity_extractor.spacy_extractor import SpacyEntityExtractor
from adapters.memory_store.neo4j_memory import Neo4jMemoryStore

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/app.log')
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Knowledge Graph SDK",
    description="Scalable Knowledge Graph with Memory & Reasoning",
    version="1.0.0"
)

# Global adapters
graph_store = None
embedding_model = None
chunking_adapter = None
entity_extractor = None
memory_store = None
config = {}

@app.on_event("startup")
async def startup():
    global graph_store, embedding_model, chunking_adapter, entity_extractor, memory_store, config
    
    logger.info("Starting Knowledge Graph SDK...")
    
    # Load configuration
    with open("config/kg_config.yaml") as f:
        config = yaml.safe_load(f)
    
    # Initialize adapters
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "changeme123")
    
    graph_store = Neo4jGraphStore(neo4j_uri, neo4j_user, neo4j_password)
    logger.info("Neo4j Graph Store initialized")
    
    embedding_model_name = os.getenv("EMBEDDING_MODEL", config["embedding"]["model"])
    embedding_model = SentenceTransformerEmbedding(embedding_model_name)
    logger.info(f"Embedding model loaded: {embedding_model_name}")
    
    chunking_adapter = SemanticChunker(
        chunk_size=config["chunking"]["chunk_size"],
        overlap=config["chunking"]["chunk_overlap"]
    )
    logger.info("Chunking adapter initialized")
    
    entity_extractor = SpacyEntityExtractor(
        model_name=config["entity_extraction"]["spacy_model"],
        entity_types=config["entity_extraction"]["entity_types"]
    )
    logger.info("Entity extractor initialized")
    
    memory_store = Neo4jMemoryStore(neo4j_uri, neo4j_user, neo4j_password)
    logger.info("Memory store initialized")
    
    logger.info("Knowledge Graph SDK ready!")

@app.on_event("shutdown")
async def shutdown():
    if graph_store:
        await graph_store.close()
    if memory_store:
        await memory_store.close()
    logger.info("Knowledge Graph SDK shutdown complete")

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "kg-service",
        "timestamp": datetime.utcnow().isoformat(),
        "config": {
            "embedding_dim": embedding_model.get_dimension() if embedding_model else 0,
            "chunk_size": config.get("chunking", {}).get("chunk_size", 0)
        }
    }

class IngestContentRequest(BaseModel):
    content: str = Field(..., description="Content to ingest into knowledge graph")
    source_id: str = Field(..., description="Unique identifier for the content source")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

@app.post("/ingest")
async def ingest_endpoint(request: IngestContentRequest):
    try:
        logger.info(f"Ingesting content from source: {request.source_id}")
        
        ingestion_request = IngestionRequest(
            content=request.content,
            source_id=request.source_id,
            metadata=request.metadata
        )
        
        response = await ingest_content(
            ingestion_request,
            chunking_adapter,
            embedding_model,
            entity_extractor,
            graph_store,
            memory_store
        )
        
        logger.info(f"Ingestion complete: {response.chunks_created} chunks")
        
        return {
            "status": response.status,
            "source_id": response.source_id,
            "chunks_created": response.chunks_created,
            "entities_extracted": response.entities_extracted,
            "relations_extracted": response.relations_extracted
        }
    
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class QueryRequest(BaseModel):
    query: str = Field(..., description="Query text")
    max_hops: int = Field(default=3, description="Maximum graph traversal hops")
    limit: int = Field(default=10, description="Maximum results to return")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Query filters")

@app.post("/query")
async def query_endpoint(request: QueryRequest, background_tasks: BackgroundTasks):
    try:
        logger.info(f"Processing query: {request.query[:100]}...")
        
        query_context = QueryContext(
            query=request.query,
            max_hops=request.max_hops,
            limit=request.limit,
            filters=request.filters
        )
        
        result = await reason_query(
            query_context,
            embedding_model,
            graph_store,
            memory_store
        )
        
        background_tasks.add_task(
            store_interaction,
            request.query,
            result.answer,
            memory_store,
            embedding_model
        )
        
        logger.info(f"Query processed with confidence: {result.confidence}")
        
        return {
            "answer": result.answer,
            "confidence": result.confidence,
            "entities": [
                {
                    "name": e.name,
                    "type": e.entity_type,
                    "confidence": e.confidence
                } for e in result.entities
            ],
            "relations": [
                {
                    "source": r.source,
                    "target": r.target,
                    "type": r.relation_type,
                    "confidence": r.confidence
                } for r in result.relations
            ],
            "reasoning_path": result.reasoning_path,
            "sources": result.sources
        }
    
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class CypherQueryRequest(BaseModel):
    query: str = Field(..., description="Cypher query to execute")
    params: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")

@app.post("/cypher")
async def cypher_query(request: CypherQueryRequest):
    try:
        logger.info(f"Executing Cypher query")
        results = await graph_store.query_cypher(request.query, request.params)
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Cypher query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/decay")
async def decay_memory():
    try:
        count = await decay_old_memories(memory_store)
        logger.info(f"Decayed {count} old memories")
        return {"status": "success", "decayed_count": count}
    except Exception as e:
        logger.error(f"Memory decay failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    try:
        node_count_query = "MATCH (n) RETURN count(n) as count"
        relation_count_query = "MATCH ()-[r]->() RETURN count(r) as count"
        memory_count_query = "MATCH (m:Memory) RETURN count(m) as count"
        
        node_result = await graph_store.query_cypher(node_count_query, {})
        relation_result = await graph_store.query_cypher(relation_count_query, {})
        memory_result = await graph_store.query_cypher(memory_count_query, {})
        
        return {
            "nodes": node_result[0]["count"] if node_result else 0,
            "relations": relation_result[0]["count"] if relation_result else 0,
            "memories": memory_result[0]["count"] if memory_result else 0,
            "embedding_dimension": embedding_model.get_dimension()
        }
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class EmbedRequest(BaseModel):
    text: str = Field(..., description="Text to embed")

@app.post("/embed")
async def embed_text(request: EmbedRequest):
    try:
        embedding = await embedding_model.embed_text(request.text)
        return {"embedding": embedding, "dimension": len(embedding)}
    except Exception as e:
        logger.error(f"Embedding failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

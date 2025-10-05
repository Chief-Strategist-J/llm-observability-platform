from typing import List
import uuid
from datetime import datetime
from core.domain.models import (
    IngestionRequest, IngestionResponse, GraphNode, GraphRelation, 
    NodeType, Memory, MemoryType
)
from core.ports.chunking import ChunkingPort
from core.ports.embedding_model import EmbeddingModelPort
from core.ports.entity_extractor import EntityExtractorPort
from core.ports.graph_store import GraphStorePort
from core.ports.memory_store import MemoryStorePort

async def ingest_content(
    request: IngestionRequest,
    chunking: ChunkingPort,
    embedding: EmbeddingModelPort,
    extractor: EntityExtractorPort,
    graph_store: GraphStorePort,
    memory_store: MemoryStorePort
) -> IngestionResponse:
    # 1. Chunk the content
    chunks = await chunking.chunk_text(request.content, request.metadata)
    
    # 2. Create document node
    doc_id = f"doc_{request.source_id}"
    doc_embedding = await embedding.embed_text(request.content[:500])
    
    doc_node = GraphNode(
        id=doc_id,
        label=NodeType.DOCUMENT,
        properties={
            "source_id": request.source_id,
            "created_at": datetime.utcnow().isoformat(),
            **request.metadata
        },
        embedding=doc_embedding
    )
    await graph_store.create_node(doc_node)
    
    entities_count = 0
    relations_count = 0
    
    # 3. Process each chunk
    for chunk in chunks:
        # Embed chunk
        chunk.embedding = await embedding.embed_text(chunk.text)
        
        # Create chunk node
        chunk_node = GraphNode(
            id=chunk.chunk_id,
            label=NodeType.CHUNK,
            properties={
                "text": chunk.text,
                "metadata": chunk.metadata
            },
            embedding=chunk.embedding
        )
        await graph_store.create_node(chunk_node)
        
        # Link chunk to document
        await graph_store.create_relation(GraphRelation(
            source_id=doc_id,
            target_id=chunk.chunk_id,
            relation_type="HAS_CHUNK",
            properties={}
        ))
        
        # 4. Extract entities from chunk
        entities = await extractor.extract_entities(chunk.text)
        
        for entity in entities:
            # Embed entity
            entity.embedding = await embedding.embed_text(entity.name)
            
            # Create entity node
            entity_id = f"entity_{uuid.uuid4().hex[:8]}_{entity.name.replace(' ', '_')}"
            entity_node = GraphNode(
                id=entity_id,
                label=NodeType.ENTITY,
                properties={
                    "name": entity.name,
                    "type": entity.entity_type,
                    "confidence": entity.confidence,
                    **entity.properties
                },
                embedding=entity.embedding
            )
            await graph_store.create_node(entity_node)
            entities_count += 1
            
            # Link entity to chunk
            await graph_store.create_relation(GraphRelation(
                source_id=chunk.chunk_id,
                target_id=entity_id,
                relation_type="MENTIONS",
                properties={"confidence": entity.confidence}
            ))
        
        # 5. Extract relations
        relations = await extractor.extract_relations(chunk.text, entities)
        relations_count += len(relations)
    
    # 6. Store in long-term memory
    memory = Memory(
        id=f"mem_{doc_id}",
        content=request.content[:1000],
        memory_type=MemoryType.LONG_TERM,
        importance=0.8,
        created_at=datetime.utcnow(),
        accessed_at=datetime.utcnow(),
        embedding=doc_embedding,
        metadata=request.metadata
    )
    await memory_store.store_memory(memory)
    
    return IngestionResponse(
        source_id=request.source_id,
        chunks_created=len(chunks),
        entities_extracted=entities_count,
        relations_extracted=relations_count,
        status="success"
    )

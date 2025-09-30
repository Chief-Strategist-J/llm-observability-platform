#!/usr/bin/env bash
set -euo pipefail

PROJECT="kg-service"

echo "🚀 Setting up Knowledge Graph Service..."

# Remove existing directory
if [ -d "$PROJECT" ]; then
    echo "Removing existing $PROJECT directory..."
    rm -rf "$PROJECT"
fi

# Create ALL directory structure first
echo "Creating directory structure..."
mkdir -p "$PROJECT"
mkdir -p "$PROJECT/adapters/graph_store"
mkdir -p "$PROJECT/adapters/embedding_model"
mkdir -p "$PROJECT/adapters/chunking"
mkdir -p "$PROJECT/adapters/entity_extractor"
mkdir -p "$PROJECT/adapters/memory_store"
mkdir -p "$PROJECT/core/domain"
mkdir -p "$PROJECT/core/ports"
mkdir -p "$PROJECT/core/usecases"
mkdir -p "$PROJECT/api"
mkdir -p "$PROJECT/config"
mkdir -p "$PROJECT/data/neo4j/data"
mkdir -p "$PROJECT/data/neo4j/logs"
mkdir -p "$PROJECT/logs"

echo "✅ Directory structure created"

# Now create all files
echo "Creating configuration files..."

# Requirements
cat > "$PROJECT/requirements.txt" << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.3
httpx==0.25.2
python-multipart==0.0.6
neo4j==5.14.1
sentence-transformers==2.2.2
spacy==3.7.2
numpy==1.24.3
torch==2.1.0
PyYAML==6.0.1
python-dateutil==2.8.2
tiktoken==0.5.1
EOF

# Environment template
cat > "$PROJECT/.env.example" << 'EOF'
# Neo4j Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=changeme123

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Memory Configuration
SHORT_TERM_MEMORY_LIMIT=50
LONG_TERM_MEMORY_DECAY_DAYS=30

# Chunking Configuration
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# API Configuration
HOST=0.0.0.0
PORT=8002

# LLM Provider for Entity Extraction (optional)
LLM_PROVIDER_URL=http://localhost:8000/generate
EOF

# Configuration YAML
cat > "$PROJECT/config/kg_config.yaml" << 'EOF'
chunking:
  strategy: "semantic"
  chunk_size: 512
  chunk_overlap: 50
  min_chunk_size: 100

embedding:
  model: "sentence-transformers/all-MiniLM-L6-v2"
  dimension: 384
  batch_size: 32

entity_extraction:
  spacy_model: "en_core_web_sm"
  min_confidence: 0.5
  entity_types:
    - PERSON
    - ORG
    - GPE
    - DATE
    - MONEY
    - PRODUCT
    - EVENT

relation_extraction:
  max_distance: 3
  min_confidence: 0.6
  relation_types:
    - WORKS_FOR
    - LOCATED_IN
    - PART_OF
    - RELATED_TO
    - CREATED_BY
    - HAPPENS_ON

memory:
  short_term:
    max_items: 50
    ttl_seconds: 3600
  long_term:
    decay_days: 30
    importance_threshold: 0.7

reasoning:
  max_hops: 3
  similarity_threshold: 0.75
  max_results: 10
EOF

echo "Creating core domain files..."

# Core __init__ files
touch "$PROJECT/core/__init__.py"
touch "$PROJECT/core/domain/__init__.py"
touch "$PROJECT/core/ports/__init__.py"
touch "$PROJECT/core/usecases/__init__.py"
touch "$PROJECT/adapters/__init__.py"
touch "$PROJECT/adapters/graph_store/__init__.py"
touch "$PROJECT/adapters/embedding_model/__init__.py"
touch "$PROJECT/adapters/chunking/__init__.py"
touch "$PROJECT/adapters/entity_extractor/__init__.py"
touch "$PROJECT/adapters/memory_store/__init__.py"
touch "$PROJECT/api/__init__.py"

# Core Domain Models
cat > "$PROJECT/core/domain/models.py" << 'EOF'
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MemoryType(Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"

class NodeType(Enum):
    ENTITY = "Entity"
    CONCEPT = "Concept"
    EVENT = "Event"
    DOCUMENT = "Document"
    CHUNK = "Chunk"

@dataclass
class Chunk:
    text: str
    chunk_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None

@dataclass
class Entity:
    name: str
    entity_type: str
    confidence: float
    properties: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None

@dataclass
class Relation:
    source: str
    target: str
    relation_type: str
    confidence: float
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GraphNode:
    id: str
    label: NodeType
    properties: Dict[str, Any]
    embedding: Optional[List[float]] = None

@dataclass
class GraphRelation:
    source_id: str
    target_id: str
    relation_type: str
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Memory:
    id: str
    content: str
    memory_type: MemoryType
    importance: float
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QueryContext:
    query: str
    embedding: Optional[List[float]] = None
    max_hops: int = 3
    limit: int = 10
    filters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ReasoningResult:
    answer: str
    entities: List[Entity]
    relations: List[Relation]
    reasoning_path: List[str]
    confidence: float
    sources: List[str]

@dataclass
class IngestionRequest:
    content: str
    source_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IngestionResponse:
    source_id: str
    chunks_created: int
    entities_extracted: int
    relations_extracted: int
    status: str
EOF

echo "Creating core ports..."

# Core Ports
cat > "$PROJECT/core/ports/graph_store.py" << 'EOF'
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from core.domain.models import GraphNode, GraphRelation

class GraphStorePort(ABC):
    @abstractmethod
    async def create_node(self, node: GraphNode) -> str:
        pass
    
    @abstractmethod
    async def create_relation(self, relation: GraphRelation) -> bool:
        pass
    
    @abstractmethod
    async def find_similar_nodes(self, embedding: List[float], limit: int) -> List[GraphNode]:
        pass
    
    @abstractmethod
    async def traverse_graph(self, start_node_id: str, max_hops: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        pass
    
    @abstractmethod
    async def query_cypher(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass
EOF

cat > "$PROJECT/core/ports/embedding_model.py" << 'EOF'
from abc import ABC, abstractmethod
from typing import List

class EmbeddingModelPort(ABC):
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        pass
EOF

cat > "$PROJECT/core/ports/chunking.py" << 'EOF'
from abc import ABC, abstractmethod
from typing import List
from core.domain.models import Chunk

class ChunkingPort(ABC):
    @abstractmethod
    async def chunk_text(self, text: str, metadata: dict) -> List[Chunk]:
        pass
EOF

cat > "$PROJECT/core/ports/entity_extractor.py" << 'EOF'
from abc import ABC, abstractmethod
from typing import List
from core.domain.models import Entity, Relation

class EntityExtractorPort(ABC):
    @abstractmethod
    async def extract_entities(self, text: str) -> List[Entity]:
        pass
    
    @abstractmethod
    async def extract_relations(self, text: str, entities: List[Entity]) -> List[Relation]:
        pass
EOF

cat > "$PROJECT/core/ports/memory_store.py" << 'EOF'
from abc import ABC, abstractmethod
from typing import List
from core.domain.models import Memory, MemoryType

class MemoryStorePort(ABC):
    @abstractmethod
    async def store_memory(self, memory: Memory) -> str:
        pass
    
    @abstractmethod
    async def retrieve_memories(self, query_embedding: List[float], memory_type: MemoryType, limit: int) -> List[Memory]:
        pass
    
    @abstractmethod
    async def update_memory_access(self, memory_id: str) -> bool:
        pass
    
    @abstractmethod
    async def decay_memories(self) -> int:
        pass
EOF

echo "Creating use cases..."

# Core Usecases
cat > "$PROJECT/core/usecases/ingest_content.py" << 'EOF'
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
EOF

cat > "$PROJECT/core/usecases/reason_query.py" << 'EOF'
from core.domain.models import QueryContext, ReasoningResult, MemoryType, Entity, Relation
from core.ports.embedding_model import EmbeddingModelPort
from core.ports.graph_store import GraphStorePort
from core.ports.memory_store import MemoryStorePort

async def reason_query(
    context: QueryContext,
    embedding: EmbeddingModelPort,
    graph_store: GraphStorePort,
    memory_store: MemoryStorePort
) -> ReasoningResult:
    # 1. Embed the query
    query_embedding = await embedding.embed_text(context.query)
    context.embedding = query_embedding
    
    # 2. Retrieve relevant memories
    short_term_memories = await memory_store.retrieve_memories(
        query_embedding, MemoryType.SHORT_TERM, limit=10
    )
    
    long_term_memories = await memory_store.retrieve_memories(
        query_embedding, MemoryType.LONG_TERM, limit=20
    )
    
    # 3. Find similar nodes in graph
    similar_nodes = await graph_store.find_similar_nodes(
        query_embedding, limit=context.limit
    )
    
    # 4. Traverse graph from relevant nodes
    reasoning_path = []
    entities = []
    relations = []
    sources = []
    
    for node in similar_nodes[:5]:
        traversal = await graph_store.traverse_graph(
            node.id, context.max_hops, context.filters
        )
        reasoning_path.append(f"Traversed from {node.id}")
    
    # 5. Combine information
    answer_parts = []
    
    if short_term_memories:
        answer_parts.append("Recent context: " + short_term_memories[0].content[:200])
    
    if similar_nodes:
        answer_parts.append(f"Found {len(similar_nodes)} relevant nodes")
    
    answer = " | ".join(answer_parts) if answer_parts else "No sufficient information found"
    
    # 6. Calculate confidence
    confidence = min(
        (len(similar_nodes) * 0.4 + len(short_term_memories) * 0.6) / 10,
        1.0
    )
    
    return ReasoningResult(
        answer=answer,
        entities=entities[:10],
        relations=relations[:10],
        reasoning_path=reasoning_path,
        confidence=confidence,
        sources=sources[:5]
    )
EOF

cat > "$PROJECT/core/usecases/manage_memory.py" << 'EOF'
from datetime import datetime
from core.domain.models import Memory, MemoryType
from core.ports.memory_store import MemoryStorePort
from core.ports.embedding_model import EmbeddingModelPort

async def store_interaction(
    query: str,
    response: str,
    memory_store: MemoryStorePort,
    embedding: EmbeddingModelPort
) -> str:
    content = f"Q: {query}\nA: {response}"
    embedding_vec = await embedding.embed_text(content)
    
    memory = Memory(
        id=f"mem_{datetime.utcnow().timestamp()}",
        content=content,
        memory_type=MemoryType.SHORT_TERM,
        importance=0.5,
        created_at=datetime.utcnow(),
        accessed_at=datetime.utcnow(),
        embedding=embedding_vec
    )
    
    return await memory_store.store_memory(memory)

async def decay_old_memories(memory_store: MemoryStorePort) -> int:
    return await memory_store.decay_memories()
EOF

echo "Creating adapters..."

# Adapters - Neo4j Graph Store
cat > "$PROJECT/adapters/graph_store/neo4j_store.py" << 'EOF'
from neo4j import AsyncGraphDatabase
from typing import List, Dict, Any, Optional
from core.ports.graph_store import GraphStorePort
from core.domain.models import GraphNode, GraphRelation

class Neo4jGraphStore(GraphStorePort):
    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    
    async def create_node(self, node: GraphNode) -> str:
        async with self.driver.session() as session:
            query = f"""
            CREATE (n:{node.label.value} $props)
            SET n.embedding = $embedding
            RETURN n.id as id
            """
            result = await session.run(
                query,
                props={**node.properties, "id": node.id},
                embedding=node.embedding
            )
            record = await result.single()
            return record["id"] if record else node.id
    
    async def create_relation(self, relation: GraphRelation) -> bool:
        async with self.driver.session() as session:
            query = f"""
            MATCH (a {{id: $source_id}})
            MATCH (b {{id: $target_id}})
            CREATE (a)-[r:`{relation.relation_type}` $props]->(b)
            RETURN r
            """
            result = await session.run(
                query,
                source_id=relation.source_id,
                target_id=relation.target_id,
                props=relation.properties
            )
            return await result.single() is not None
    
    async def find_similar_nodes(self, embedding: List[float], limit: int) -> List[GraphNode]:
        async with self.driver.session() as session:
            query = """
            MATCH (n)
            WHERE n.embedding IS NOT NULL
            RETURN n
            LIMIT $limit
            """
            result = await session.run(query, limit=limit)
            
            nodes = []
            async for record in result:
                node_data = dict(record["n"])
                nodes.append(GraphNode(
                    id=node_data.get("id", ""),
                    label=node_data.get("label", "Entity"),
                    properties=node_data,
                    embedding=node_data.get("embedding")
                ))
            return nodes
    
    async def traverse_graph(self, start_node_id: str, max_hops: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        async with self.driver.session() as session:
            query = f"""
            MATCH path = (start {{id: $start_id}})-[*1..{max_hops}]-(end)
            RETURN path
            LIMIT 50
            """
            result = await session.run(query, start_id=start_node_id)
            
            paths = []
            async for record in result:
                paths.append({"path": str(record["path"])})
            return paths
    
    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        async with self.driver.session() as session:
            query = "MATCH (n {id: $node_id}) RETURN n"
            result = await session.run(query, node_id=node_id)
            record = await result.single()
            
            if record:
                node_data = dict(record["n"])
                return GraphNode(
                    id=node_data.get("id", ""),
                    label=node_data.get("label", "Entity"),
                    properties=node_data,
                    embedding=node_data.get("embedding")
                )
            return None
    
    async def query_cypher(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        async with self.driver.session() as session:
            result = await session.run(query, **params)
            return [dict(record) async for record in result]
    
    async def close(self):
        await self.driver.close()
EOF

# Embedding Model Adapter
cat > "$PROJECT/adapters/embedding_model/sentence_transformer.py" << 'EOF'
from sentence_transformers import SentenceTransformer
from typing import List
from core.ports.embedding_model import EmbeddingModelPort
import asyncio

class SentenceTransformerEmbedding(EmbeddingModelPort):
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    async def embed_text(self, text: str) -> List[float]:
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, self.model.encode, text
        )
        return embedding.tolist()
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, self.model.encode, texts
        )
        return [emb.tolist() for emb in embeddings]
    
    def get_dimension(self) -> int:
        return self.dimension
EOF

# Chunking Adapter
cat > "$PROJECT/adapters/chunking/semantic_chunker.py" << 'EOF'
from typing import List
import uuid
import tiktoken
from core.ports.chunking import ChunkingPort
from core.domain.models import Chunk

class SemanticChunker(ChunkingPort):
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    async def chunk_text(self, text: str, metadata: dict) -> List[Chunk]:
        tokens = self.encoding.encode(text)
        chunks = []
        
        start = 0
        while start < len(tokens):
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoding.decode(chunk_tokens)
            
            chunk = Chunk(
                text=chunk_text,
                chunk_id=f"chunk_{uuid.uuid4().hex[:12]}",
                metadata={
                    **metadata,
                    "start_token": start,
                    "end_token": end,
                    "token_count": len(chunk_tokens)
                }
            )
            chunks.append(chunk)
            
            start = end - self.overlap
        
        return chunks
EOF

# Entity Extractor Adapter
cat > "$PROJECT/adapters/entity_extractor/spacy_extractor.py" << 'EOF'
from typing import List
import spacy
from core.ports.entity_extractor import EntityExtractorPort
from core.domain.models import Entity, Relation

class SpacyEntityExtractor(EntityExtractorPort):
    def __init__(self, model_name: str = "en_core_web_sm", entity_types: List[str] = None):
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", model_name])
            self.nlp = spacy.load(model_name)
        
        self.entity_types = entity_types or ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT"]
    
    async def extract_entities(self, text: str) -> List[Entity]:
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            if ent.label_ in self.entity_types:
                entity = Entity(
                    name=ent.text,
                    entity_type=ent.label_,
                    confidence=0.8,
                    properties={
                        "start_char": ent.start_char,
                        "end_char": ent.end_char
                    }
                )
                entities.append(entity)
        
        return entities
    
    async def extract_relations(self, text: str, entities: List[Entity]) -> List[Relation]:
        relations = []
        entity_names = [e.name for e in entities]
        
        for i, ent1 in enumerate(entity_names):
            for ent2 in entity_names[i+1:]:
                if ent1 in text and ent2 in text:
                    pos1 = text.find(ent1)
                    pos2 = text.find(ent2)
                    
                    if abs(pos1 - pos2) < 200:
                        relation = Relation(
                            source=ent1,
                            target=ent2,
                            relation_type="RELATED_TO",
                            confidence=0.6,
                            properties={"distance": abs(pos1 - pos2)}
                        )
                        relations.append(relation)
        
        return relations
EOF

# Memory Store Adapter
cat > "$PROJECT/adapters/memory_store/neo4j_memory.py" << 'EOF'
from neo4j import AsyncGraphDatabase
from typing import List
from datetime import datetime, timedelta
import os
from core.ports.memory_store import MemoryStorePort
from core.domain.models import Memory, MemoryType

class Neo4jMemoryStore(MemoryStorePort):
    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self.decay_days = int(os.getenv("LONG_TERM_MEMORY_DECAY_DAYS", 30))
    
    async def store_memory(self, memory: Memory) -> str:
        async with self.driver.session() as session:
            query = """
            CREATE (m:Memory {
                id: $id,
                content: $content,
                memory_type: $memory_type,
                importance: $importance,
                created_at: $created_at,
                accessed_at: $accessed_at,
                access_count: $access_count,
                embedding: $embedding
            })
            RETURN m.id as id
            """
            result = await session.run(
                query,
                id=memory.id,
                content=memory.content,
                memory_type=memory.memory_type.value,
                importance=memory.importance,
                created_at=memory.created_at.isoformat(),
                accessed_at=memory.accessed_at.isoformat(),
                access_count=memory.access_count,
                embedding=memory.embedding
            )
            record = await result.single()
            return record["id"] if record else memory.id
    
    async def retrieve_memories(self, query_embedding: List[float], memory_type: MemoryType, limit: int) -> List[Memory]:
        async with self.driver.session() as session:
            query = """
            MATCH (m:Memory {memory_type: $memory_type})
            WHERE m.embedding IS NOT NULL
            RETURN m
            ORDER BY m.importance DESC
            LIMIT $limit
            """
            result = await session.run(
                query,
                memory_type=memory_type.value,
                limit=limit
            )
            
            memories = []
            async for record in result:
                mem_data = dict(record["m"])
                memory = Memory(
                    id=mem_data["id"],
                    content=mem_data["content"],
                    memory_type=MemoryType(mem_data["memory_type"]),
                    importance=mem_data["importance"],
                    created_at=datetime.fromisoformat(mem_data["created_at"]),
                    accessed_at=datetime.fromisoformat(mem_data["accessed_at"]),
                    access_count=mem_data["access_count"],
                    embedding=mem_data.get("embedding")
                )
                memories.append(memory)
            return memories
    
    async def update_memory_access(self, memory_id: str) -> bool:
        async with self.driver.session() as session:
            query = """
            MATCH (m:Memory {id: $memory_id})
            SET m.accessed_at = $now,
                m.access_count = m.access_count + 1
            RETURN m
            """
            result = await session.run(
                query,
                memory_id=memory_id,
                now=datetime.utcnow().isoformat()
            )
            return await result.single() is not None
    
    async def decay_memories(self) -> int:
        async with self.driver.session() as session:
            decay_date = (datetime.utcnow() - timedelta(days=self.decay_days)).isoformat()
            query = """
            MATCH (m:Memory {memory_type: $long_term})
            WHERE m.created_at < $decay_date AND m.importance < 0.7
            DELETE m
            RETURN count(m) as deleted_count
            """
            result = await session.run(
                query,
                long_term=MemoryType.LONG_TERM.value,
                decay_date=decay_date
            )
            record = await result.single()
            return record["deleted_count"] if record else 0
    
    async def close(self):
        await self.driver.close()
EOF

echo "Creating API..."

# API Main
cat > "$PROJECT/api/main.py" << 'EOF'
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
EOF

echo "Creating Docker files..."

# Dockerfile
cat > "$PROJECT/Dockerfile" << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8002/health || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8002"]
EOF

# Docker Compose
cat > "$PROJECT/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  neo4j:
    image: neo4j:5.14.0
    container_name: kg-neo4j
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/changeme123
      - NEO4J_dbms_memory_heap_initial__size=512m
      - NEO4J_dbms_memory_heap_max__size=2G
      - NEO4J_dbms_memory_pagecache_size=512m
    volumes:
      - ./data/neo4j/data:/data
      - ./data/neo4j/logs:/logs
    networks:
      - kg-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "cypher-shell -u neo4j -p changeme123 'RETURN 1' || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 40s

  kg-api:
    build: .
    container_name: kg-api
    ports:
      - "8002:8002"
    env_file:
      - .env
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=changeme123
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
    networks:
      - kg-network
    depends_on:
      neo4j:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8002/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

networks:
  kg-network:
    driver: bridge
EOF

echo "Creating shell scripts..."

# Start script
cat > "$PROJECT/start.sh" << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting Knowledge Graph Service..."

# Stop any existing containers
docker compose down 2>/dev/null || true

# Create necessary directories
mkdir -p data/neo4j/data data/neo4j/logs logs

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
fi

# Build and start services
echo "🔨 Building containers..."
docker compose build

echo "🚢 Starting services..."
docker compose up -d

echo "⏳ Waiting for services to be healthy..."
sleep 10

# Wait for Neo4j
echo "Waiting for Neo4j..."
for i in {1..30}; do
    if docker compose exec -T neo4j cypher-shell -u neo4j -p changeme123 "RETURN 1" > /dev/null 2>&1; then
        echo "✅ Neo4j is ready!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

# Wait for API
echo "Waiting for API..."
for i in {1..30}; do
    if curl -s http://localhost:8002/health > /dev/null 2>&1; then
        echo "✅ API is ready!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

echo ""
echo "✅ Knowledge Graph Service is running!"
echo ""
echo "📊 Neo4j Browser: http://localhost:7474"
echo "   Username: neo4j"
echo "   Password: changeme123"
echo ""
echo "📡 API Documentation: http://localhost:8002/docs"
echo "🏥 Health Check: http://localhost:8002/health"
echo ""
echo "📋 View logs: docker compose logs -f kg-api"
echo "🛑 Stop services: ./stop.sh"
EOF

# Stop script
cat > "$PROJECT/stop.sh" << 'EOF'
#!/bin/bash
set -e

echo "🛑 Stopping Knowledge Graph Service..."
docker compose down

echo "✅ Services stopped"
EOF

# Clean script
cat > "$PROJECT/clean.sh" << 'EOF'
#!/bin/bash
set -e

echo "🧹 Cleaning Knowledge Graph Service..."

# Stop services
docker compose down -v

# Remove data
read -p "Remove all data (Neo4j database)? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Removing data..."
    rm -rf data/neo4j/data/*
    rm -rf data/neo4j/logs/*
    rm -rf logs/*
    echo "✅ Data cleaned"
fi

echo "✅ Cleanup complete"
EOF

chmod +x "$PROJECT/start.sh" "$PROJECT/stop.sh" "$PROJECT/clean.sh"

echo "Creating additional files..."

# .gitignore
cat > "$PROJECT/.gitignore" << 'EOF'
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.env
*.log
data/
logs/
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
EOF

# README
cat > "$PROJECT/README.md" << 'EOF'
# Knowledge Graph SDK

Scalable Knowledge Graph service with advanced reasoning, memory layer, and entity extraction.

## 🚀 Quick Start

```bash
cd kg-service
./start.sh
```

## 📡 Endpoints

- API Docs: http://localhost:8002/docs
- Neo4j Browser: http://localhost:7474 (neo4j/changeme123)
- Health: http://localhost:8002/health

## 🔧 Usage

### Ingest Content
```bash
curl -X POST http://localhost:8002/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your content here",
    "source_id": "doc_001"
  }'
```

### Query
```bash
curl -X POST http://localhost:8002/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Your question here"}'
```

### Get Stats
```bash
curl http://localhost:8002/stats
```

## 🛑 Management

```bash
./stop.sh    # Stop services
./clean.sh   # Clean all data
```

## 📁 Structure

```
kg-service/
├── core/             # Business logic
│   ├── domain/       # Models
│   ├── ports/        # Interfaces
│   └── usecases/     # Use cases
├── adapters/         # Implementations
│   ├── graph_store/  # Neo4j
│   ├── embedding_model/
│   ├── chunking/
│   ├── entity_extractor/
│   └── memory_store/
├── api/              # FastAPI
└── config/           # Configuration
```
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "📂 Project created at: $PROJECT/"
echo ""
echo "Next steps:"
echo "  cd $PROJECT"
echo "  ./start.sh"
echo ""
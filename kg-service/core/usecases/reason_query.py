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

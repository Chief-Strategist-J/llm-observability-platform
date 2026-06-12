RAG Project — Folder Structure

rag-{domain}/
├── contracts/
│   └── v1.yaml                      ← query input, response + sources schema
│
├── src/
│   ├── api/rest/v1/handler
│   │
│   ├── features/retrieval/
│   │   ├── index
│   │   ├── pipeline             ← embed → retrieve → rerank → generate
│   │   ├── embedder             ← wraps embedding model, port interface
│   │   ├── retriever            ← queries vector store, port interface
│   │   ├── reranker             ← reranks retrieved docs by relevance
│   │   ├── generator            ← calls LLM with context, port interface
│   │   ├── types                ← Query, Document, RetrievalResult
│   │   └── tests/
│   │
│   ├── infra/adapters/
│   │   ├── openai/              ← implements llm.port
│   │   ├── anthropic/           ← implements llm.port
│   │   ├── chroma/              ← implements vector-store.port
│   │   ├── pinecone/            ← implements vector-store.port
│   │   └── cohere/              ← implements reranker.port
│   │
│   └── shared/ports/
│       ├── llm.port             ← complete(prompt) → completion
│       ├── embedder.port        ← embed(texts) → vectors
│       ├── vector-store.port    ← upsert, query, delete
│       └── reranker.port        ← rerank(query, docs) → ranked docs
│
├── prompts/
│   └── retrieval/
│       ├── system-v1.txt
│       ├── user-template-v1.txt
│       └── changelog.md
│
├── data/
│   ├── raw/                     ← source documents, PDFs, HTML
│   ├── processed/               ← chunked, cleaned text
│   └── index/                   ← embedded and indexed artifacts
│
├── evaluation/
│   ├── datasets/                ← question-answer pairs
│   ├── metrics/                 ← faithfulness, relevancy, recall
│   └── reports/                 ← dated eval run results
│
├── scripts/
│   ├── ingest.sh                ← raw → process → embed → index
│   ├── evaluate.sh
│   └── run.sh
├── .env.example
└── .package-meta.yaml


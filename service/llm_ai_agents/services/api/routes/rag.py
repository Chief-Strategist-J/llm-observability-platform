from flask import Blueprint, request, jsonify
from services.rag.api.rag_service import RAGService
from services.rag.retrieval.vector_search import ChromaRetriever
from services.rag.retrieval.reranker import CrossEncoderReranker
from services.rag.indexing.embedder_adapter import SentenceTransformerEmbedder
from services.rag.ingestion.pipeline import IngestionPipeline
from services.llm.factory import LLMFactory
from services.shared.exceptions import RAGIngestionError, ProviderNotFoundError
from services.shared.cache import instance_cache

rag_bp = Blueprint("rag", __name__)


from services.api.routes.common import get_rag_service


def _resolve_llm(provider: str):
    cache_key = f"llm:{provider}"
    cached = instance_cache.get(cache_key)
    if cached is not None:
        return cached
    config = {"model": {"provider": provider}}
    llm = LLMFactory.create(config)
    instance_cache.set(cache_key, llm)
    return llm


def _ingest(data: dict) -> dict:
    source = data.get("source", "")
    source_type = data.get("source_type", "text")
    collection = data.get("collection", "default")
    service = get_rag_service()
    count = service.ingest(source, source_type, collection)
    return {"status": "ok", "chunks_indexed": count, "collection": collection}


def _query(data: dict) -> dict:
    question = data.get("question", "")
    collection = data.get("collection", "default")
    provider = data.get("provider", "local")
    k = int(data.get("k", 4))
    service = get_rag_service()
    llm = _resolve_llm(provider)
    return service.query(question=question, llm=llm, collection=collection, k=k)


@rag_bp.route("/api/rag/ingest", methods=["POST"])
def ingest():
    data = request.get_json(silent=True) or {}
    if not data.get("source"):
        return jsonify({"error": "source is required"}), 400
    try:
        return jsonify(_ingest(data))
    except RAGIngestionError as exc:
        return jsonify({"error": str(exc)}), 422


@rag_bp.route("/api/rag/query", methods=["POST"])
def query():
    data = request.get_json(silent=True) or {}
    if not data.get("question"):
        return jsonify({"error": "question is required"}), 400
    try:
        return jsonify(_query(data))
    except ProviderNotFoundError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@rag_bp.route("/api/rag/collections", methods=["GET"])
def list_collections():
    try:
        service = get_rag_service()
        return jsonify({"collections": service.list_collections()})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@rag_bp.route("/api/rag/collection", methods=["DELETE"])
def delete_collection():
    data = request.get_json(silent=True) or {}
    collection = data.get("collection")
    if not collection:
        return jsonify({"error": "collection is required"}), 400
    try:
        service = get_rag_service()
        service.delete_collection(collection)
        return jsonify({"status": "deleted", "collection": collection})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

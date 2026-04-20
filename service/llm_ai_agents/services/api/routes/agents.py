from flask import Blueprint, request, jsonify
from services.orchestrator.executor import AgentExecutorService
from services.orchestrator.router import OrchestratorRouter
from services.agents.registry import AGENT_REGISTRY, AGENT_DESCRIPTIONS
from services.llm.registry import PROVIDER_REGISTRY
from services.shared.exceptions import AgentExecutionError, ProviderNotFoundError

from services.api.routes.common import get_rag_service

agents_bp = Blueprint("agents", __name__)

_router = OrchestratorRouter()

def _get_executor():
    return AgentExecutorService(rag_service=get_rag_service())


def _run_agent(data: dict) -> dict:
    agent_type_raw = data.get("agent_type", "auto")
    provider = data.get("provider", "local")
    user_input = data.get("input", "")
    session_id = data.get("session_id", "")
    collection = data.get("collection", "default")

    resolved_type = _router.resolve_agent_type(agent_type_raw, user_input)
    context = _router.build_context(resolved_type, provider, session_id, collection)
    output = _get_executor().execute(context, user_input)

    return {
        "output": output.text,
        "sources": output.sources,
        "agent_type": resolved_type,
        "provider": provider,
        "metadata": output.metadata,
    }


@agents_bp.route("/api/agent/run", methods=["POST"])
def run_agent():
    data = request.get_json(silent=True) or {}
    if not data.get("input"):
        return jsonify({"error": "input is required"}), 400
    try:
        return jsonify(_run_agent(data))
    except ProviderNotFoundError as exc:
        return jsonify({"error": str(exc)}), 400
    except AgentExecutionError as exc:
        return jsonify({"error": str(exc)}), 500


@agents_bp.route("/api/agent/list", methods=["GET"])
def list_agents():
    return jsonify({"agents": list(AGENT_REGISTRY.keys())})


@agents_bp.route("/api/agent/types", methods=["GET"])
def agent_types():
    return jsonify({
        "agents": {
            name: {"description": AGENT_DESCRIPTIONS.get(name, "")}
            for name in AGENT_REGISTRY
        },
        "providers": list(PROVIDER_REGISTRY.keys()),
    })

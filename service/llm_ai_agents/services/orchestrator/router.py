from services.orchestrator.context_manager import SessionContext


_KEYWORD_AGENT_MAP = {
    "rag": "rag",
    "document": "rag",
    "search": "research",
    "research": "research",
    "find": "research",
}


class OrchestratorRouter:
    def resolve_agent_type(self, requested_type: str, user_input: str = "") -> str:
        if requested_type and requested_type != "auto":
            return requested_type
        lowered = user_input.lower()
        for keyword, agent_type in _KEYWORD_AGENT_MAP.items():
            if keyword in lowered:
                return agent_type
        return "chat"

    def build_context(
        self,
        agent_type: str,
        provider: str,
        session_id: str = "",
        collection: str = "default",
    ) -> SessionContext:
        return SessionContext(
            session_id=session_id,
            agent_type=agent_type,
            provider=provider,
            collection=collection,
        )

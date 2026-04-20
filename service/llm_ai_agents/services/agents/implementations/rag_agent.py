from services.agents.base.agent import BaseAgent, AgentInput, AgentOutput
from services.llm.base.llm import BaseLLM
from services.rag.api.rag_service import RAGService


class RAGAgent(BaseAgent):
    def __init__(self, llm: BaseLLM, rag_service: RAGService):
        super().__init__(llm)
        self._rag_service = rag_service

    def run(self, agent_input: AgentInput) -> AgentOutput:
        result = self._rag_service.query(
            question=agent_input.text,
            llm=self._llm,
            collection=agent_input.collection,
        )
        return AgentOutput(
            text=result["answer"],
            sources=result["sources"],
            metadata={"chunks_retrieved": result["chunks_retrieved"]},
        )

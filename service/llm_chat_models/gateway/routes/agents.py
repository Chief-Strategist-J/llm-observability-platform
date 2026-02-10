from fastapi import APIRouter, HTTPException
from typing import List
from gateway.schemas.agents import (
    AgentChatRequest,
    AgentChatResponse,
    AgentTypeInfo,
)
from logic.agents.base import AgentInput
from logic.agents.registry import AgentRegistry
from telemetry.logger import log_event, get_tracer, trace_with_details

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/types", response_model=List[AgentTypeInfo])
@trace_with_details(get_tracer())
async def list_agent_types():
    """List all registered agent types and their capabilities."""
    log_event("api_list_agent_types")
    registry = AgentRegistry.get_instance()
    return registry.list_types()


@router.post("/chat/completions", response_model=AgentChatResponse)
@trace_with_details(get_tracer())
async def agent_chat_completions(request: AgentChatRequest):
    """
    Execute a chat completion through an agent.

    The dashboard calls this endpoint. It resolves the agent_type
    from the request, converts to AgentInput, and delegates.
    """
    log_event(
        "api_agent_chat",
        agent_type=request.agent_type,
        model=request.model,
    )

    registry = AgentRegistry.get_instance()

    if not registry.has(request.agent_type):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown agent type: '{request.agent_type}'. "
            f"Available: {[t['name'] for t in registry.list_types()]}",
        )

    agent = registry.get(request.agent_type)

    agent_input = AgentInput(
        messages=[msg.model_dump() for msg in request.messages],
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stream=request.stream,
        metadata=request.metadata,
    )

    try:
        output = await agent.execute(agent_input)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_event("api_agent_chat_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

    if output.metadata.get("error"):
        raise HTTPException(
            status_code=500, detail=output.metadata["error"]
        )

    return AgentChatResponse(
        content=output.content,
        model=output.model,
        finish_reason=output.finish_reason,
        usage=output.usage,
        metadata=output.metadata,
    )

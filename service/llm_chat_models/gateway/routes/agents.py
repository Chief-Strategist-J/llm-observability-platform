from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
from gateway.schemas.agents import AgentChatRequest, AgentChatResponse, AgentTypeInfo
from logic.agents.base import AgentInput
from logic.agents.registry import AgentRegistry
from telemetry.logger import log_event, get_tracer, trace_with_details
router = APIRouter(prefix='/agents', tags=['agents'])

@router.get('/types', response_model=List[AgentTypeInfo])
@trace_with_details(get_tracer())
async def list_agent_types():
    log_event('api_list_agent_types')
    registry = AgentRegistry.get_instance()
    return registry.list_types()

@router.post('/chat/completions', response_model=AgentChatResponse)
@trace_with_details(get_tracer())
async def agent_chat_completions(request: AgentChatRequest):
    log_event('api_agent_chat', agent_type=request.agent_type, model=request.model)
    registry = AgentRegistry.get_instance()
    agent_cls = registry.get(request.agent_type)
    if not agent_cls:
        raise HTTPException(status_code=400, detail=f"Unknown agent type: '{request.agent_type}'. Available: {[t['name'] for t in registry.list_types()]}")
    agent = agent_cls()
    agent_input = AgentInput(prompt=request.prompt, parameters=request.parameters or {}, context=request.context or {})
    try:
        output = await agent.generate_response(agent_input)
        return AgentChatResponse(content=output.content, metadata=output.metadata, usage=output.usage)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_event('api_agent_chat_error', error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    if output.metadata.get('error'):
        raise HTTPException(status_code=500, detail=output.metadata['error'])
    return AgentChatResponse(content=output.content, model=output.model, finish_reason=output.finish_reason, usage=output.usage, metadata=output.metadata)
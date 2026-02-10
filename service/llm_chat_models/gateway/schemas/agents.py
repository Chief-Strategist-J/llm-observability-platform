from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class ChatMessage(BaseModel):
    role: str
    content: str

class AgentChatRequest(BaseModel):
    agent_type: str = 'chat'
    model: str = 'llama3'
    messages: List[ChatMessage]
    stream: bool = False
    temperature: float = 0.7
    max_tokens: int = 2048
    metadata: Dict[str, Any] = {}

class AgentChatResponse(BaseModel):
    content: str
    model: str
    finish_reason: str = 'stop'
    usage: Dict[str, int] = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
    metadata: Dict[str, Any] = {}

class AgentTypeInfo(BaseModel):
    name: str
    supports_streaming: bool
    supports_voice: bool
    supported_models: List[str]
    metadata: Dict[str, Any] = {}
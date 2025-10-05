from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class LLMRequest:
    prompt: str
    provider: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str

@dataclass
class STTRequest:
    audio_data: bytes
    provider: str

@dataclass
class STTResponse:
    text: str
    provider: str

@dataclass
class TTSRequest:
    text: str
    provider: str

@dataclass
class TTSResponse:
    audio_data: bytes
    provider: str

"""Domain models for AI Proxy service.

This module contains data classes representing requests and responses for various AI
services (LLM, STT, TTS).

"""

from dataclasses import dataclass


@dataclass
class LLMRequest:
    """
    Request model for language model generation.
    """

    prompt: str
    provider: str
    max_tokens: int | None = None
    temperature: float | None = None


@dataclass
class LLMResponse:
    """
    Response model for language model generation.
    """

    text: str
    provider: str
    model: str


@dataclass
class STTRequest:
    """
    Request model for speech-to-text conversion.
    """

    audio_data: bytes
    provider: str


@dataclass
class STTResponse:
    """
    Response model for speech-to-text conversion.
    """

    text: str
    provider: str


@dataclass
class TTSRequest:
    """
    Request model for text-to-speech conversion.
    """

    text: str
    provider: str


@dataclass
class TTSResponse:
    """
    Response model for text-to-speech conversion.
    """

    audio_data: bytes
    provider: str

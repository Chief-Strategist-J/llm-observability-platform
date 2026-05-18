from typing import Union, List, Dict, Any, Tuple
from .service import TokenCountingService, LLMSpanWithTokensContext
from .infra.adapters.tiktoken_adapter import TiktokenEncoderAdapter

_SERVICE = TokenCountingService(encoder=TiktokenEncoderAdapter())

def count_tokens(prompt: Union[str, List[Dict[str, Any]]], model: str) -> Tuple[int, str]:
    return _SERVICE.count_tokens(prompt, model)

def llm_span_with_tokens(model: str, provider: str, prompt: Union[str, List[Dict[str, Any]]], **kwargs: Any) -> LLMSpanWithTokensContext:
    return _SERVICE.llm_span_with_tokens(model, provider, prompt, **kwargs)

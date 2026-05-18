from typing import Union, List, Dict, Any, Tuple
from ...ports import TokenCounterPort
from ....token_counting.index import count_tokens

class TokenCounterAdapter(TokenCounterPort):
    def count_tokens(self, prompt: Union[str, List[Dict[str, Any]]], model: str) -> Tuple[int, str]:
        return count_tokens(prompt, model)

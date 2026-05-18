import tiktoken
from typing import Any, List
from ...ports import TokenEncoderPort

class TiktokenEncoderAdapter(TokenEncoderPort):
    def get_encoding(self, model: str) -> Any:
        return tiktoken.encoding_for_model(model)

    def encode(self, encoding: Any, text: str) -> List[int]:
        return encoding.encode(text)

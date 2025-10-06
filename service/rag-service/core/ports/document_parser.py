from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class DocumentParserPort(ABC):
    @abstractmethod
    async def parse(self, file_bytes: bytes) -> str:
        raise NotImplementedError

    @abstractmethod
    async def chunk(self, text: str) -> AsyncIterator[str]:
        raise NotImplementedError

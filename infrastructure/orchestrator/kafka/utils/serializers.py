import json
from abc import ABC, abstractmethod
from typing import Any, Optional


class Serializer(ABC):
    @abstractmethod
    def serialize(self, data: Any) -> bytes:
        pass


class Deserializer(ABC):
    @abstractmethod
    def deserialize(self, data: bytes) -> Any:
        pass


class StringSerializer(Serializer):
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding

    def serialize(self, data: Any) -> bytes:
        if data is None:
            return b''
        if isinstance(data, bytes):
            return data
        return str(data).encode(self.encoding)


class StringDeserializer(Deserializer):
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding

    def deserialize(self, data: bytes) -> str:
        if not data:
            return ''
        return data.decode(self.encoding)


class JSONSerializer(Serializer):
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding

    def serialize(self, data: Any) -> bytes:
        if data is None:
            return b''
        return json.dumps(data).encode(self.encoding)


class JSONDeserializer(Deserializer):
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding

    def deserialize(self, data: bytes) -> Any:
        if not data:
            return None
        return json.loads(data.decode(self.encoding))


class BytesSerializer(Serializer):
    def serialize(self, data: Any) -> bytes:
        if data is None:
            return b''
        if isinstance(data, bytes):
            return data
        raise TypeError(f"Expected bytes, got {type(data)}")


class BytesDeserializer(Deserializer):
    def deserialize(self, data: bytes) -> bytes:
        return data


class IntegerSerializer(Serializer):
    def serialize(self, data: Any) -> bytes:
        if data is None:
            return b''
        return int(data).to_bytes(8, byteorder='big', signed=True)


class IntegerDeserializer(Deserializer):
    def deserialize(self, data: bytes) -> Optional[int]:
        if not data:
            return None
        return int.from_bytes(data, byteorder='big', signed=True)

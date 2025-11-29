import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.kafka.utils.serializers import (
    StringSerializer,
    StringDeserializer,
    JSONSerializer,
    JSONDeserializer,
    BytesSerializer,
    BytesDeserializer,
    IntegerSerializer,
    IntegerDeserializer
)


class TestKafkaIntegration:
    def test_string_serialization_roundtrip(self):
        serializer = StringSerializer()
        deserializer = StringDeserializer()
        
        original = "Hello, Kafka!"
        serialized = serializer.serialize(original)
        deserialized = deserializer.deserialize(serialized)
        
        assert deserialized == original
    
    def test_json_serialization_roundtrip(self):
        serializer = JSONSerializer()
        deserializer = JSONDeserializer()
        
        original = {
            "name": "test",
            "count": 42,
            "nested": {"key": "value"},
            "list": [1, 2, 3]
        }
        
        serialized = serializer.serialize(original)
        deserialized = deserializer.deserialize(serialized)
        
        assert deserialized == original
    
    def test_bytes_serialization_roundtrip(self):
        serializer = BytesSerializer()
        deserializer = BytesDeserializer()
        
        original = b"binary data \x00\x01\x02"
        serialized = serializer.serialize(original)
        deserialized = deserializer.deserialize(serialized)
        
        assert deserialized == original
    
    def test_integer_serialization_roundtrip(self):
        serializer = IntegerSerializer()
        deserializer = IntegerDeserializer()
        
        for original in [0, 42, -100, 1000000, -999999]:
            serialized = serializer.serialize(original)
            deserialized = deserializer.deserialize(serialized)
            assert deserialized == original
    
    def test_null_value_handling(self):
        string_serializer = StringSerializer()
        json_serializer = JSONSerializer()
        bytes_serializer = BytesSerializer()
        integer_serializer = IntegerSerializer()
        
        assert string_serializer.serialize(None) == b''
        assert json_serializer.serialize(None) == b''
        assert bytes_serializer.serialize(None) == b''
        assert integer_serializer.serialize(None) == b''
    
    def test_empty_value_deserialization(self):
        string_deserializer = StringDeserializer()
        json_deserializer = JSONDeserializer()
        integer_deserializer = IntegerDeserializer()
        
        assert string_deserializer.deserialize(b'') == ''
        assert json_deserializer.deserialize(b'') is None
        assert integer_deserializer.deserialize(b'') is None
    
    @pytest.mark.parametrize("data", [
        "simple string",
        "unicode: こんにちは",
        "special chars: !@#$%^&*()",
        "numbers: 0123456789",
    ])
    def test_string_serialization_various_inputs(self, data):
        serializer = StringSerializer()
        deserializer = StringDeserializer()
        
        serialized = serializer.serialize(data)
        deserialized = deserializer.deserialize(serialized)
        
        assert deserialized == data
    
    @pytest.mark.parametrize("data", [
        {"simple": "dict"},
        {"nested": {"deep": {"value": 123}}},
        {"array": [1, 2, 3, 4, 5]},
        {"mixed": {"str": "text", "num": 42, "bool": True, "null": None}},
    ])
    def test_json_serialization_various_structures(self, data):
        serializer = JSONSerializer()
        deserializer = JSONDeserializer()
        
        serialized = serializer.serialize(data)
        deserialized = deserializer.deserialize(serialized)
        
        assert deserialized == data
    
    def test_encoding_variations(self):
        for encoding in ['utf-8', 'utf-16', 'ascii']:
            serializer = StringSerializer(encoding=encoding)
            deserializer = StringDeserializer(encoding=encoding)
            
            if encoding == 'ascii':
                data = "ASCII only"
            else:
                data = "Unicode: 你好"
            
            try:
                serialized = serializer.serialize(data)
                deserialized = deserializer.deserialize(serialized)
                assert deserialized == data
            except UnicodeEncodeError:
                pass

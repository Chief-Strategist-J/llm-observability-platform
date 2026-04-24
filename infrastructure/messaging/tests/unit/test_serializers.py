import pytest
import json
from infrastructure.messaging.utils.serializers import (
    Serializer,
    Deserializer,
    StringSerializer,
    StringDeserializer,
    JSONSerializer,
    JSONDeserializer,
    BytesSerializer,
    BytesDeserializer,
    IntegerSerializer,
    IntegerDeserializer,
)


class TestStringSerializer:
    @pytest.fixture
    def serializer(self):
        return StringSerializer()

    def test_serialize_string(self, serializer):
        data = "test string"
        result = serializer.serialize(data)
        assert result == b"test string"

    def test_serialize_none(self, serializer):
        result = serializer.serialize(None)
        assert result == b""

    def test_serialize_bytes(self, serializer):
        data = b"test bytes"
        result = serializer.serialize(data)
        assert result == b"test bytes"

    def test_serialize_int(self, serializer):
        data = 123
        result = serializer.serialize(data)
        assert result == b"123"

    def test_serialize_dict(self, serializer):
        data = {"key": "value"}
        result = serializer.serialize(data)
        assert result == b"{'key': 'value'}"

    def test_custom_encoding(self):
        serializer = StringSerializer(encoding='utf-16')
        data = "test"
        result = serializer.serialize(data)
        assert result != b"test"

    def test_serialize_empty_string(self, serializer):
        result = serializer.serialize("")
        assert result == b""


class TestStringDeserializer:
    @pytest.fixture
    def deserializer(self):
        return StringDeserializer()

    def test_deserialize_bytes(self, deserializer):
        data = b"test string"
        result = deserializer.deserialize(data)
        assert result == "test string"

    def test_deserialize_empty(self, deserializer):
        result = deserializer.deserialize(b"")
        assert result == ""

    def test_custom_encoding(self):
        deserializer = StringDeserializer(encoding='utf-16')
        data = "test".encode('utf-16')
        result = deserializer.deserialize(data)
        assert result == "test"

    def test_invalid_encoding(self, deserializer):
        with pytest.raises(UnicodeDecodeError):
            deserializer.deserialize(b"\xff\xfe")


class TestJSONSerializer:
    @pytest.fixture
    def serializer(self):
        return JSONSerializer()

    def test_serialize_dict(self, serializer):
        data = {"key": "value", "number": 123}
        result = serializer.serialize(data)
        assert b'"key": "value"' in result
        assert b'"number": 123' in result

    def test_serialize_list(self, serializer):
        data = [1, 2, 3]
        result = serializer.serialize(data)
        assert result == b"[1, 2, 3]"

    def test_serialize_none(self, serializer):
        result = serializer.serialize(None)
        assert result == b""

    def test_serialize_string(self, serializer):
        data = "test"
        result = serializer.serialize(data)
        assert result == b'"test"'

    def test_serialize_nested_dict(self, serializer):
        data = {"outer": {"inner": "value"}}
        result = serializer.serialize(data)
        assert b'"outer"' in result
        assert b'"inner"' in result

    def test_serialize_unserializable(self, serializer):
        class CustomClass:
            pass
        with pytest.raises(TypeError):
            serializer.serialize(CustomClass())


class TestJSONDeserializer:
    @pytest.fixture
    def deserializer(self):
        return JSONDeserializer()

    def test_deserialize_dict(self, deserializer):
        data = b'{"key": "value"}'
        result = deserializer.deserialize(data)
        assert result == {"key": "value"}

    def test_deserialize_list(self, deserializer):
        data = b'[1, 2, 3]'
        result = deserializer.deserialize(data)
        assert result == [1, 2, 3]

    def test_deserialize_empty(self, deserializer):
        result = deserializer.deserialize(b"")
        assert result is None

    def test_deserialize_invalid_json(self, deserializer):
        with pytest.raises(json.JSONDecodeError):
            deserializer.deserialize(b"invalid json")

    def test_deserialize_number(self, deserializer):
        data = b'123'
        result = deserializer.deserialize(data)
        assert result == 123

    def test_deserialize_boolean(self, deserializer):
        data = b'true'
        result = deserializer.deserialize(data)
        assert result is True


class TestBytesSerializer:
    @pytest.fixture
    def serializer(self):
        return BytesSerializer()

    def test_serialize_bytes(self, serializer):
        data = b"test bytes"
        result = serializer.serialize(data)
        assert result == b"test bytes"

    def test_serialize_none(self, serializer):
        result = serializer.serialize(None)
        assert result == b""

    def test_serialize_non_bytes(self, serializer):
        with pytest.raises(TypeError, match="Expected bytes"):
            serializer.serialize("string")

    def test_serialize_empty_bytes(self, serializer):
        result = serializer.serialize(b"")
        assert result == b""


class TestBytesDeserializer:
    @pytest.fixture
    def deserializer(self):
        return BytesDeserializer()

    def test_deserialize_bytes(self, deserializer):
        data = b"test bytes"
        result = deserializer.deserialize(data)
        assert result == b"test bytes"

    def test_deserialize_empty(self, deserializer):
        result = deserializer.deserialize(b"")
        assert result == b""


class TestIntegerSerializer:
    @pytest.fixture
    def serializer(self):
        return IntegerSerializer()

    def test_serialize_positive_int(self, serializer):
        data = 123
        result = serializer.serialize(data)
        assert len(result) == 8

    def test_serialize_negative_int(self, serializer):
        data = -123
        result = serializer.serialize(data)
        assert len(result) == 8

    def test_serialize_zero(self, serializer):
        data = 0
        result = serializer.serialize(data)
        assert result == b"\x00" * 8

    def test_serialize_none(self, serializer):
        result = serializer.serialize(None)
        assert result == b""

    def test_serialize_large_int(self, serializer):
        data = 2**63 - 1
        result = serializer.serialize(data)
        assert len(result) == 8

    def test_serialize_string_int(self, serializer):
        data = "123"
        result = serializer.serialize(data)
        assert len(result) == 8

    def test_serialize_invalid_type(self, serializer):
        with pytest.raises(ValueError):
            serializer.serialize("not a number")


class TestIntegerDeserializer:
    @pytest.fixture
    def deserializer(self):
        return IntegerDeserializer()

    def test_deserialize_positive_int(self, deserializer):
        data = (123).to_bytes(8, byteorder='big', signed=True)
        result = deserializer.deserialize(data)
        assert result == 123

    def test_deserialize_negative_int(self, deserializer):
        data = (-123).to_bytes(8, byteorder='big', signed=True)
        result = deserializer.deserialize(data)
        assert result == -123

    def test_deserialize_zero(self, deserializer):
        data = b"\x00" * 8
        result = deserializer.deserialize(data)
        assert result == 0

    def test_deserialize_empty(self, deserializer):
        result = deserializer.deserialize(b"")
        assert result is None

    def test_deserialize_invalid_length(self):
        deserializer = IntegerDeserializer()
        result = deserializer.deserialize(b"")
        assert result is None


class TestAbstractClasses:
    def test_serializer_is_abstract(self):
        with pytest.raises(TypeError):
            Serializer()

    def test_deserializer_is_abstract(self):
        with pytest.raises(TypeError):
            Deserializer()


class TestRoundTrip:
    def test_string_round_trip(self):
        serializer = StringSerializer()
        deserializer = StringDeserializer()
        original = "test string"
        serialized = serializer.serialize(original)
        deserialized = deserializer.deserialize(serialized)
        assert deserialized == original

    def test_json_round_trip(self):
        serializer = JSONSerializer()
        deserializer = JSONDeserializer()
        original = {"key": "value", "number": 123}
        serialized = serializer.serialize(original)
        deserialized = deserializer.deserialize(serialized)
        assert deserialized == original

    def test_bytes_round_trip(self):
        serializer = BytesSerializer()
        deserializer = BytesDeserializer()
        original = b"test bytes"
        serialized = serializer.serialize(original)
        deserialized = deserializer.deserialize(serialized)
        assert deserialized == original

    def test_integer_round_trip(self):
        serializer = IntegerSerializer()
        deserializer = IntegerDeserializer()
        original = 12345
        serialized = serializer.serialize(original)
        deserialized = deserializer.deserialize(serialized)
        assert deserialized == original

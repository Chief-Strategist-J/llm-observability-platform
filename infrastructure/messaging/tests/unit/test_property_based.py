import pytest
from hypothesis import given, strategies as st, settings, example
from hypothesis.strategies import text, binary, integers, lists, dictionaries, none
from infrastructure.messaging.utils.serializers import (
    StringSerializer,
    StringDeserializer,
    JSONSerializer,
    JSONDeserializer,
    BytesSerializer,
    BytesDeserializer,
    IntegerSerializer,
    IntegerDeserializer,
)
from infrastructure.messaging.utils.compression import (
    CompressionType,
    get_compressor,
)
from infrastructure.messaging.utils.partition_selector import (
    HashPartitioner,
    RoundRobinPartitioner,
)
from domain.models.schemas import (
    DatabaseConfig,
    SchemaRegistryConfig,
    ProcessingConfig,
)
from domain.ports.schema_registry_port import SchemaType


class TestSerializationPropertyBased:
    @given(text(min_size=0, max_size=1000))
    @settings(max_examples=100)
    def test_string_serialization_round_trip(self, data):
        serializer = StringSerializer()
        deserializer = StringDeserializer()
        serialized = serializer.serialize(data)
        deserialized = deserializer.deserialize(serialized)
        assert deserialized == data

    @given(text(min_size=0, max_size=1000))
    @settings(max_examples=100)
    def test_string_serialization_with_bytes(self, data):
        serializer = StringSerializer()
        deserializer = StringDeserializer()
        serialized = serializer.serialize(data.encode('utf-8'))
        deserialized = deserializer.deserialize(serialized)
        assert deserialized == data

    @given(dictionaries(keys=text(min_size=1, max_size=50), values=text(min_size=0, max_size=100), min_size=0, max_size=20))
    @settings(max_examples=100)
    def test_json_serialization_round_trip(self, data):
        serializer = JSONSerializer()
        deserializer = JSONDeserializer()
        serialized = serializer.serialize(data)
        deserialized = deserializer.deserialize(serialized)
        assert deserialized == data

    @given(lists(elements=integers(min_value=-1000, max_value=1000), min_size=0, max_size=50))
    @settings(max_examples=100)
    def test_json_list_serialization_round_trip(self, data):
        serializer = JSONSerializer()
        deserializer = JSONDeserializer()
        serialized = serializer.serialize(data)
        deserialized = deserializer.deserialize(serialized)
        assert deserialized == data

    @given(binary(min_size=0, max_size=1000))
    @settings(max_examples=100)
    def test_bytes_serialization_round_trip(self, data):
        serializer = BytesSerializer()
        deserializer = BytesDeserializer()
        serialized = serializer.serialize(data)
        deserialized = deserializer.deserialize(serialized)
        assert deserialized == data

    @given(integers(min_value=-2**63, max_value=2**63 - 1))
    @settings(max_examples=100)
    def test_integer_serialization_round_trip(self, data):
        serializer = IntegerSerializer()
        deserializer = IntegerDeserializer()
        serialized = serializer.serialize(data)
        deserialized = deserializer.deserialize(serialized)
        assert deserialized == data

    @given(none())
    @settings(max_examples=10)
    def test_none_serialization(self, data):
        string_serializer = StringSerializer()
        json_serializer = JSONSerializer()
        bytes_serializer = BytesSerializer()
        integer_serializer = IntegerSerializer()
        
        assert string_serializer.serialize(data) == b""
        assert json_serializer.serialize(data) == b""
        assert bytes_serializer.serialize(data) == b""
        assert integer_serializer.serialize(data) == b""


class TestCompressionPropertyBased:
    @given(binary(min_size=0, max_size=10000))
    @settings(max_examples=50)
    def test_gzip_round_trip(self, data):
        compressor = get_compressor(CompressionType.GZIP, level=6)
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        assert decompressed == data

    @given(binary(min_size=0, max_size=10000))
    @settings(max_examples=50)
    def test_none_compression_identity(self, data):
        compressor = get_compressor(CompressionType.NONE)
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        assert compressed == data
        assert decompressed == data

    @given(binary(min_size=0, max_size=10000))
    @settings(max_examples=50)
    def test_compression_reduces_size(self, data):
        if len(data) > 100:
            compressor = get_compressor(CompressionType.GZIP, level=9)
            compressed = compressor.compress(data)
            assert len(compressed) <= len(data)

    @given(binary(min_size=0, max_size=1000))
    @settings(max_examples=50)
    def test_compression_deterministic(self, data):
        compressor1 = get_compressor(CompressionType.GZIP, level=6)
        compressor2 = get_compressor(CompressionType.GZIP, level=6)
        compressed1 = compressor1.compress(data)
        compressed2 = compressor2.compress(data)
        assert compressed1 == compressed2


class TestPartitionPropertyBased:
    @given(binary(min_size=1, max_size=1000), integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_hash_partitioner_consistency(self, key, num_partitions):
        partitioner = HashPartitioner()
        partition1 = partitioner.select_partition(key, num_partitions)
        partition2 = partitioner.select_partition(key, num_partitions)
        assert partition1 == partition2

    @given(binary(min_size=1, max_size=1000), integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_hash_partitioner_bounds(self, key, num_partitions):
        partitioner = HashPartitioner()
        partition = partitioner.select_partition(key, num_partitions)
        assert 0 <= partition < num_partitions

    @given(binary(min_size=1, max_size=1000), integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_hash_partitioner_different_keys(self, key, num_partitions):
        partitioner = HashPartitioner()
        key2 = key + b"x"
        partition1 = partitioner.select_partition(key, num_partitions)
        partition2 = partitioner.select_partition(key2, num_partitions)
        if key != key2:
            assert partition1 != partition2 or partition1 == partition2

    @given(integers(min_value=1, max_value=100))
    @settings(max_examples=50)
    def test_round_robin_sequence(self, num_partitions):
        partitioner = RoundRobinPartitioner()
        partitions = [partitioner.select_partition(None, num_partitions) for _ in range(num_partitions * 3)]
        expected = [i % num_partitions for i in range(num_partitions * 3)]
        assert partitions == expected

    @given(integers(min_value=1, max_value=100))
    @settings(max_examples=50)
    def test_round_robin_bounds(self, num_partitions):
        partitioner = RoundRobinPartitioner()
        for _ in range(1000):
            partition = partitioner.select_partition(None, num_partitions)
            assert 0 <= partition < num_partitions


class TestSchemaValidationPropertyBased:
    @given(text(min_size=1, max_size=50), text(min_size=1, max_size=200))
    @settings(max_examples=50)
    def test_database_config_postgresql(self, db_type, connection_string):
        if db_type == "postgresql":
            config = DatabaseConfig(database_type=db_type, connection_string=connection_string)
            assert config.database_type == db_type
            assert config.connection_string == connection_string

    @given(text(min_size=1, max_size=50), text(min_size=1, max_size=200))
    @settings(max_examples=50)
    def test_database_config_mongodb(self, db_type, connection_string):
        if db_type == "mongodb":
            config = DatabaseConfig(database_type=db_type, connection_string=connection_string)
            assert config.database_type == db_type
            assert config.connection_string == connection_string

    @given(text(min_size=1, max_size=200), integers(min_value=1, max_value=10))
    @settings(max_examples=50)
    def test_schema_registry_config(self, url, timeout):
        config = SchemaRegistryConfig(url=url, timeout_ms=timeout * 1000)
        assert config.url == url
        assert config.timeout_ms == timeout * 1000

    @given(integers(min_value=1, max_value=1000), integers(min_value=0, max_value=10), st.booleans())
    @settings(max_examples=50)
    def test_processing_config(self, batch_size, max_retries, auto_commit):
        config = ProcessingConfig(batch_size=batch_size, max_retries=max_retries, auto_commit=auto_commit)
        assert config.batch_size == batch_size
        assert config.max_retries == max_retries
        assert config.auto_commit == auto_commit


class TestEdgeCasesPropertyBased:
    @given(binary(min_size=0, max_size=0))
    @settings(max_examples=10)
    def test_empty_data_serialization(self, data):
        string_serializer = StringSerializer()
        json_serializer = JSONSerializer()
        bytes_serializer = BytesSerializer()
        
        assert string_serializer.serialize(data) == b""
        assert json_serializer.serialize(data) == b""
        assert bytes_serializer.serialize(data) == b""

    @given(binary(min_size=10000, max_size=100000))
    @settings(max_examples=20)
    def test_large_data_compression(self, data):
        compressor = get_compressor(CompressionType.GZIP, level=6)
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        assert decompressed == data
        assert len(compressed) < len(data)

    @given(integers(min_value=1, max_value=1000000))
    @settings(max_examples=50)
    def test_large_partition_count(self, num_partitions):
        partitioner = HashPartitioner()
        key = b"test-key"
        partition = partitioner.select_partition(key, num_partitions)
        assert 0 <= partition < num_partitions

    @given(integers(min_value=-1000, max_value=1000))
    @settings(max_examples=50)
    def test_negative_integer_serialization(self, data):
        serializer = IntegerSerializer()
        deserializer = IntegerDeserializer()
        serialized = serializer.serialize(data)
        deserialized = deserializer.deserialize(serialized)
        assert deserialized == data

    @given(text(min_size=0, max_size=1000, alphabet="abcdefghijklmnopqrstuvwxyz"))
    @settings(max_examples=50)
    def test_unicode_serialization(self, data):
        serializer = StringSerializer()
        deserializer = StringDeserializer()
        serialized = serializer.serialize(data)
        deserialized = deserializer.deserialize(serialized)
        assert deserialized == data


class TestInvalidInputsPropertyBased:
    @given(integers(min_value=-1000, max_value=-1))
    @settings(max_examples=50)
    def test_invalid_partition_count(self, num_partitions):
        partitioner = HashPartitioner()
        with pytest.raises((ZeroDivisionError, Exception)):
            partitioner.select_partition(b"key", num_partitions)

    @given(integers(min_value=0, max_value=0))
    @settings(max_examples=10)
    def test_zero_partition_count(self, num_partitions):
        partitioner = HashPartitioner()
        with pytest.raises(ZeroDivisionError):
            partitioner.select_partition(b"key", num_partitions)

    @given(text(min_size=1, max_size=50))
    @settings(max_examples=50)
    def test_invalid_database_type(self, db_type):
        if db_type not in ["postgresql", "mongodb"]:
            with pytest.raises(ValidationError):
                DatabaseConfig(database_type=db_type, connection_string="test")

    @given(integers(min_value=0, max_value=500))
    @settings(max_examples=50)
    def test_invalid_timeout(self, timeout):
        if timeout < 1000:
            with pytest.raises(ValidationError):
                SchemaRegistryConfig(url="http://localhost:8081", timeout_ms=timeout)

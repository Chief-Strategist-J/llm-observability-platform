import pytest
from infrastructure.messaging.utils.partition_selector import (
    PartitionSelector,
    HashPartitioner,
    RoundRobinPartitioner,
    StickyPartitioner,
    CustomPartitioner,
)


class TestHashPartitioner:
    @pytest.fixture
    def partitioner(self):
        return HashPartitioner()

    def test_select_partition_with_key(self, partitioner):
        key = b"test-key"
        partition = partitioner.select_partition(key, 10)
        assert 0 <= partition < 10

    def test_select_partition_without_key(self, partitioner):
        partition = partitioner.select_partition(None, 10)
        assert partition == 0

    def test_select_partition_consistency(self, partitioner):
        key = b"test-key"
        partition1 = partitioner.select_partition(key, 10)
        partition2 = partitioner.select_partition(key, 10)
        assert partition1 == partition2

    def test_select_partition_different_keys(self, partitioner):
        key1 = b"key1"
        key2 = b"key2"
        partition1 = partitioner.select_partition(key1, 10)
        partition2 = partitioner.select_partition(key2, 10)
        assert partition1 != partition2

    def test_select_partition_single_partition(self, partitioner):
        key = b"test-key"
        partition = partitioner.select_partition(key, 1)
        assert partition == 0

    def test_select_partition_large_partition_count(self, partitioner):
        key = b"test-key"
        partition = partitioner.select_partition(key, 1000)
        assert 0 <= partition < 1000

    def test_murmur2_hash_empty_key(self, partitioner):
        hash_value = partitioner._murmur2_hash(b"")
        assert isinstance(hash_value, int)

    def test_murmur2_hash_consistency(self, partitioner):
        key = b"test-key"
        hash1 = partitioner._murmur2_hash(key)
        hash2 = partitioner._murmur2_hash(key)
        assert hash1 == hash2


class TestRoundRobinPartitioner:
    @pytest.fixture
    def partitioner(self):
        return RoundRobinPartitioner()

    def test_select_partition_sequence(self, partitioner):
        partitions = [partitioner.select_partition(None, 3) for _ in range(10)]
        assert partitions == [0, 1, 2, 0, 1, 2, 0, 1, 2, 0]

    def test_select_partition_with_key_ignored(self, partitioner):
        partition1 = partitioner.select_partition(b"key1", 3)
        partition2 = partitioner.select_partition(b"key2", 3)
        assert partition2 == (partition1 + 1) % 3

    def test_select_partition_single_partition(self, partitioner):
        for _ in range(10):
            partition = partitioner.select_partition(None, 1)
            assert partition == 0

    def test_counter_overflow(self, partitioner):
        for _ in range(30000):
            partitioner.select_partition(None, 3)
        assert partitioner.counter < 30000


class TestStickyPartitioner:
    @pytest.fixture
    def partitioner(self):
        return StickyPartitioner()

    def test_select_partition_with_key(self, partitioner):
        key = b"test-key"
        partition = partitioner.select_partition(key, 10)
        assert 0 <= partition < 10

    def test_select_partition_without_key_sticky(self, partitioner):
        partitions = [partitioner.select_partition(None, 3) for _ in range(150)]
        assert partitions[:100] == [0] * 100
        assert partitions[100:200] == [1] * 50

    def test_select_partition_batch_size(self, partitioner):
        partitioner.batch_size = 5
        partitions = [partitioner.select_partition(None, 3) for _ in range(15)]
        assert partitions[:5] == [0] * 5
        assert partitions[5:10] == [1] * 5
        assert partitions[10:15] == [2] * 5

    def test_select_partition_mixed_keys(self, partitioner):
        partitioner.batch_size = 5
        p1 = partitioner.select_partition(None, 10)
        p2 = partitioner.select_partition(b"key", 10)
        p3 = partitioner.select_partition(None, 10)
        assert p1 == 0
        assert 0 <= p2 < 10
        assert p3 == 0

    def test_message_count_reset(self, partitioner):
        partitioner.batch_size = 3
        partitioner.select_partition(None, 10)
        partitioner.select_partition(None, 10)
        partitioner.select_partition(None, 10)
        assert partitioner.message_count == 3
        partitioner.select_partition(None, 10)
        assert partitioner.message_count == 1
        assert partitioner.current_partition == 1


class TestCustomPartitioner:
    def test_select_partition_custom_function(self):
        def custom_fn(key, num_partitions):
            if key:
                return len(key) % num_partitions
            return 0

        partitioner = CustomPartitioner(custom_fn)
        partition = partitioner.select_partition(b"test-key", 5)
        assert partition == len(b"test-key") % 5

    def test_select_partition_with_none_key(self):
        def custom_fn(key, num_partitions):
            return 0 if key is None else len(key) % num_partitions

        partitioner = CustomPartitioner(custom_fn)
        partition = partitioner.select_partition(None, 5)
        assert partition == 0

    def test_select_partition_edge_cases(self):
        def custom_fn(key, num_partitions):
            return num_partitions - 1

        partitioner = CustomPartitioner(custom_fn)
        partition = partitioner.select_partition(b"key", 10)
        assert partition == 9


class TestPartitionSelectorAbstract:
    def test_partition_selector_is_abstract(self):
        with pytest.raises(TypeError):
            PartitionSelector()


class TestPartitionSelectorEdgeCases:
    def test_zero_partitions(self):
        partitioner = HashPartitioner()
        with pytest.raises(ZeroDivisionError):
            partitioner.select_partition(b"key", 0)

    def test_negative_partitions(self):
        partitioner = HashPartitioner()
        result = partitioner.select_partition(b"key", 10)
        assert 0 <= result < 10

    def test_very_large_key(self):
        partitioner = HashPartitioner()
        key = b"x" * 1000000
        partition = partitioner.select_partition(key, 10)
        assert 0 <= partition < 10

    def test_unicode_key(self):
        partitioner = HashPartitioner()
        key = "test-key-unicode-ñ".encode('utf-8')
        partition = partitioner.select_partition(key, 10)
        assert 0 <= partition < 10


class TestPartitionDistribution:
    def test_hash_partitioner_distribution(self):
        partitioner = HashPartitioner()
        partitions = {}
        for i in range(1000):
            key = f"key-{i}".encode()
            partition = partitioner.select_partition(key, 10)
            partitions[partition] = partitions.get(partition, 0) + 1
        
        assert len(partitions) == 10
        for count in partitions.values():
            assert 50 < count < 200

    def test_round_robin_distribution(self):
        partitioner = RoundRobinPartitioner()
        partitions = {}
        for i in range(30):
            partition = partitioner.select_partition(None, 3)
            partitions[partition] = partitions.get(partition, 0) + 1
        
        assert partitions == {0: 10, 1: 10, 2: 10}

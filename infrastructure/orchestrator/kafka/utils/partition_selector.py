from abc import ABC, abstractmethod
from typing import Optional
import hashlib


class PartitionSelector(ABC):
    @abstractmethod
    def select_partition(self, key: Optional[bytes], num_partitions: int) -> int:
        pass


class HashPartitioner(PartitionSelector):
    def select_partition(self, key: Optional[bytes], num_partitions: int) -> int:
        if key is None:
            return 0
        
        hash_value = self._murmur2_hash(key)
        return abs(hash_value) % num_partitions
    
    def _murmur2_hash(self, data: bytes) -> int:
        m = 0x5bd1e995
        seed = 0x9747b28c
        length = len(data)
        h = seed ^ length
        
        offset = 0
        while length >= 4:
            k = int.from_bytes(data[offset:offset+4], byteorder='little', signed=False)
            k = (k * m) & 0xFFFFFFFF
            k ^= k >> 24
            k = (k * m) & 0xFFFFFFFF
            
            h = (h * m) & 0xFFFFFFFF
            h ^= k
            
            offset += 4
            length -= 4
        
        if length == 3:
            h ^= data[offset + 2] << 16
        if length >= 2:
            h ^= data[offset + 1] << 8
        if length >= 1:
            h ^= data[offset]
            h = (h * m) & 0xFFFFFFFF
        
        h ^= h >> 13
        h = (h * m) & 0xFFFFFFFF
        h ^= h >> 15
        
        return h if h < 0x80000000 else h - 0x100000000


class RoundRobinPartitioner(PartitionSelector):
    def __init__(self):
        self.counter = 0
    
    def select_partition(self, key: Optional[bytes], num_partitions: int) -> int:
        partition = self.counter % num_partitions
        self.counter = (self.counter + 1) % (num_partitions * 10000)
        return partition


class StickyPartitioner(PartitionSelector):
    def __init__(self):
        self.current_partition = 0
        self.message_count = 0
        self.batch_size = 100
    
    def select_partition(self, key: Optional[bytes], num_partitions: int) -> int:
        if key is not None:
            hash_partitioner = HashPartitioner()
            return hash_partitioner.select_partition(key, num_partitions)
        
        if self.message_count >= self.batch_size:
            self.current_partition = (self.current_partition + 1) % num_partitions
            self.message_count = 0
        
        self.message_count += 1
        return self.current_partition


class CustomPartitioner(PartitionSelector):
    def __init__(self, partition_fn):
        self.partition_fn = partition_fn
    
    def select_partition(self, key: Optional[bytes], num_partitions: int) -> int:
        return self.partition_fn(key, num_partitions)

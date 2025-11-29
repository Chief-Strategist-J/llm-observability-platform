import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.kafka.utils.compression import (
    CompressionType,
    NoneCompressor,
    GzipCompressor,
    get_compressor
)


class TestKafkaCompression:
    def test_compression_type_enum(self):
        assert CompressionType.NONE.value == 0
        assert CompressionType.GZIP.value == 1
        assert CompressionType.SNAPPY.value == 2
        assert CompressionType.LZ4.value == 3
        assert CompressionType.ZSTD.value == 4
    
    def test_none_compressor(self):
        compressor = NoneCompressor()
        
        data = b"test data to compress"
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        
        assert compressed == data
        assert decompressed == data
    
    def test_gzip_compressor(self):
        compressor = GzipCompressor(level=6)
        
        data = b"test data to compress" * 100
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        
        assert len(compressed) < len(data)
        assert decompressed == data
    
    def test_gzip_compressor_levels(self):
        data = b"test data to compress" * 100
        
        compressor_fast = GzipCompressor(level=1)
        compressor_best = GzipCompressor(level=9)
        
        compressed_fast = compressor_fast.compress(data)
        compressed_best = compressor_best.compress(data)
        
        assert len(compressed_best) <= len(compressed_fast)
        assert compressor_fast.decompress(compressed_fast) == data
        assert compressor_best.decompress(compressed_best) == data
    
    def test_get_compressor_none(self):
        compressor = get_compressor(CompressionType.NONE)
        
        assert isinstance(compressor, NoneCompressor)
    
    def test_get_compressor_gzip(self):
        compressor = get_compressor(CompressionType.GZIP, level=6)
        
        assert isinstance(compressor, GzipCompressor)
    
    def test_compression_roundtrip(self):
        data = b"Hello, World! This is a test message." * 50
        
        compressor = GzipCompressor()
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        
        assert decompressed == data
        assert len(compressed) < len(data)
    
    @pytest.mark.parametrize("data", [
        b"short",
        b"medium length data" * 10,
        b"very long data" * 1000,
    ])
    def test_gzip_various_data_sizes(self, data):
        compressor = GzipCompressor()
        
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        
        assert decompressed == data

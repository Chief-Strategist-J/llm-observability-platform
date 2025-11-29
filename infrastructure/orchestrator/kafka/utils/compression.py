import gzip
import zlib
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

try:
    import snappy
    SNAPPY_AVAILABLE = True
except ImportError:
    SNAPPY_AVAILABLE = False

try:
    import lz4.frame
    LZ4_AVAILABLE = True
except ImportError:
    LZ4_AVAILABLE = False

try:
    import zstandard as zstd
    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False


class CompressionType(Enum):
    NONE = 0
    GZIP = 1
    SNAPPY = 2
    LZ4 = 3
    ZSTD = 4


class Compressor(ABC):
    @abstractmethod
    def compress(self, data: bytes) -> bytes:
        pass
    
    @abstractmethod
    def decompress(self, data: bytes) -> bytes:
        pass


class NoneCompressor(Compressor):
    def compress(self, data: bytes) -> bytes:
        return data
    
    def decompress(self, data: bytes) -> bytes:
        return data


class GzipCompressor(Compressor):
    def __init__(self, level: int = 6):
        self.level = level
    
    def compress(self, data: bytes) -> bytes:
        return gzip.compress(data, compresslevel=self.level)
    
    def decompress(self, data: bytes) -> bytes:
        return gzip.decompress(data)


class SnappyCompressor(Compressor):
    def __init__(self):
        if not SNAPPY_AVAILABLE:
            raise ImportError("python-snappy is not installed")
    
    def compress(self, data: bytes) -> bytes:
        return snappy.compress(data)
    
    def decompress(self, data: bytes) -> bytes:
        return snappy.decompress(data)


class LZ4Compressor(Compressor):
    def __init__(self, level: int = 0):
        if not LZ4_AVAILABLE:
            raise ImportError("lz4 is not installed")
        self.level = level
    
    def compress(self, data: bytes) -> bytes:
        return lz4.frame.compress(data, compression_level=self.level)
    
    def decompress(self, data: bytes) -> bytes:
        return lz4.frame.decompress(data)


class ZstdCompressor(Compressor):
    def __init__(self, level: int = 3):
        if not ZSTD_AVAILABLE:
            raise ImportError("zstandard is not installed")
        self.level = level
        self.compressor = zstd.ZstdCompressor(level=self.level)
        self.decompressor = zstd.ZstdDecompressor()
    
    def compress(self, data: bytes) -> bytes:
        return self.compressor.compress(data)
    
    def decompress(self, data: bytes) -> bytes:
        return self.decompressor.decompress(data)


def get_compressor(compression_type: CompressionType, **kwargs) -> Compressor:
    if compression_type == CompressionType.NONE:
        return NoneCompressor()
    elif compression_type == CompressionType.GZIP:
        return GzipCompressor(**kwargs)
    elif compression_type == CompressionType.SNAPPY:
        return SnappyCompressor()
    elif compression_type == CompressionType.LZ4:
        return LZ4Compressor(**kwargs)
    elif compression_type == CompressionType.ZSTD:
        return ZstdCompressor(**kwargs)
    else:
        raise ValueError(f"Unknown compression type: {compression_type}")

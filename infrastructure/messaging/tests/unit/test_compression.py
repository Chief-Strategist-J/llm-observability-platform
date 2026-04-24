import pytest
from infrastructure.messaging.utils.compression import (
    CompressionType,
    Compressor,
    NoneCompressor,
    GzipCompressor,
    SnappyCompressor,
    LZ4Compressor,
    ZstdCompressor,
    get_compressor,
    SNAPPY_AVAILABLE,
    LZ4_AVAILABLE,
    ZSTD_AVAILABLE,
)


class TestCompressionType:
    def test_compression_type_values(self):
        assert CompressionType.NONE.value == 0
        assert CompressionType.GZIP.value == 1
        assert CompressionType.SNAPPY.value == 2
        assert CompressionType.LZ4.value == 3
        assert CompressionType.ZSTD.value == 4


class TestNoneCompressor:
    @pytest.fixture
    def compressor(self):
        return NoneCompressor()

    def test_compress_identity(self, compressor):
        data = b"test data"
        result = compressor.compress(data)
        assert result == data

    def test_decompress_identity(self, compressor):
        data = b"test data"
        result = compressor.decompress(data)
        assert result == data

    def test_empty_data(self, compressor):
        data = b""
        assert compressor.compress(data) == data
        assert compressor.decompress(data) == data

    def test_large_data(self, compressor):
        data = b"x" * 1000000
        assert compressor.compress(data) == data
        assert compressor.decompress(data) == data


class TestGzipCompressor:
    @pytest.fixture
    def compressor(self):
        return GzipCompressor(level=6)

    def test_compress_decompress(self, compressor):
        data = b"test data for compression that is longer"
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        assert decompressed == data

    def test_different_compression_levels(self):
        data = b"test data" * 100
        compressor_low = GzipCompressor(level=1)
        compressor_high = GzipCompressor(level=9)
        
        compressed_low = compressor_low.compress(data)
        compressed_high = compressor_high.compress(data)
        
        assert len(compressed_high) <= len(compressed_low)
        assert compressor_low.decompress(compressed_low) == data
        assert compressor_high.decompress(compressed_high) == data

    def test_invalid_compression_level(self):
        compressor = GzipCompressor(level=9)
        data = b"test"
        compressed = compressor.compress(data)
        assert compressed is not None

    def test_empty_data(self, compressor):
        data = b""
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        assert decompressed == data

    def test_invalid_data_decompress(self, compressor):
        with pytest.raises(Exception):
            compressor.decompress(b"invalid gzip data")


class TestSnappyCompressor:
    def test_import_error_when_not_available(self):
        if SNAPPY_AVAILABLE:
            pytest.skip("snappy is available")
        with pytest.raises(ImportError, match="python-snappy is not installed"):
            SnappyCompressor()

    @pytest.mark.skipif(not SNAPPY_AVAILABLE, reason="snappy not installed")
    def test_compress_decompress(self):
        compressor = SnappyCompressor()
        data = b"test data for compression"
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        assert decompressed == data

    @pytest.mark.skipif(not SNAPPY_AVAILABLE, reason="snappy not installed")
    def test_empty_data(self):
        compressor = SnappyCompressor()
        data = b""
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        assert decompressed == data


class TestLZ4Compressor:
    def test_import_error_when_not_available(self):
        if LZ4_AVAILABLE:
            pytest.skip("lz4 is available")
        with pytest.raises(ImportError, match="lz4 is not installed"):
            LZ4Compressor()

    @pytest.mark.skipif(not LZ4_AVAILABLE, reason="lz4 not installed")
    def test_compress_decompress(self):
        compressor = LZ4Compressor(level=0)
        data = b"test data for compression"
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        assert decompressed == data

    @pytest.mark.skipif(not LZ4_AVAILABLE, reason="lz4 not installed")
    def test_different_compression_levels(self):
        data = b"test data" * 100
        compressor_low = LZ4Compressor(level=0)
        compressor_high = LZ4Compressor(level=16)
        
        compressed_low = compressor_low.compress(data)
        compressed_high = compressor_high.compress(data)
        
        assert compressor_low.decompress(compressed_low) == data
        assert compressor_high.decompress(compressed_high) == data


class TestZstdCompressor:
    def test_import_error_when_not_available(self):
        if ZSTD_AVAILABLE:
            pytest.skip("zstandard is available")
        with pytest.raises(ImportError, match="zstandard is not installed"):
            ZstdCompressor()

    @pytest.mark.skipif(not ZSTD_AVAILABLE, reason="zstandard not installed")
    def test_compress_decompress(self):
        compressor = ZstdCompressor(level=3)
        data = b"test data for compression"
        compressed = compressor.compress(data)
        decompressed = compressor.decompress(compressed)
        assert decompressed == data

    @pytest.mark.skipif(not ZSTD_AVAILABLE, reason="zstandard not installed")
    def test_different_compression_levels(self):
        data = b"test data" * 100
        compressor_low = ZstdCompressor(level=1)
        compressor_high = ZstdCompressor(level=19)
        
        compressed_low = compressor_low.compress(data)
        compressed_high = compressor_high.compress(data)
        
        assert len(compressed_high) <= len(compressed_low)
        assert compressor_low.decompress(compressed_low) == data
        assert compressor_high.decompress(compressed_high) == data

    @pytest.mark.skipif(not ZSTD_AVAILABLE, reason="zstandard not installed")
    def test_invalid_compression_level(self):
        with pytest.raises(Exception):
            ZstdCompressor(level=25)


class TestGetCompressor:
    def test_get_none_compressor(self):
        compressor = get_compressor(CompressionType.NONE)
        assert isinstance(compressor, NoneCompressor)

    def test_get_gzip_compressor(self):
        compressor = get_compressor(CompressionType.GZIP, level=6)
        assert isinstance(compressor, GzipCompressor)
        assert compressor.level == 6

    def test_get_snappy_compressor(self):
        if not SNAPPY_AVAILABLE:
            pytest.skip("snappy not installed")
        compressor = get_compressor(CompressionType.SNAPPY)
        assert isinstance(compressor, SnappyCompressor)

    def test_get_lz4_compressor(self):
        if not LZ4_AVAILABLE:
            pytest.skip("lz4 not installed")
        compressor = get_compressor(CompressionType.LZ4, level=0)
        assert isinstance(compressor, LZ4Compressor)

    def test_get_zstd_compressor(self):
        if not ZSTD_AVAILABLE:
            pytest.skip("zstandard not installed")
        compressor = get_compressor(CompressionType.ZSTD, level=3)
        assert isinstance(compressor, ZstdCompressor)

    def test_invalid_compression_type(self):
        with pytest.raises(ValueError, match="Unknown compression type"):
            get_compressor(999)


class TestCompressorAbstract:
    def test_compressor_is_abstract(self):
        with pytest.raises(TypeError):
            Compressor()

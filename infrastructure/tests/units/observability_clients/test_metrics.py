"""
Unit tests for functional metrics module

Tests pure functions and metrics client
"""

import pytest
from unittest.mock import Mock, MagicMock
from infrastructure.observability.clients.python.metrics import (
    create_counter,
    create_histogram,
    record_counter,
    record_histogram,
    MetricsClient,
)


class TestPureFunctions:
    """Test pure functional components"""
    
    def test_create_counter(self):
        """Test counter creation"""
        meter = Mock()
        counter = Mock()
        meter.create_counter.return_value = counter
        
        result = create_counter(meter, "test_counter", "Test description")
        
        meter.create_counter.assert_called_once_with(
            name="test_counter",
            description="Test description"
        )
        assert result == counter
    
    def test_create_counter_default_description(self):
        """Test counter creation with default description"""
        meter = Mock()
        create_counter(meter, "my_counter")
        
        meter.create_counter.assert_called_once_with(
            name="my_counter",
            description="Counter for my_counter"
        )
    
    def test_create_histogram(self):
        """Test histogram creation"""
        meter = Mock()
        histogram = Mock()
        meter.create_histogram.return_value = histogram
        
        result = create_histogram(meter, "test_histogram", "Test desc")
        
        meter.create_histogram.assert_called_once_with(
            name="test_histogram",
            description="Test desc"
        )
        assert result == histogram
    
    def test_record_counter_default_value(self):
        """Test recording counter with default value"""
        counter = Mock()
        
        record_counter(counter)
        
        counter.add.assert_called_once_with(1, attributes={})
    
    def test_record_counter_with_value_and_attrs(self):
        """Test recording counter with value and attributes"""
        counter = Mock()
        attrs = {"endpoint": "/api/users", "method": "GET"}
        
        record_counter(counter, value=5, attributes=attrs)
        
        counter.add.assert_called_once_with(5, attributes=attrs)
    
    def test_record_histogram(self):
        """Test recording histogram value"""
        histogram = Mock()
        attrs = {"status": "200"}
        
        record_histogram(histogram, value=0.045, attributes=attrs)
        
        histogram.record.assert_called_once_with(0.045, attributes=attrs)


class TestMetricsClient:
    """Test MetricsClient class"""
    
    def test_initialization(self):
        """Test client initialization"""
        meter = Mock()
        client = MetricsClient(meter)
        
        assert client.meter == meter
        assert client._counters == {}
        assert client._histograms == {}
    
    def test_counter_creates_instrument(self):
        """Test counter creates instrument on first use"""
        meter = Mock()
        counter_instrument = Mock()
        meter.create_counter.return_value = counter_instrument
        
        client = MetricsClient(meter)
        client.counter("requests_total")
        
        meter.create_counter.assert_called_once()
        counter_instrument.add.assert_called_once()
    
    def test_counter_reuses_instrument(self):
        """Test counter reuses existing instrument"""
        meter = Mock()
        counter_instrument = Mock()
        meter.create_counter.return_value = counter_instrument
        
        client = MetricsClient(meter)
        client.counter("requests_total", 1)
        client.counter("requests_total", 1)
        
        # Should only create once
        meter.create_counter.assert_called_once()
        # But record twice
        assert counter_instrument.add.call_count == 2
    
    def test_counter_with_attributes(self):
        """Test counter with attributes"""
        meter = Mock()
        counter_instrument = Mock()
        meter.create_counter.return_value = counter_instrument
        
        client = MetricsClient(meter)
        attrs = {"endpoint": "/api", "status": "200"}
        client.counter("http_requests", value=5, attributes=attrs)
        
        counter_instrument.add.assert_called_once_with(5, attributes=attrs)
    
    def test_histogram_creates_instrument(self):
        """Test histogram creates instrument on first use"""
        meter = Mock()
        histogram_instrument = Mock()
        meter.create_histogram.return_value = histogram_instrument
        
        client = MetricsClient(meter)
        client.histogram("request_duration", 0.123)
        
        meter.create_histogram.assert_called_once()
        histogram_instrument.record.assert_called_once_with(0.123, attributes={})
    
    def test_histogram_reuses_instrument(self):
        """Test histogram reuses existing instrument"""
        meter = Mock()
        histogram_instrument = Mock()
        meter.create_histogram.return_value = histogram_instrument
        
        client = MetricsClient(meter)
        client.histogram("latency", 0.1)
        client.histogram("latency", 0.2)
        
        # Should only create once
        meter.create_histogram.assert_called_once()
        # But record twice
        assert histogram_instrument.record.call_count == 2
    
    def test_multiple_metrics(self):
        """Test multiple different metrics"""
        meter = Mock()
        counter = Mock()
        histogram = Mock()
        meter.create_counter.return_value = counter
        meter.create_histogram.return_value = histogram
        
        client = MetricsClient(meter)
        client.counter("metric1")
        client.histogram("metric2", 1.5)
        client.counter("metric3")
        
        assert len(client._counters) == 2
        assert len(client._histograms) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

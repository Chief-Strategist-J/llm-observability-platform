"""
Unit tests for functional tracing module

Tests pure functions and tracer client
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from contextlib import contextmanager
from infrastructure.observability.clients.python.tracer import (
    create_span,
    set_span_attributes,
    span_context,
    TracerClient,
)


class TestPureFunctions:
    """Test pure functional components"""
    
    def test_create_span_without_attributes(self):
        """Test span creation without attributes"""
        tracer = Mock()
        span = Mock()
        tracer.start_span.return_value = span
        
        result = create_span(tracer, "test-span")
        
        tracer.start_span.assert_called_once_with("test-span")
        assert result == span
    
    def test_create_span_with_attributes(self):
        """Test span creation with attributes"""
        tracer = Mock()
        span = Mock()
        tracer.start_span.return_value = span
        
        attrs = {"user_id": 123, "action": "login"}
        result = create_span(tracer, "user-action", attributes=attrs)
        
        tracer.start_span.assert_called_once_with("user-action")
        assert span.set_attribute.call_count == 2
        assert result == span
    
    def test_set_span_attributes(self):
        """Test setting multiple span attributes"""
        span = Mock()
        attrs = {"key1": "value1", "key2": 42}
        
        set_span_attributes(span, attrs)
        
        assert span.set_attribute.call_count == 2
        span.set_attribute.assert_any_call("key1", "value1")
        span.set_attribute.assert_any_call("key2", 42)
    
    def test_span_context_success(self):
        """Test span context manager with successful execution"""
        tracer = Mock()
        span = Mock()
        tracer.start_span.return_value = span
        
        with span_context(tracer, "test-span") as s:
            assert s == span
            # Do some work
            pass
        
        span.end.assert_called_once()
        span.record_exception.assert_not_called()
    
    def test_span_context_with_exception(self):
        """Test span context manager when exception occurs"""
        tracer = Mock()
        span = Mock()
        tracer.start_span.return_value = span
        
        with pytest.raises(ValueError):
            with span_context(tracer, "test-span"):
                raise ValueError("Test error")
        
        span.record_exception.assert_called_once()
        span.set_status.assert_called_once()
        span.end.assert_called_once()


class TestTracerClient:
    """Test TracerClient class"""
    
    def test_initialization(self):
        """Test tracer client initialization"""
        tracer = Mock()
        client = TracerClient(tracer)
        
        assert client.tracer == tracer
    
    def test_start_span(self):
        """Test starting a span"""
        tracer = Mock()
        span = Mock()
        tracer.start_span.return_value = span
        
        client = TracerClient(tracer)
        result = client.start_span("my-span")
        
        tracer.start_span.assert_called_once_with("my-span")
        assert result == span
    
    def test_start_span_with_attributes(self):
        """Test starting a span with attributes"""
        tracer = Mock()
        span = Mock()
        tracer.start_span.return_value = span
        
        client = TracerClient(tracer)
        attrs = {"transaction_id": "abc123"}
        result = client.start_span("payment", attributes=attrs)
        
        span.set_attribute.assert_called_once_with("transaction_id", "abc123")
    
    def test_start_as_current_span(self):
        """Test starting span as current context"""
        tracer = Mock()
        span = Mock()
        tracer.start_span.return_value = span
        
        client = TracerClient(tracer)
        
        with client.start_as_current_span("db-query") as s:
            assert s == span
        
        span.end.assert_called_once()


class TestIntegration:
    """Integration tests for tracer module"""
    
    def test_nested_spans(self):
        """Test nested span contexts"""
        tracer = Mock()
        parent_span = Mock()
        child_span = Mock()
        
        # Setup mock to return different spans for each call
        tracer.start_span.side_effect = [parent_span, child_span]
        
        client = TracerClient(tracer)
        
        with client.start_as_current_span("parent"):
            with client.start_as_current_span("child"):
                pass
        
        assert parent_span.end.called
        assert child_span.end.called
    
    def test_span_with_attributes_and_exception(self):
        """Test span with both attributes and exception handling"""
        tracer = Mock()
        span = Mock()
        tracer.start_span.return_value = span
        
        attrs = {"user_id": 456}
        
        with pytest.raises(RuntimeError):
            with span_context(tracer, "risky-operation", attributes=attrs):
                span.set_attribute.assert_called_with("user_id", 456)
                raise RuntimeError("Something went wrong")
        
        span.record_exception.assert_called_once()
        span.end.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

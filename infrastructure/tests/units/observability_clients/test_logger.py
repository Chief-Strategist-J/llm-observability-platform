"""
Unit tests for functional logging module

Tests pure functions and composable logger
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from infrastructure.observability.clients.python.logger import (
    create_logger,
    format_structured_log,
    log_with_context,
    create_log_functions,
    StructuredLogger,
)


class TestPureFunctions:
    """Test pure functional components"""
    
    def test_create_logger(self):
        """Test logger creation is deterministic"""
        logger1 = create_logger("test-service", logging.INFO)
        logger2 = create_logger("test-service", logging.INFO)
        
        assert logger1.name == logger2.name == "test-service"
        assert logger1.level == logger2.level == logging.INFO
    
    def test_format_structured_log_empty(self):
        """Test formatting with no data"""
        result = format_structured_log("Test message", {})
        assert result == "Test message"
    
    def test_format_structured_log_with_data(self):
        """Test formatting with structured data"""
        result = format_structured_log(
            "User action",
            {"user_id": 123, "action": "login"}
        )
        assert "User action" in result
        assert "user_id=123" in result
        assert "action=login" in result
    
    def test_format_structured_log_deterministic(self):
        """Test formatting is deterministic (sorted keys)"""
        data = {"z": 1, "a": 2, "m": 3}
        result = format_structured_log("Test", data)
        
        # Keys should be in sorted order
        assert result.index("a=2") < result.index("m=3") < result.index("z=1")


class TestLogFunctions:
    """Test log function creation and execution"""
    
    def test_create_log_functions(self):
        """Test log function factory"""
        logger = Mock(spec=logging.Logger)
        log_fns = create_log_functions(logger)
        
        assert 'info' in log_fns
        assert 'error' in log_fns
        assert 'warning' in log_fns
        assert 'debug' in log_fns
        assert 'critical' in log_fns
    
    def test_log_with_context(self):
        """Test logging with context data"""
        logger = Mock(spec=logging.Logger)
        
        log_with_context(logger, logging.INFO, "Test message", user_id=123)
        
        logger.log.assert_called_once_with(
            logging.INFO,
            "Test message",
            extra={"user_id": 123}
        )


class TestStructuredLogger:
    """Test StructuredLogger class"""
    
    def test_initialization(self):
        """Test logger initialization"""
        logger = StructuredLogger("test-service")
        assert logger._logger.name == "test-service"
        assert len(logger._log_fns) == 5
    
    @patch('infrastructure.observability.clients.python.logger.create_logger')
    def test_info_logging(self, mock_create_logger):
        """Test info level logging"""
        mock_logger = MagicMock()
        mock_create_logger.return_value = mock_logger
        
        logger = StructuredLogger("test-service")
        logger.info("Test info", user_id=123)
        
        mock_logger.log.assert_called_once()
        args, kwargs = mock_logger.log.call_args
        assert args[0] == logging.INFO
        assert args[1] == "Test info"
        assert kwargs['extra'] == {"user_id": 123}
    
    @patch('infrastructure.observability.clients.python.logger.create_logger')
    def test_error_logging(self, mock_create_logger):
        """Test error level logging"""
        mock_logger = MagicMock()
        mock_create_logger.return_value = mock_logger
        
        logger = StructuredLogger("test-service")
        logger.error("Test error", error_code="E001")
        
        mock_logger.log.assert_called_once()
        args, kwargs = mock_logger.log.call_args
        assert args[0] == logging.ERROR
        assert args[1] == "Test error"
    
    @patch('infrastructure.observability.clients.python.logger.create_logger')
    def test_warning_logging(self, mock_create_logger):
        """Test warning level logging"""
        mock_logger = MagicMock()
        mock_create_logger.return_value = mock_logger
        
        logger = StructuredLogger("test-service")
        logger.warning("Test warning")
        
        args, _ = mock_logger.log.call_args
        assert args[0] == logging.WARNING
    
    @patch('infrastructure.observability.clients.python.logger.create_logger')
    def test_debug_logging(self, mock_create_logger):
        """Test debug level logging*/
        mock_logger = MagicMock()
        mock_create_logger.return_value = mock_logger
        
        logger = StructuredLogger("test-service")
        logger.debug("Debug message")
        
        args, _ = mock_logger.log.call_args
        assert args[0] == logging.DEBUG


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

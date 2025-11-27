import logging
import time
import uuid
from typing import Any, Dict, Optional
from functools import wraps

class LogQLLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.trace_id: Optional[str] = None
    
    def set_trace_id(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        return self.trace_id
    
    def _format_message(self, event: str, **kwargs) -> str:
        parts = [f"event={event}"]
        
        if self.trace_id:
            parts.append(f"trace_id={self.trace_id}")
        
        for key, value in kwargs.items():
            if value is not None:
                if isinstance(value, str):
                    parts.append(f'{key}="{value}"')
                else:
                    parts.append(f"{key}={value}")
        
        return " ".join(parts)
    
    def debug(self, event: str, **kwargs):
        self.logger.debug(self._format_message(event, **kwargs))
    
    def info(self, event: str, **kwargs):
        self.logger.info(self._format_message(event, **kwargs))
    
    def warning(self, event: str, **kwargs):
        self.logger.warning(self._format_message(event, **kwargs))
    
    def error(self, event: str, error: Optional[Exception] = None, **kwargs):
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_msg"] = str(error)
        self.logger.error(self._format_message(event, **kwargs))
    
    def exception(self, event: str, error: Exception, **kwargs):
        kwargs["error_type"] = type(error).__name__
        kwargs["error_msg"] = str(error)
        self.logger.exception(self._format_message(event, **kwargs))

def trace_operation(operation_name: str):
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            log = LogQLLogger(func.__module__)
            trace_id = log.set_trace_id()
            start_time = time.time()
            
            log.info("operation_start", operation=operation_name, function=func.__name__)
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                log.info("operation_complete", operation=operation_name, duration_ms=int(duration * 1000))
                return result
            except Exception as e:
                duration = time.time() - start_time
                log.exception("operation_failed", error=e, operation=operation_name, duration_ms=int(duration * 1000))
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            log = LogQLLogger(func.__module__)
            trace_id = log.set_trace_id()
            start_time = time.time()
            
            log.info("operation_start", operation=operation_name, function=func.__name__)
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log.info("operation_complete", operation=operation_name, duration_ms=int(duration * 1000))
                return result
            except Exception as e:
                duration = time.time() - start_time
                log.exception("operation_failed", error=e, operation=operation_name, duration_ms=int(duration * 1000))
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator

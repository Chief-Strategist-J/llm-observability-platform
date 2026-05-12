"""Shared validation utilities with single responsibility."""

from typing import Any, Dict, List, Optional
import re
from opentelemetry import trace

from shared.errors.codes import validation_failed

_tracer = trace.get_tracer(__name__)


class ValidationError(Exception):
    """Custom validation error with detailed information"""
    def __init__(self, field: str, message: str, fix_suggestion: str):
        self.field = field
        self.message = message
        self.fix_suggestion = fix_suggestion
        super().__init__(f"{field}: {message}. {fix_suggestion}")


class Preconditions:
    """Precondition validators with single responsibility"""
    
    @staticmethod
    def validate_non_empty_string(value: Any, field_name: str) -> None:
        """Validate that value is a non-empty string"""
        with _tracer.start_as_current_span("validate_non_empty_string") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "validation")
            span.set_attribute("api.version", "v1")
            span.set_attribute("validation.field", field_name)
            
            if value is None or (isinstance(value, str) and not value.strip()):
                span.set_attribute("validation.result", "failed")
                raise ValidationError(
                    field=field_name,
                    message=f"{field_name} cannot be empty",
                    fix_suggestion=f"Provide a non-empty {field_name}"
                )
            
            span.set_attribute("validation.result", "success")
    
    @staticmethod
    def validate_non_negative(value: int, field_name: str) -> None:
        """Validate that value is non-negative"""
        with _tracer.start_as_current_span("validate_non_negative") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "validation")
            span.set_attribute("api.version", "v1")
            span.set_attribute("validation.field", field_name)
            span.set_attribute("validation.value", str(value))
            
            if value < 0:
                span.set_attribute("validation.result", "failed")
                raise ValidationError(
                    field=field_name,
                    message=f"{field_name} must be non-negative",
                    fix_suggestion=f"Provide a {field_name} >= 0"
                )
            
            span.set_attribute("validation.result", "success")
    
    @staticmethod
    def validate_positive(value: int, field_name: str) -> None:
        """Validate that value is positive"""
        with _tracer.start_as_current_span("validate_positive") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "validation")
            span.set_attribute("api.version", "v1")
            span.set_attribute("validation.field", field_name)
            span.set_attribute("validation.value", str(value))
            
            if value <= 0:
                span.set_attribute("validation.result", "failed")
                raise ValidationError(
                    field=field_name,
                    message=f"{field_name} must be positive",
                    fix_suggestion=f"Provide a {field_name} > 0"
                )
            
            span.set_attribute("validation.result", "success")
    
    @staticmethod
    def validate_max_length(value: str, field_name: str, max_length: int) -> None:
        """Validate string length"""
        with _tracer.start_as_current_span("validate_max_length") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "validation")
            span.set_attribute("api.version", "v1")
            span.set_attribute("validation.field", field_name)
            span.set_attribute("validation.max_length", str(max_length))
            span.set_attribute("validation.length", str(len(value) if value else 0))
            
            if value and len(value) > max_length:
                span.set_attribute("validation.result", "failed")
                raise ValidationError(
                    field=field_name,
                    message=f"{field_name} exceeds maximum length of {max_length}",
                    fix_suggestion=f"Provide {field_name} with length <= {max_length}"
                )
            
            span.set_attribute("validation.result", "success")
    
    @staticmethod
    def validate_regex(value: str, field_name: str, pattern: str, description: str) -> None:
        """Validate string against regex pattern"""
        with _tracer.start_as_current_span("validate_regex") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "validation")
            span.set_attribute("api.version", "v1")
            span.set_attribute("validation.field", field_name)
            span.set_attribute("validation.pattern", pattern)
            
            if value and not re.match(pattern, value):
                span.set_attribute("validation.result", "failed")
                raise ValidationError(
                    field=field_name,
                    message=f"{field_name} does not match required pattern",
                    fix_suggestion=f"Provide {field_name} that matches: {description}"
                )
            
            span.set_attribute("validation.result", "success")
    
    @staticmethod
    def validate_in_range(value: int, field_name: str, min_val: int, max_val: int) -> None:
        """Validate that value is within range"""
        with _tracer.start_as_current_span("validate_in_range") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "validation")
            span.set_attribute("api.version", "v1")
            span.set_attribute("validation.field", field_name)
            span.set_attribute("validation.min", str(min_val))
            span.set_attribute("validation.max", str(max_val))
            span.set_attribute("validation.value", str(value))
            
            if not (min_val <= value <= max_val):
                span.set_attribute("validation.result", "failed")
                raise ValidationError(
                    field=field_name,
                    message=f"{field_name} must be between {min_val} and {max_val}",
                    fix_suggestion=f"Provide {field_name} in range [{min_val}, {max_val}]"
                )
            
            span.set_attribute("validation.result", "success")
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
        """Validate that all required fields are present"""
        with _tracer.start_as_current_span("validate_required_fields") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "validation")
            span.set_attribute("api.version", "v1")
            span.set_attribute("validation.required_count", str(len(required_fields)))
            
            missing_fields = [field for field in required_fields if field not in data or data[field] is None]
            
            if missing_fields:
                span.set_attribute("validation.result", "failed")
                span.set_attribute("validation.missing_fields", missing_fields)
                raise ValidationError(
                    field="required_fields",
                    message=f"Missing required fields: {', '.join(missing_fields)}",
                    fix_suggestion=f"Provide all required fields: {', '.join(required_fields)}"
                )
            
            span.set_attribute("validation.result", "success")


class Postconditions:
    """Postcondition validators with single responsibility"""
    
    @staticmethod
    def validate_not_none(value: Any, field_name: str) -> None:
        """Validate that value is not None"""
        with _tracer.start_as_current_span("validate_not_none") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "validation")
            span.set_attribute("api.version", "v1")
            span.set_attribute("validation.field", field_name)
            
            if value is None:
                span.set_attribute("validation.result", "failed")
                raise ValidationError(
                    field=field_name,
                    message=f"{field_name} cannot be None after operation",
                    fix_suggestion=f"Ensure {field_name} is properly initialized"
                )
            
            span.set_attribute("validation.result", "success")
    
    @staticmethod
    def validate_list_not_empty(value: List[Any], field_name: str) -> None:
        """Validate that list is not empty"""
        with _tracer.start_as_current_span("validate_list_not_empty") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "validation")
            span.set_attribute("api.version", "v1")
            span.set_attribute("validation.field", field_name)
            
            if not value:
                span.set_attribute("validation.result", "failed")
                raise ValidationError(
                    field=field_name,
                    message=f"{field_name} cannot be empty after operation",
                    fix_suggestion=f"Ensure {field_name} contains expected items"
                )
            
            span.set_attribute("validation.result", "success")
    
    @staticmethod
    def validate_count_matches(value: List[Any], field_name: str, expected_count: int) -> None:
        """Validate that list count matches expected"""
        with _tracer.start_as_current_span("validate_count_matches") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "validation")
            span.set_attribute("api.version", "v1")
            span.set_attribute("validation.field", field_name)
            span.set_attribute("validation.expected_count", str(expected_count))
            span.set_attribute("validation.actual_count", str(len(value)))
            
            if len(value) != expected_count:
                span.set_attribute("validation.result", "failed")
                raise ValidationError(
                    field=field_name,
                    message=f"{field_name} count ({len(value)}) does not match expected ({expected_count})",
                    fix_suggestion=f"Ensure {field_name} contains exactly {expected_count} items"
                )
            
            span.set_attribute("validation.result", "success")

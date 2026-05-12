"""Pure validation functions with no side effects."""

from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import ValidationError as PydanticValidationError


def validate_event_record(event_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate event record data structure."""
    required_fields = ['topic', 'partition', 'offset', 'value', 'timestamp']
    
    # Check required fields
    for field in required_fields:
        if field not in event_data:
            return False, f"Missing required field: {field}"
    
    # Validate field types
    if not isinstance(event_data['topic'], str) or not event_data['topic'].strip():
        return False, "Topic must be a non-empty string"
    
    if not isinstance(event_data['partition'], int) or event_data['partition'] < 0:
        return False, "Partition must be a non-negative integer"
    
    if not isinstance(event_data['offset'], int) or event_data['offset'] < 0:
        return False, "Offset must be a non-negative integer"
    
    # Validate timestamp
    timestamp = event_data['timestamp']
    if isinstance(timestamp, str):
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            return False, "Invalid timestamp format, use ISO 8601"
    elif not isinstance(timestamp, (int, float, datetime)):
        return False, "Timestamp must be ISO string, number, or datetime"
    
    # Validate optional fields
    if 'key' in event_data and event_data['key'] is not None:
        if not isinstance(event_data['key'], str):
            return False, "Key must be a string or null"
    
    if 'headers' in event_data and event_data['headers'] is not None:
        if not isinstance(event_data['headers'], dict):
            return False, "Headers must be a dictionary or null"
    
    return True, None


def validate_schema_request(schema_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate schema registration request."""
    required_fields = ['subject', 'schema', 'schema_type']
    
    # Check required fields
    for field in required_fields:
        if field not in schema_data:
            return False, f"Missing required field: {field}"
    
    # Validate subject
    subject = schema_data['subject']
    if not isinstance(subject, str) or not subject.strip():
        return False, "Subject must be a non-empty string"
    
    if len(subject) > 255:
        return False, "Subject name too long (max 255 characters)"
    
    # Validate schema type
    schema_type = schema_data['schema_type']
    valid_types = ['AVRO', 'JSON', 'PROTOBUF']
    if schema_type not in valid_types:
        return False, f"Invalid schema type: {schema_type}. Must be one of {valid_types}"
    
    # Validate schema content
    schema = schema_data['schema']
    if not isinstance(schema, str) or not schema.strip():
        return False, "Schema must be a non-empty string"
    
    # Basic schema validation based on type
    if schema_type == 'AVRO':
        if not schema.strip().startswith(('{"type":', '{')):
            return False, "AVRO schema must be valid JSON"
    elif schema_type == 'JSON':
        try:
            import json
            json.loads(schema)
        except json.JSONDecodeError:
            return False, "JSON schema must be valid JSON"
    
    return True, None


def validate_batch_request(batch_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Validate batch processing request."""
    if 'records' not in batch_data:
        return False, "Missing required field: records"
    
    records = batch_data['records']
    if not isinstance(records, list):
        return False, "Records must be an array"
    
    if len(records) == 0:
        return False, "Records array cannot be empty"
    
    if len(records) > 1000:
        return False, "Batch size too large (max 1000 records)"
    
    # Validate each record
    for i, record in enumerate(records):
        is_valid, error = validate_event_record(record)
        if not is_valid:
            return False, f"Invalid record at index {i}: {error}"
    
    return True, None


def validate_pagination_params(params: Dict[str, Any]) -> tuple[bool, Optional[str], Dict[str, Any]]:
    """Validate pagination parameters."""
    cleaned = {}
    
    # Validate limit
    if 'limit' in params:
        try:
            limit = int(params['limit'])
            if limit < 1:
                return False, "Limit must be at least 1", {}
            if limit > 1000:
                return False, "Limit cannot exceed 1000", {}
            cleaned['limit'] = limit
        except ValueError:
            return False, "Invalid limit parameter", {}
    else:
        cleaned['limit'] = 100  # default
    
    # Validate offset
    if 'offset' in params:
        try:
            offset = int(params['offset'])
            if offset < 0:
                return False, "Offset cannot be negative", {}
            cleaned['offset'] = offset
        except ValueError:
            return False, "Invalid offset parameter", {}
    else:
        cleaned['offset'] = 0  # default
    
    return True, None, cleaned

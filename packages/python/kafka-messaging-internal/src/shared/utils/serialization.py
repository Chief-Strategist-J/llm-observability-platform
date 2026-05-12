"""Pure serialization utilities with no side effects."""

import json
from typing import Any, Dict, Optional
from base64 import b64encode, b64decode


def serialize_json(data: Any) -> str:
    """Serialize data to JSON string."""
    try:
        return json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    except (TypeError, ValueError) as e:
        raise ValueError(f"JSON serialization failed: {e}")


def deserialize_json(json_str: str) -> Any:
    """Deserialize JSON string to Python object."""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON deserialization failed: {e}")


def serialize_to_base64(data: Any) -> str:
    """Serialize data to JSON and encode to base64."""
    json_str = serialize_json(data)
    json_bytes = json_str.encode('utf-8')
    return b64encode(json_bytes).decode('ascii')


def deserialize_from_base64(base64_str: str) -> Any:
    """Decode base64 string and deserialize from JSON."""
    try:
        json_bytes = b64decode(base64_str.encode('ascii'))
        json_str = json_bytes.decode('utf-8')
        return deserialize_json(json_str)
    except Exception as e:
        raise ValueError(f"Base64 deserialization failed: {e}")


def normalize_headers(headers: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """Normalize headers to string values."""
    if not headers:
        return {}
    
    normalized = {}
    for key, value in headers.items():
        if isinstance(value, str):
            normalized[key] = value
        elif isinstance(value, (int, float, bool)):
            normalized[key] = str(value)
        else:
            normalized[key] = serialize_json(value)
    
    return normalized


def sanitize_topic_name(topic: str) -> str:
    """Sanitize topic name according to Kafka naming rules."""
    if not isinstance(topic, str):
        raise ValueError("Topic name must be a string")
    
    # Remove invalid characters and normalize
    sanitized = topic.strip().lower()
    
    # Replace spaces and invalid characters with underscores
    invalid_chars = [' ', '/', '\\', ',', '\0', ':', '"', '\'', '`', '(', ')', '[', ']', '{', '}']
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Remove consecutive underscores
    while '__' in sanitized:
        sanitized = sanitized.replace('__', '_')
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Validate length
    if len(sanitized) == 0:
        raise ValueError("Topic name cannot be empty after sanitization")
    
    if len(sanitized) > 249:
        raise ValueError("Topic name too long (max 249 characters)")
    
    return sanitized


def extract_event_metadata(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metadata from event data."""
    metadata = {}
    
    # Standard metadata fields
    metadata_fields = ['event_type', 'status', 'retry_count', 'created_at', 'updated_at']
    for field in metadata_fields:
        if field in event_data:
            metadata[field] = event_data[field]
    
    # Extract from headers if present
    if 'headers' in event_data and isinstance(event_data['headers'], dict):
        headers = event_data['headers']
        metadata_headers = {}
        for key, value in headers.items():
            if key.startswith('x-') or key.startswith('meta-'):
                metadata_headers[key] = value
        if metadata_headers:
            metadata['headers'] = metadata_headers
    
    return metadata

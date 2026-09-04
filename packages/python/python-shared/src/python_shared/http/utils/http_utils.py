import uuid
from typing import Dict, Optional
from python_shared.http.constants import HTTP_CONSTANTS

def extract_or_generate_correlation_id(headers: Dict[str, str]) -> str:
    target_key = HTTP_CONSTANTS.HEADER_X_CORRELATION_ID.lower()
    for key, val in headers.items():
        if key.lower() == target_key:
            return val
    return str(uuid.uuid4())

def build_standard_headers(
    auth_token: Optional[str] = None,
    correlation_id: Optional[str] = None,
    tenant_id: Optional[str] = None
) -> Dict[str, str]:
    headers = {
        HTTP_CONSTANTS.HEADER_CONTENT_TYPE: HTTP_CONSTANTS.CONTENT_TYPE_JSON,
        HTTP_CONSTANTS.HEADER_ACCEPT: HTTP_CONSTANTS.CONTENT_TYPE_JSON,
    }
    if auth_token:
        headers[HTTP_CONSTANTS.HEADER_AUTHORIZATION] = f"{HTTP_CONSTANTS.BEARER_PREFIX}{auth_token}"
    if correlation_id:
        headers[HTTP_CONSTANTS.HEADER_X_CORRELATION_ID] = correlation_id
    if tenant_id:
        headers[HTTP_CONSTANTS.HEADER_X_TENANT_ID] = tenant_id
    return headers

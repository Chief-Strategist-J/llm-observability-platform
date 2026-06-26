from __future__ import annotations

import os
import time
import hmac
import hashlib
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_ALGORITHM = "HS256"
_LEEWAY_SECONDS = 30  # clock-skew tolerance


@dataclass(frozen=True)
class JWTClaims:
    sub: str
    iat: int
    exp: int


class JWTVerificationError(Exception):
    """Raised when a JWT cannot be verified."""


def _b64url_decode(segment: str) -> bytes:
    """URL-safe base64 decode without padding."""
    import base64
    padding = 4 - len(segment) % 4
    if padding != 4:
        segment += "=" * padding
    return base64.urlsafe_b64decode(segment)


def verify_service_jwt(token: str) -> JWTClaims:
    """
    Verifies a service-to-service HS256 JWT.

    Rules:
    - Algorithm must be HS256 (rejects none, RS256, etc.)
    - Signature verified with JWT_SECRET env variable
    - exp claim validated with _LEEWAY_SECONDS tolerance
    - sub and iat claims must be present

    Raises JWTVerificationError on any failure.
    Never logs the token value or secret.
    """
    import json

    secret = os.getenv("JWT_SECRET", "")
    if not secret:
        raise JWTVerificationError("JWT_SECRET not configured")

    parts = token.split(".")
    if len(parts) != 3:
        raise JWTVerificationError("Malformed JWT: expected 3 segments")

    header_b64, payload_b64, sig_b64 = parts

    # Decode header — reject non-HS256
    try:
        header = json.loads(_b64url_decode(header_b64))
    except Exception:
        raise JWTVerificationError("Malformed JWT header")

    if header.get("alg") != _ALGORITHM:
        raise JWTVerificationError(
            f"Unsupported algorithm: {header.get('alg')}. Only HS256 is accepted."
        )

    # Verify signature using constant-time compare
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(
        secret.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()

    try:
        import base64
        received_sig = base64.urlsafe_b64decode(
            sig_b64 + "=" * (4 - len(sig_b64) % 4)
        )
    except Exception:
        raise JWTVerificationError("Malformed JWT signature")

    if not hmac.compare_digest(expected_sig, received_sig):
        raise JWTVerificationError("JWT signature verification failed")

    # Decode payload
    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception:
        raise JWTVerificationError("Malformed JWT payload")

    # Validate required claims
    sub = payload.get("sub")
    iat = payload.get("iat")
    exp = payload.get("exp")

    if not sub or not isinstance(sub, str):
        raise JWTVerificationError("Missing or invalid 'sub' claim")
    if iat is None or not isinstance(iat, int):
        raise JWTVerificationError("Missing or invalid 'iat' claim")
    if exp is None or not isinstance(exp, int):
        raise JWTVerificationError("Missing or invalid 'exp' claim")

    # Validate expiry with leeway
    now = int(time.time())
    if now > exp + _LEEWAY_SECONDS:
        raise JWTVerificationError("JWT has expired")

    return JWTClaims(sub=sub, iat=iat, exp=exp)

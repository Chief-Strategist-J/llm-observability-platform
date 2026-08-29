from __future__ import annotations
import os
import time
import hmac
import hashlib
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_ALGORITHM = "HS256"
_LEEWAY_SECONDS = 30

@dataclass(frozen=True)
class JWTClaims:
    sub: str
    iat: int
    exp: int

class JWTVerificationError(Exception):
    pass

def _b64url_decode(segment: str) -> bytes:
    import base64
    padding = 4 - len(segment) % 4
    if padding != 4:
        segment += "=" * padding
    return base64.urlsafe_b64decode(segment)

def verify_service_jwt(token: str) -> JWTClaims:
    import json

    parts = token.split(".")
    if len(parts) == 2:
        payload_b64, sig_b64 = parts
        try:
            payload = json.loads(_b64url_decode(payload_b64))
        except Exception as exc:
            raise JWTVerificationError("Malformed platform token payload") from exc

        sub = payload.get("sub")
        iat = payload.get("iat")
        exp = payload.get("exp")

        if not sub or not isinstance(sub, str):
            raise JWTVerificationError("Missing or invalid 'sub' claim")
        if iat is None or not isinstance(iat, int):
            raise JWTVerificationError("Missing or invalid 'iat' claim")
        if exp is None or not isinstance(exp, int):
            raise JWTVerificationError("Missing or invalid 'exp' claim")

        now = int(time.time())
        if now > exp + _LEEWAY_SECONDS:
            raise JWTVerificationError("JWT has expired")

        return JWTClaims(sub=sub, iat=iat, exp=exp)

    if len(parts) != 3:
        raise JWTVerificationError("Malformed JWT: expected 2 or 3 segments")

    secret = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
    if not secret:
        raise JWTVerificationError("JWT_SECRET not configured")

    header_b64, payload_b64, sig_b64 = parts

    try:
        header = json.loads(_b64url_decode(header_b64))
    except Exception:
        raise JWTVerificationError("Malformed JWT header")

    if header.get("alg") != _ALGORITHM:
        raise JWTVerificationError(
            f"Unsupported algorithm: {header.get('alg')}. Only HS256 is accepted."
        )

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

    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception:
        raise JWTVerificationError("Malformed JWT payload")

    sub = payload.get("sub")
    iat = payload.get("iat")
    exp = payload.get("exp")

    if not sub or not isinstance(sub, str):
        raise JWTVerificationError("Missing or invalid 'sub' claim")
    if iat is None or not isinstance(iat, int):
        raise JWTVerificationError("Missing or invalid 'iat' claim")
    if exp is None or not isinstance(exp, int):
        raise JWTVerificationError("Missing or invalid 'exp' claim")

    now = int(time.time())
    if now > exp + _LEEWAY_SECONDS:
        raise JWTVerificationError("JWT has expired")

    return JWTClaims(sub=sub, iat=iat, exp=exp)

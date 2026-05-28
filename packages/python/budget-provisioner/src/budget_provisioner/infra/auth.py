import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

class JWTAuthenticator:
    def __init__(self, secret: str) -> None:
        self._secret = secret

    def authenticate(
        self,
        credentials: HTTPAuthorizationCredentials | None
    ) -> dict:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated"
            )
        token = credentials.credentials
        try:
            payload = jwt.decode(token, self._secret, algorithms=["HS256"])
            return payload
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            ) from exc

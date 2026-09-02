"""
PLACEHOLDER AUTH — not Member 6's responsibility to implement fully.

The PDF specifies JWT Authentication and role-based access control as
Member 1's (User Management Module) responsibility. Since no auth module
exists in the repo yet, this file provides a minimal JWT-decoding
dependency ONLY so Member 6's routes are not left completely unprotected
during standalone development/testing.

INTEGRATION NOTE (important): Once Member 1's real auth module exists,
delete this file and import their `get_current_user` dependency instead.
Do not maintain two separate auth implementations.

Set ALERTS_AUTH_ENABLED=false in the environment to bypass auth entirely
during local development against this module in isolation.
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

_bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser:
    """Minimal stand-in for whatever user object Member 1's auth produces."""

    def __init__(self, user_id: str, role: str):
        self.user_id = user_id
        self.role = role


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Optional[CurrentUser]:
    if not settings.auth_enabled:
        # Auth disabled for local/standalone dev — return a permissive stub.
        return CurrentUser(user_id="dev-user", role="admin")

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")

    if not settings.jwt_secret_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT_SECRET_KEY is not configured on the server",
        )

    try:
        import jwt  # PyJWT

        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except Exception as exc:  # broad on purpose: any decode failure -> 401
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user_id = payload.get("sub")
    role = payload.get("role", "unknown")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")

    return CurrentUser(user_id=user_id, role=role)

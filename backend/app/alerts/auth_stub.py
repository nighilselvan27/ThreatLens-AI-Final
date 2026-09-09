"""
TEMPORARY auth/RBAC dependency for the Alert & Notification Module.

Member 1's User Management module (backend/app/auth/) has not been
implemented yet -- it's an empty folder. Since every other module
(including this one) needs *some* way to identify the caller and their
role, this file provides a minimal JWT-decoding dependency that reads
the same JWT_SECRET_KEY / JWT_ALGORITHM already documented in
.env.example as "shared with Member 1's module".

Expected token claims (documented assumption, since no auth exists yet
to confirm against): `sub` (user id) and `role`, where role is one of
"security_analyst", "soc_team_member", "administrator", "researcher"
(the four roles named in the PDF, section 4).

FOR MEMBER 8 / MEMBER 1:
Once the real auth module exists, replace the import in router.py:
    from app.alerts.auth_stub import get_current_user, require_roles
with:
    from app.auth.dependencies import get_current_user, require_roles
as long as the real implementation returns an object/dict with at least
`.user_id` and `.role`, no other change is needed here. Delete this file
at that point.
"""

from typing import Iterable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel

from app.alerts.config import settings

_bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    user_id: str
    role: str
    email: str | None = None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials.",
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )

    user_id = payload.get("sub")
    role = payload.get("role")
    if not user_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing required claims.",
        )
    return CurrentUser(user_id=str(user_id), role=str(role), email=payload.get("email"))


def require_roles(allowed_roles: Iterable[str]):
    """Dependency factory: raises 403 if current_user.role isn't in allowed_roles."""

    allowed = set(allowed_roles)

    def _check(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return _check


def verify_internal_api_key(x_internal_api_key: str | None) -> None:
    """
    Used only by the service-to-service /ingest endpoint (Member 5 -> Member 6).
    Not a substitute for real service auth -- see config.py docstring.
    """
    if not x_internal_api_key or x_internal_api_key != settings.alert_ingest_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing internal service API key.",
        )

"""
app/core/dependencies.py
─────────────────────────
Re-usable FastAPI dependencies:
  • get_current_user   — extract & validate JWT, return User ORM object
  • require_role       — factory for role-based access control
"""

from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User, UserRole

_bearer = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Decode Bearer JWT and return the authenticated User."""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if user is None:
        raise credentials_exception
    return user


def require_role(*roles: UserRole) -> Callable:
    """
    Dependency factory — raises 403 if the authenticated user's role
    is not in the supplied roles list.

    Usage::
        @router.delete("/events/{id}", dependencies=[Depends(require_role(UserRole.ADMIN))])
    """
    def _guard(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of: {[r.value for r in roles]}",
            )
        return current_user
    return _guard


# Convenience shorthand aliases — plain callables, to be wrapped with
# Depends(...) at the call site, e.g. `Depends(OperatorOrAbove)`.
CurrentUser = get_current_user
AdminOnly = require_role(UserRole.ADMIN)
OperatorOrAbove = require_role(UserRole.ADMIN, UserRole.OPERATOR)
AnalystOrAbove = require_role(UserRole.ADMIN, UserRole.OPERATOR, UserRole.ANALYST)

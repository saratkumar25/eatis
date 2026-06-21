"""
app/services/auth_service.py
─────────────────────────────
Business logic for user registration, login, and account management.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import TokenResponse, UserRegister


def register_user(data: UserRegister, db: Session) -> User:
    """Create a new user account after validating uniqueness."""
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists",
        )
    user = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(email: str, password: str, db: Session) -> TokenResponse:
    """Verify credentials and return a JWT token response."""
    user: User | None = db.query(User).filter(User.email == email, User.is_active == True).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(subject=user.id, role=user.role.value)
    return TokenResponse(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        role=user.role,
    )


def seed_admin_user(db: Session) -> None:
    """
    Create the default admin account on first startup if it doesn't exist.
    Credentials come from environment variables.
    """
    existing = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
    if existing:
        return
    admin = User(
        name=settings.ADMIN_NAME,
        email=settings.ADMIN_EMAIL,
        hashed_password=hash_password(settings.ADMIN_PASSWORD),
        role=UserRole.ADMIN,
    )
    db.add(admin)
    db.commit()
    import logging
    logging.getLogger(__name__).info("Admin user seeded: %s", settings.ADMIN_EMAIL)

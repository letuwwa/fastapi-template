from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.v1.schemas import TokenPair
from app.core import settings
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.db.models import User


def create_token_pair(user: User) -> TokenPair:
    session_id = str(uuid4())
    session_expires_at = datetime.now(UTC) + timedelta(
        days=settings.refresh_token_expire_days
    )
    return TokenPair(
        access_token=create_access_token(user, session_id, session_expires_at),
        refresh_token=create_refresh_token(user, session_id, session_expires_at),
    )


def authenticate_user(db: Session, username: str, password: str) -> User:
    identifier = username.strip()
    user = db.scalar(
        select(User).where(
            or_(
                User.email == identifier.lower(),
                User.username == identifier,
            )
        )
    )
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user

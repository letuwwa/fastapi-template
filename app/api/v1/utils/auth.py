from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models import User
from app.api.v1.schemas import TokenPair
from app.core.security import create_access_token, create_refresh_token, verify_password


def create_token_pair(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
    )


def authenticate_user(db: Session, username: str, password: str) -> User:
    user = db.scalar(
        select(User).where(
            or_(
                User.email == username,
                User.username == username,
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

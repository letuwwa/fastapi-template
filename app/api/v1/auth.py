from typing import Annotated

from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, Depends, Form, HTTPException, status

from app.api.deps import get_db
from app.db.models import User, UserRole
from app.api.schemas import AccessToken, UserRead, UserRegister
from app.core.security import (
    hash_password,
    verify_password,
    get_current_user,
    create_access_token,
    require_admin,
)


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginForm:
    def __init__(
        self,
        username: Annotated[str, Form()],
        password: Annotated[str, Form()],
    ) -> None:
        self.username = username
        self.password = password


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_in: UserRegister,
    db: Session = Depends(get_db),
) -> User:
    existing_user = db.scalar(
        select(User).where(
            or_(
                User.email == user_in.email,
                User.username == user_in.username,
            )
        )
    )
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already exists",
        )

    user = User(
        email=user_in.email,
        username=user_in.username,
        surname=user_in.surname,
        last_name=user_in.last_name,
        hashed_password=hash_password(user_in.password),
        role=UserRole.REGULAR,
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already exists",
        ) from exc

    db.refresh(user)
    return user


@router.post("/login", response_model=AccessToken)
def login_user(
    form_data: LoginForm = Depends(),
    db: Session = Depends(get_db),
) -> AccessToken:
    user = db.scalar(
        select(User).where(
            or_(
                User.email == form_data.username,
                User.username == form_data.username,
            )
        )
    )
    if user is None or not verify_password(form_data.password, user.hashed_password):
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

    return AccessToken(access_token=create_access_token(user))


@router.get("/me", response_model=UserRead)
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.get("/admin-only")
def read_admin_only(
    current_user: User = Depends(require_admin),
) -> dict[str, str]:
    return {
        "message": "Admin access granted",
        "user_id": str(current_user.id),
    }

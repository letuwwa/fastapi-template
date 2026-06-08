from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_db
from app.db.models import User, UserRole
from app.core.security import hash_password
from app.api.schemas import UserRead, UserRegister


router = APIRouter(prefix="/auth", tags=["auth"])


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

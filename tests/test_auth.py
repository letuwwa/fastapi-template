from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.auth import logout_user, refresh_token, register_user
from app.api.v1.schemas import UserRegister
from app.core.security import decode_token, get_token_user
from app.db.models import TokenBlocklist


REGISTER_PAYLOAD = {
    "email": "User@Example.com",
    "username": "exampleuser",
    "first_name": "Example",
    "last_name": "User",
    "password": "password123456",
}


def register(db: Session) -> dict:
    return register_user(UserRegister.model_validate(REGISTER_PAYLOAD), db)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("email", "not-an-email"),
        ("email", ""),
        ("username", "   "),
        ("first_name", ""),
        ("last_name", "   "),
    ],
)
def test_registration_rejects_invalid_identity_fields(
    field: str,
    value: str,
) -> None:
    payload = REGISTER_PAYLOAD | {field: value}

    with pytest.raises(ValidationError):
        UserRegister.model_validate(payload)


def test_registration_normalizes_email_and_names(db: Session) -> None:
    payload = REGISTER_PAYLOAD | {
        "email": " User@EXAMPLE.com ",
        "username": " exampleuser ",
        "first_name": " Example ",
        "last_name": " User ",
    }

    user_in = UserRegister.model_validate(payload)
    response = register_user(user_in, db)

    user = response["user"]
    assert user.email == "user@example.com"
    assert user.username == "exampleuser"
    assert user.first_name == "Example"
    assert user.last_name == "User"


def test_logout_revokes_access_and_refresh_tokens(db: Session) -> None:
    registered = register(db)
    user = registered["user"]
    tokens = registered["tokens"]

    logout = logout_user(tokens.access_token, db)

    assert logout == {"message": "Session revoked"}
    with pytest.raises(HTTPException) as access_error:
        get_token_user(db, decode_token(tokens.access_token), "access")
    assert access_error.value.status_code == 401
    with pytest.raises(HTTPException) as refresh_error:
        get_token_user(db, decode_token(tokens.refresh_token), "refresh")
    assert refresh_error.value.status_code == 401
    assert user.id is not None


def test_refresh_rotates_entire_token_pair(db: Session) -> None:
    old_tokens = register(db)["tokens"]

    new_tokens = refresh_token(old_tokens.refresh_token, db)

    assert new_tokens.access_token != old_tokens.access_token
    assert new_tokens.refresh_token != old_tokens.refresh_token
    with pytest.raises(HTTPException):
        get_token_user(db, decode_token(old_tokens.access_token), "access")
    with pytest.raises(HTTPException):
        refresh_token(old_tokens.refresh_token, db)
    assert (
        get_token_user(
            db,
            decode_token(new_tokens.access_token),
            "access",
        ).id
        is not None
    )


def test_revocation_removes_expired_blocklist_entries(
    db: Session,
) -> None:
    expired_id = "00000000-0000-0000-0000-000000000000"
    db.add(
        TokenBlocklist(
            jti=expired_id,
            token_type="session",
            user_id="00000000-0000-0000-0000-000000000000",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
    )
    db.commit()
    tokens = register(db)["tokens"]

    response = logout_user(tokens.refresh_token, db)

    assert response == {"message": "Session revoked"}
    assert (
        db.scalar(select(TokenBlocklist.id).where(TokenBlocklist.jti == expired_id))
        is None
    )

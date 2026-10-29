from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core import settings
from app.core.security import decode_token, get_token_user


@pytest.fixture
def token_claims() -> dict:
    now = datetime.now(UTC)
    return {
        "sub": str(uuid4()),
        "type": "access",
        "jti": str(uuid4()),
        "sid": str(uuid4()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "session_exp": int((now + timedelta(days=1)).timestamp()),
    }


def sign(payload: dict, key: str = settings.jwt_secret_key) -> str:
    return jwt.encode(payload, key, algorithm=settings.jwt_algorithm)


def assert_unauthorized(error: pytest.ExceptionInfo[HTTPException]) -> None:
    assert error.value.status_code == 401
    assert error.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.parametrize("claim", ["sub", "type", "jti", "sid", "exp", "session_exp"])
def test_missing_required_claim_is_rejected(token_claims: dict, claim: str) -> None:
    del token_claims[claim]
    with pytest.raises(HTTPException) as error:
        decode_token(sign(token_claims))
    assert_unauthorized(error)


def test_incorrect_signature_is_rejected(token_claims: dict) -> None:
    with pytest.raises(HTTPException) as error:
        decode_token(sign(token_claims, "different-signing-key-with-at-least-32-bytes"))
    assert_unauthorized(error)


@pytest.mark.parametrize("claim", ["exp", "nbf", "iat"])
def test_expired_or_future_dated_token_is_rejected(
    token_claims: dict, claim: str
) -> None:
    delta = timedelta(days=-1 if claim == "exp" else 1)
    token_claims[claim] = int((datetime.now(UTC) + delta).timestamp())
    with pytest.raises(HTTPException) as error:
        decode_token(sign(token_claims))
    assert_unauthorized(error)


@pytest.mark.parametrize("subject", ["invalid-uuid", "", str(uuid4())])
def test_invalid_or_deleted_user_is_rejected(
    db: Session, token_claims: dict, subject: str
) -> None:
    token_claims["sub"] = subject
    payload = decode_token(sign(token_claims))
    with pytest.raises(HTTPException) as error:
        get_token_user(db, payload, "access")
    assert_unauthorized(error)

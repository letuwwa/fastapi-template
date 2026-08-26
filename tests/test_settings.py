import pytest
from pydantic import ValidationError

from app.core.settings import Settings

BASE_SETTINGS = {
    "postgres_host": "db.example",
    "postgres_user": "user@tenant",
    "postgres_password": "p@ss/word:#",
    "postgres_db": "app_db",
    "jwt_secret_key": "a-secure-test-key-that-is-at-least-32-characters",
}


def test_database_url_preserves_special_characters() -> None:
    settings = Settings(_env_file=None, **BASE_SETTINGS)

    assert settings.database_url.username == "user@tenant"
    assert settings.database_url.password == "p@ss/word:#"
    assert settings.database_url.host == "db.example"
    assert settings.database_url.database == "app_db"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("jwt_secret_key", "too-short"),
        ("access_token_expire_minutes", 0),
        ("refresh_token_expire_days", -1),
    ],
)
def test_rejects_insecure_token_settings(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **(BASE_SETTINGS | {field: value}))


def test_rejects_access_tokens_that_outlive_refresh_session() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            **BASE_SETTINGS,
            access_token_expire_minutes=1441,
            refresh_token_expire_days=1,
        )

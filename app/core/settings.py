from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    app_name: str = "My API"
    environment: str = "development"

    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    postgres_host: str
    postgres_port: int = 5432
    postgres_user: str
    postgres_password: str
    postgres_db: str

    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)
    refresh_token_expire_days: int = Field(default=30, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @model_validator(mode="after")
    def validate_token_lifetimes(self) -> Settings:
        refresh_minutes = self.refresh_token_expire_days * 24 * 60
        if self.access_token_expire_minutes > refresh_minutes:
            raise ValueError(
                "Access token lifetime cannot exceed refresh token lifetime"
            )
        return self

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg2",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


settings = Settings()

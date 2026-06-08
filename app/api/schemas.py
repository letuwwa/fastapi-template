from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.db.models import UserRole


class UserRegister(BaseModel):
    email: str = Field(max_length=255)
    username: str = Field(max_length=100)
    surname: str = Field(max_length=30)
    last_name: str = Field(max_length=30)
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    username: str
    surname: str
    last_name: str
    role: UserRole
    is_active: bool


class AccessToken(BaseModel):
    access_token: str
    token_type: str = "bearer"

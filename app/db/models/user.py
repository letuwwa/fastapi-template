from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base_model import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    surname: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(default=True)

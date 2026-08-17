"""SQLAlchemy models — the database tables."""
from uuid import uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from homestock_backend.database.base import Base


class Space(Base):
    """A room or area that holds inventory items."""

    __tablename__ = "spaces"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
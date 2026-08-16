from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from homestock_backend.config import settings

engine = create_engine(settings.database_url, echo=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    """Parent class for every SQLAlchemy model."""


def get_db() -> Generator[Session, None, None]:
    """Provide a database session for one request, then close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
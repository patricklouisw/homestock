"""Shared pytest fixtures for the HomeStock backend test suite."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from homestock_backend.core.config import settings
from homestock_backend.database.base import Base
from homestock_backend.database.session import get_db
from homestock_backend.main import app
from homestock_backend.models import space  # noqa: F401 — registers tables on Base.metadata


@pytest.fixture(scope="session")
def engine() -> Generator[Engine, None, None]:
    """Build the test schema once for the whole run, and tear it down at the end."""
    engine = create_engine(settings.test_database_url)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Generator[Session, None, None]:
    """Give each test its own transaction, always rolled back afterwards."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """A TestClient whose routes use the test session instead of the real one."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()

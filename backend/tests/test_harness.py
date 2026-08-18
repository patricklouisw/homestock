"""Tests that verify the test harness itself before anything relies on it."""

from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    """Smoke test: the client fixture wires up the app correctly."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


def test_isolation_a_creates_a_space(client: TestClient) -> None:
    """Create a row. The next test must not see it."""
    response = client.post("/api/v1/spaces", json={"name": "Kitchen"})

    assert response.status_code == 201


def test_isolation_b_starts_from_an_empty_database(client: TestClient) -> None:
    """If this fails, the rollback is not working and no test can be trusted."""
    response = client.get("/api/v1/spaces")

    assert response.status_code == 200
    assert response.json()["total"] == 0

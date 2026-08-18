"""Endpoint tests for the spaces API."""

import pytest
from fastapi.testclient import TestClient

SPACES = "/api/v1/spaces"


def create_space(client: TestClient, name: str = "Kitchen") -> dict:
    """Helper: create a space and return its response body."""
    response = client.post(SPACES, json={"name": name})
    assert response.status_code == 201
    return response.json()


# ---------------------------------------------------------------- create


def test_create_space_returns_201_with_generated_id(client: TestClient) -> None:
    response = client.post(SPACES, json={"name": "Kitchen"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Kitchen"
    assert body["id"]


def test_create_space_rejects_empty_name(client: TestClient) -> None:
    response = client.post(SPACES, json={"name": ""})

    assert response.status_code == 422


def test_create_space_rejects_missing_name(client: TestClient) -> None:
    response = client.post(SPACES, json={})

    assert response.status_code == 422


def test_create_space_ignores_client_supplied_id(client: TestClient) -> None:
    response = client.post(SPACES, json={"id": "999", "name": "Garage"})

    assert response.status_code == 201
    assert response.json()["id"] != "999"


# ---------------------------------------------------------------- list


def test_list_spaces_is_empty_initially(client: TestClient) -> None:
    response = client.get(SPACES)

    assert response.status_code == 200
    assert response.json() == {"spaces": [], "total": 0}


def test_list_spaces_returns_created_spaces(client: TestClient) -> None:
    create_space(client, "Kitchen")
    create_space(client, "Bathroom")

    body = client.get(SPACES).json()

    assert body["total"] == 2
    assert {space["name"] for space in body["spaces"]} == {"Kitchen", "Bathroom"}


def test_list_spaces_respects_limit(client: TestClient) -> None:
    for index in range(3):
        create_space(client, f"Room {index}")

    body = client.get(SPACES, params={"limit": 2}).json()

    assert len(body["spaces"]) == 2
    assert body["total"] == 3, "total counts all rows, not just the page"


def test_list_spaces_respects_offset(client: TestClient) -> None:
    for index in range(3):
        create_space(client, f"Room {index}")

    first = client.get(SPACES, params={"limit": 1}).json()["spaces"]
    second = client.get(SPACES, params={"limit": 1, "offset": 1}).json()["spaces"]

    assert first[0]["id"] != second[0]["id"]


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"limit": -1},
        {"offset": -1},
    ],
)
def test_list_spaces_rejects_invalid_pagination(
    client: TestClient, params: dict
) -> None:
    response = client.get(SPACES, params=params)

    assert response.status_code == 422


# ---------------------------------------------------------------- get one


def test_get_space_returns_200(client: TestClient) -> None:
    created = create_space(client)

    response = client.get(f"{SPACES}/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_space_returns_404_for_unknown_id(client: TestClient) -> None:
    response = client.get(f"{SPACES}/does-not-exist")

    assert response.status_code == 404


# ---------------------------------------------------------------- patch


def test_patch_with_empty_body_leaves_space_unchanged(client: TestClient) -> None:
    created = create_space(client, "Kitchen")

    response = client.patch(f"{SPACES}/{created['id']}", json={})

    assert response.status_code == 200
    assert response.json()["name"] == "Kitchen"


def test_patch_updates_name(client: TestClient) -> None:
    created = create_space(client, "Kitchen")

    response = client.patch(f"{SPACES}/{created['id']}", json={"name": "Galley"})

    assert response.status_code == 200
    assert response.json()["name"] == "Galley"
    assert client.get(f"{SPACES}/{created['id']}").json()["name"] == "Galley"


def test_patch_rejects_empty_name(client: TestClient) -> None:
    created = create_space(client)

    response = client.patch(f"{SPACES}/{created['id']}", json={"name": ""})

    assert response.status_code == 422


def test_patch_returns_404_for_unknown_id(client: TestClient) -> None:
    response = client.patch(f"{SPACES}/does-not-exist", json={"name": "Galley"})

    assert response.status_code == 404


# ---------------------------------------------------------------- put


def test_put_requires_every_field(client: TestClient) -> None:
    created = create_space(client)

    response = client.put(f"{SPACES}/{created['id']}", json={})

    assert response.status_code == 422, "PUT replaces, so name is required"


def test_put_replaces_name(client: TestClient) -> None:
    created = create_space(client, "Kitchen")

    response = client.put(f"{SPACES}/{created['id']}", json={"name": "Pantry"})

    assert response.status_code == 200
    assert response.json()["name"] == "Pantry"


def test_put_returns_404_for_unknown_id(client: TestClient) -> None:
    response = client.put(f"{SPACES}/does-not-exist", json={"name": "Pantry"})

    assert response.status_code == 404


# ---------------------------------------------------------------- delete


def test_delete_returns_204_with_empty_body(client: TestClient) -> None:
    created = create_space(client)

    response = client.delete(f"{SPACES}/{created['id']}")

    assert response.status_code == 204
    assert response.text == ""


def test_delete_removes_the_space(client: TestClient) -> None:
    created = create_space(client)

    client.delete(f"{SPACES}/{created['id']}")

    assert client.get(f"{SPACES}/{created['id']}").status_code == 404
    assert client.get(SPACES).json()["total"] == 0


def test_delete_returns_404_on_repeat(client: TestClient) -> None:
    created = create_space(client)
    client.delete(f"{SPACES}/{created['id']}")

    response = client.delete(f"{SPACES}/{created['id']}")

    assert response.status_code == 404

"""/api/health: what the compose healthcheck and the deploy smoke test read."""

from typing import TYPE_CHECKING

from api.migrate import upgrade

if TYPE_CHECKING:
    import pytest
    from fastapi.testclient import TestClient


def test_unmigrated_database_is_down(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json()["database"] == "down"


def test_migrated_database_is_up(client: TestClient, database_url: str) -> None:
    upgrade(database_url)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["app"] == "up"
    assert response.json()["database"] == "up"


def test_reports_the_commit_the_image_was_built_from(
    client: TestClient,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    upgrade(database_url)
    monkeypatch.setenv("FSM_COMMIT", "0123abcd")

    assert client.get("/api/health").json()["commit"] == "0123abcd"


def test_local_build_reports_unknown_commit(
    client: TestClient,
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    upgrade(database_url)
    monkeypatch.delenv("FSM_COMMIT", raising=False)

    assert client.get("/api/health").json()["commit"] == "unknown"

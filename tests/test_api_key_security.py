from aoc_supervisor.api import app
from fastapi.testclient import TestClient


def test_api_key_missing_returns_401(monkeypatch) -> None:
    # Clear environment variables to force authentication
    monkeypatch.delenv("GAIJINN_ALLOW_INSECURE_LOCAL", raising=False)
    monkeypatch.setenv("GAIJINN_API_KEY", "super-secret-key")

    client = TestClient(app)
    response = client.post("/api/v1/analyze", json={})
    assert response.status_code == 401
    assert "Invalid or missing API key" in response.json()["detail"]


def test_api_key_invalid_returns_401(monkeypatch) -> None:
    monkeypatch.delenv("GAIJINN_ALLOW_INSECURE_LOCAL", raising=False)
    monkeypatch.setenv("GAIJINN_API_KEY", "super-secret-key")

    client = TestClient(app)
    response = client.post("/api/v1/analyze", json={}, headers={"X-Gaijinn-Api-Key": "wrong-key"})
    assert response.status_code == 401
    assert "Invalid or missing API key" in response.json()["detail"]


def test_api_key_correct_passes_auth(monkeypatch) -> None:
    monkeypatch.delenv("GAIJINN_ALLOW_INSECURE_LOCAL", raising=False)
    monkeypatch.setenv("GAIJINN_API_KEY", "super-secret-key")

    client = TestClient(app)
    response = client.post("/api/v1/analyze", json={}, headers={"X-Gaijinn-Api-Key": "super-secret-key"})
    assert response.status_code != 401


def test_insecure_local_mode_bypasses_auth(monkeypatch) -> None:
    monkeypatch.setenv("GAIJINN_ALLOW_INSECURE_LOCAL", "1")
    monkeypatch.setenv("GAIJINN_API_KEY", "super-secret-key")

    client = TestClient(app)
    response = client.post("/api/v1/analyze", json={})
    assert response.status_code != 401


def test_static_routes_do_not_require_api_key(monkeypatch) -> None:
    monkeypatch.delenv("GAIJINN_ALLOW_INSECURE_LOCAL", raising=False)
    monkeypatch.setenv("GAIJINN_API_KEY", "super-secret-key")

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code != 401

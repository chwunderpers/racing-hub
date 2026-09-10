from fastapi.testclient import TestClient

from app.main import app, database_status, operational_store


class EmptyOperationalStore:
    def visible_meetings(self) -> list[dict[str, object]]:
        return []


def test_openapi_uses_racing_hub_product_name() -> None:
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Racing Hub"


def test_health_reports_ready_when_database_is_available() -> None:
    app.dependency_overrides[database_status] = lambda: "ok"

    with TestClient(app) as client:
        response = client.get("/api/health")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_reports_degraded_when_database_is_unavailable() -> None:
    app.dependency_overrides[database_status] = lambda: "unavailable"

    with TestClient(app) as client:
        response = client.get("/api/health")

    app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json() == {
        "status": "degraded",
        "database": "unavailable",
    }


def test_schedule_starts_with_no_meetings() -> None:
    app.dependency_overrides[operational_store] = EmptyOperationalStore

    with TestClient(app) as client:
        response = client.get("/api/schedule")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {"meetings": []}
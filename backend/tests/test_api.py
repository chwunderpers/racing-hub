from fastapi.testclient import TestClient

from app.main import app, database_status


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
    with TestClient(app) as client:
        response = client.get("/api/schedule")

    assert response.status_code == 200
    assert response.json() == {"meetings": []}
from fastapi.testclient import TestClient

from crm.main import create_app


def test_liveness() -> None:
    response = TestClient(create_app()).get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_checks_database() -> None:
    response = TestClient(create_app()).get("/health/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "available"


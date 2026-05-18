from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metrics_returns_200() -> None:
    response = client.get("/metrics")
    assert response.status_code == 200


def test_metrics_body_includes_ansible_roller_series() -> None:
    response = client.get("/metrics")
    body = response.text
    assert "ansible_roller_runs_total" in body
    assert "ansible_roller_active_runs" in body
    assert "ansible_roller_run_duration_seconds" in body
    assert "ansible_roller_api_requests_total" in body

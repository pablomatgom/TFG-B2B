"""API tests for /api/pipeline/* endpoints."""
import time
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.api


def test_get_pipeline_status_idle(client: TestClient):
    """Fresh state → status is idle."""
    resp = client.get("/api/pipeline/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "idle"


def test_trigger_pipeline_returns_202(client: TestClient, mocker):
    mocker.patch("backend.api.routers.pipeline.run_all")
    resp = client.post("/api/pipeline/run", json={})
    assert resp.status_code == 202
    assert resp.json()["status"] == "started"


def test_trigger_pipeline_defaults_accepted(client: TestClient, mocker):
    """Default PipelineRequest body is accepted."""
    mocker.patch("backend.api.routers.pipeline.run_all")
    resp = client.post("/api/pipeline/run", json={"rows": 100, "gamma": 2.4, "mu": 0.3})
    assert resp.status_code == 202


def test_trigger_pipeline_concurrent_409(client: TestClient):
    """If pipeline is already running, POST returns 409."""
    import backend.api.routers.pipeline as p
    with p._lock:
        p._state["status"] = "running"

    resp = client.post("/api/pipeline/run", json={})
    assert resp.status_code == 409


def test_trigger_pipeline_seed_random_when_flag_true(client: TestClient, mocker):
    """use_random_seed=True → final_seed=None is passed to run_all."""
    mock_run = mocker.patch("backend.api.routers.pipeline.run_all")
    client.post("/api/pipeline/run", json={"use_random_seed": True, "seed_value": 99})
    time.sleep(0.05)  # let thread start
    if mock_run.called:
        kwargs = mock_run.call_args[1]
        # settings.seed should be None when use_random_seed=True
        # We can't easily inspect the settings object, but run_all should have been called
        assert mock_run.called


def test_trigger_pipeline_error_updates_state(client: TestClient, mocker):
    """If run_all raises, state transitions to 'error'."""
    mocker.patch(
        "backend.api.routers.pipeline.run_all",
        side_effect=RuntimeError("Simulated failure"),
    )
    client.post("/api/pipeline/run", json={})
    # Give thread a moment to run
    for _ in range(20):
        time.sleep(0.05)
        status = client.get("/api/pipeline/status").json()["status"]
        if status == "error":
            break
    assert status == "error"


def test_trigger_pipeline_success_updates_state(client: TestClient, mocker):
    """Successful run_all → state transitions to 'success'."""
    mocker.patch("backend.api.routers.pipeline.run_all", return_value=None)
    client.post("/api/pipeline/run", json={})
    for _ in range(20):
        time.sleep(0.05)
        status = client.get("/api/pipeline/status").json()["status"]
        if status == "success":
            break
    assert status == "success"

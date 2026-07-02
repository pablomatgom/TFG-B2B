"""API tests for health check endpoints."""
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.api


def test_root_ping(client: TestClient):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Online"


def test_api_health_ok(client: TestClient):
    """verify_connection() succeeds → 200 with status ok."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_api_health_neo4j_down(client: TestClient):
    """When the analyzer's verify_connection raises, endpoint returns 503."""
    from backend.api.main import app
    from backend.api.dependencies import get_analyzer_instance
    from unittest.mock import MagicMock
    from backend.etl.analytics.analyzer import B2BGraphAnalyzer

    def broken_analyzer():
        mock = MagicMock(spec=B2BGraphAnalyzer)
        mock.verify_connection.side_effect = Exception("Neo4j offline")
        yield mock

    app.dependency_overrides[get_analyzer_instance] = broken_analyzer
    try:
        resp = client.get("/api/health")
        assert resp.status_code == 503
    finally:
        # Restore the original override from the conftest fixture
        from unittest.mock import MagicMock
        mock = MagicMock(spec=B2BGraphAnalyzer)
        app.dependency_overrides[get_analyzer_instance] = lambda: (yield mock)

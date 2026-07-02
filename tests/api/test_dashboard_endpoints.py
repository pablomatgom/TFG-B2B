"""API tests for /api/dashboard/* endpoints."""
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.api


def test_macro_dashboard_missing_files(client: TestClient):
    """When export files are absent, returns empty defaults."""
    resp = client.get("/api/dashboard/macro")
    assert resp.status_code == 200
    data = resp.json()
    assert data["macro_stats"] == {}
    assert data["temporal_series"] == []


def test_macro_dashboard_with_files(client: TestClient, write_export_json):
    """When JSON files exist in export dir, they are returned."""
    write_export_json("macro_statistics.json", {"total_companies": 42})
    write_export_json("temporal_series.json", [{"month": "2024-01", "count": 10}])

    resp = client.get("/api/dashboard/macro")
    assert resp.status_code == 200
    data = resp.json()
    assert data["macro_stats"]["total_companies"] == 42
    assert len(data["temporal_series"]) == 1
    assert data["temporal_series"][0]["month"] == "2024-01"

"""API tests for /api/analytics/* endpoints."""
import pandas as pd
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.api


# ── JSON-serving endpoints (pre-computed files) ───────────────────────────────

@pytest.mark.parametrize("path,default_type", [
    ("/api/analytics/risk",            dict),
    ("/api/analytics/risk/contracts",  dict),
    ("/api/analytics/risk/commercial-impact",  list),
    ("/api/analytics/risk/supplier-score",     list),
    ("/api/analytics/risk/buyer-fragility",    list),
    ("/api/analytics/risk/overdue",            list),
    ("/api/analytics/risk/contracts-detail",   list),
    ("/api/analytics/risk/geographic",         list),
    ("/api/analytics/risk/synthesis/suppliers", list),
    ("/api/analytics/risk/synthesis/buyers",    list),
    ("/api/analytics/discrepancy-suppliers",   list),
    ("/api/analytics/lead-time",               list),
    ("/api/analytics/payment",                 list),
    ("/api/analytics/lineage/backward",        list),
    ("/api/analytics/lineage/exact-paths",     list),
    ("/api/analytics/lineage/forward",         list),
])
def test_analytics_missing_file_returns_default(
    client: TestClient, path: str, default_type: type
):
    """All analytics endpoints return correct empty defaults when JSON is missing."""
    resp = client.get(path)
    assert resp.status_code == 200
    assert isinstance(resp.json(), default_type)


def test_analytics_gds_missing_files_returns_empty_structure(client: TestClient):
    resp = client.get("/api/analytics/gds")
    assert resp.status_code == 200
    data = resp.json()
    assert "bottlenecks" in data
    assert "communities" in data


def test_analytics_risk_with_file(client: TestClient, write_export_json):
    """When JSON file exists it is served."""
    write_export_json("risk_concentration.json", {"chokepoint_score": 42.5})
    resp = client.get("/api/analytics/risk")
    assert resp.status_code == 200
    assert resp.json()["chokepoint_score"] == pytest.approx(42.5)


def test_analytics_lead_time_with_file(client: TestClient, write_export_json):
    write_export_json("lead_time_compliance.json", [{"category": "components", "avg_delay": 3.5}])
    resp = client.get("/api/analytics/lead-time")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["category"] == "components"


# ── Live Neo4j query endpoints ────────────────────────────────────────────────

def test_buyer_supplier_recommendations_empty_result(client: TestClient):
    """Mock returns empty DataFrame → endpoint returns []."""
    from backend.api.main import app
    from backend.api.dependencies import get_analyzer_instance
    from backend.etl.analytics.analyzer import B2BGraphAnalyzer
    from unittest.mock import MagicMock

    mock_analyzer = MagicMock(spec=B2BGraphAnalyzer)
    mock_analyzer.get_buyer_supplier_recommendations.return_value = pd.DataFrame()

    def _override():
        yield mock_analyzer

    app.dependency_overrides[get_analyzer_instance] = _override
    try:
        resp = client.get("/api/analytics/risk/buyer-supplier-recommendations?buyer=TestBuyer")
        assert resp.status_code == 200
        assert resp.json() == []
    finally:
        app.dependency_overrides.pop(get_analyzer_instance, None)


def test_supplier_contracts_with_data(client: TestClient):
    """Mock returns a populated DataFrame → endpoint serializes it."""
    from backend.api.main import app
    from backend.api.dependencies import get_analyzer_instance
    from backend.etl.analytics.analyzer import B2BGraphAnalyzer
    from unittest.mock import MagicMock

    df = pd.DataFrame([{"supplier": "ACME", "contract_type": "FRAME", "since_date": "2020-01-01"}])
    mock_analyzer = MagicMock(spec=B2BGraphAnalyzer)
    mock_analyzer.get_supplier_contracts.return_value = df

    def _override():
        yield mock_analyzer

    app.dependency_overrides[get_analyzer_instance] = _override
    try:
        resp = client.get("/api/analytics/risk/supplier-contracts?supplier=ACME")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["supplier"] == "ACME"
    finally:
        app.dependency_overrides.pop(get_analyzer_instance, None)


def test_buyer_supplier_recommendations_missing_param(client: TestClient):
    """Query param 'buyer' is required — missing → 422."""
    resp = client.get("/api/analytics/risk/buyer-supplier-recommendations")
    assert resp.status_code == 422

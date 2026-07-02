"""API tests for /api/company/* and /api/documents/* endpoints."""
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.api


# ── GET /api/company/me ───────────────────────────────────────────────────────

def test_get_my_company_unauthenticated(client: TestClient):
    """No auth header → 401 or 403 depending on FastAPI/HTTPBearer version."""
    resp = client.get("/api/company/me")
    assert resp.status_code in (401, 403)


def test_get_my_company_success(client: TestClient, company_user, make_token):
    """Mock Neo4j session returns a node → 200."""
    from backend.api.main import app
    from backend.api.dependencies import get_analyzer_instance
    from backend.etl.analytics.analyzer import B2BGraphAnalyzer

    # Build a mock that returns a fake company node from session.run().single()
    mock_session = MagicMock()
    mock_session.run.return_value.single.return_value = {
        "c": {"company_id": "COMP-0000042", "legal_name": "Empresa B", "city": "Barcelona"}
    }
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    mock_analyzer = MagicMock(spec=B2BGraphAnalyzer)
    mock_analyzer._driver = mock_driver

    def _override_analyzer():
        yield mock_analyzer

    app.dependency_overrides[get_analyzer_instance] = _override_analyzer
    try:
        token = make_token("user@test.com", company_id="COMP-0000042")
        resp = client.get("/api/company/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
    finally:
        # Restore conftest override
        app.dependency_overrides.pop(get_analyzer_instance, None)


def test_get_my_company_not_found(client: TestClient, company_user, make_token):
    """Mock returns None (no matching company node) → 404."""
    from backend.api.main import app
    from backend.api.dependencies import get_analyzer_instance
    from backend.etl.analytics.analyzer import B2BGraphAnalyzer

    mock_session = MagicMock()
    mock_session.run.return_value.single.return_value = None
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    mock_analyzer = MagicMock(spec=B2BGraphAnalyzer)
    mock_analyzer._driver = mock_driver

    def _override():
        yield mock_analyzer

    app.dependency_overrides[get_analyzer_instance] = _override
    try:
        token = make_token("user@test.com", company_id="COMP-0000042")
        resp = client.get("/api/company/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.pop(get_analyzer_instance, None)


# ── PATCH /api/company/me ─────────────────────────────────────────────────────

def test_patch_my_company_all_none_raises_400(client: TestClient, company_user, make_token):
    """Empty body (all fields None) → 400."""
    token = make_token("user@test.com", company_id="COMP-0000042")
    resp = client.patch(
        "/api/company/me",
        json={},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


# ── GET /api/company/documents ────────────────────────────────────────────────

def test_get_my_documents_unauthenticated(client: TestClient):
    resp = client.get("/api/company/documents")
    assert resp.status_code in (401, 403)


def test_get_my_documents_empty(client: TestClient, company_user, make_token):
    """Mock returns empty list → 200 with empty array."""
    from backend.api.main import app
    from backend.api.dependencies import get_analyzer_instance
    from backend.etl.analytics.analyzer import B2BGraphAnalyzer

    mock_session = MagicMock()
    mock_session.run.return_value.data.return_value = []
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    mock_analyzer = MagicMock(spec=B2BGraphAnalyzer)
    mock_analyzer._driver = mock_driver

    def _override():
        yield mock_analyzer

    app.dependency_overrides[get_analyzer_instance] = _override
    try:
        token = make_token("user@test.com", company_id="COMP-0000042")
        resp = client.get("/api/company/documents", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json() == []
    finally:
        app.dependency_overrides.pop(get_analyzer_instance, None)


# ── PATCH /api/documents/{doc_id}/status ─────────────────────────────────────

def test_update_document_status_invalid_status(client: TestClient, company_user, make_token):
    """Pydantic rejects invalid status → 422."""
    token = make_token("user@test.com", company_id="COMP-0000042")
    resp = client.patch(
        "/api/documents/DOC-001/status",
        json={"status": "BOGUS"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_update_document_status_forbidden(client: TestClient, company_user, make_token):
    """Doc belongs to another company → single() returns None → 403."""
    from backend.api.main import app
    from backend.api.dependencies import get_analyzer_instance
    from backend.etl.analytics.analyzer import B2BGraphAnalyzer

    mock_session = MagicMock()
    mock_session.run.return_value.single.return_value = None
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    mock_analyzer = MagicMock(spec=B2BGraphAnalyzer)
    mock_analyzer._driver = mock_driver
    mock_analyzer._database = "neo4j"

    def _override():
        yield mock_analyzer

    app.dependency_overrides[get_analyzer_instance] = _override
    try:
        token = make_token("user@test.com", company_id="COMP-0000042")
        resp = client.patch(
            "/api/documents/DOC-999/status",
            json={"status": "PAID"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_analyzer_instance, None)

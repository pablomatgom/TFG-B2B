"""Unit tests for backend/api/models/company.py."""
import pytest
from pydantic import ValidationError

from backend.api.models.company import (
    CompanyProfileUpdate,
    DocumentStatusUpdate,
    _VALID_STATUSES,
)

pytestmark = pytest.mark.unit


# ── DocumentStatusUpdate ──────────────────────────────────────────────────────

@pytest.mark.parametrize("status", sorted(_VALID_STATUSES))
def test_document_status_update_all_valid_statuses(status: str):
    obj = DocumentStatusUpdate(status=status)
    assert obj.status == status


def test_document_status_update_invalid_raises():
    with pytest.raises(ValidationError):
        DocumentStatusUpdate(status="BOGUS")


def test_document_status_update_case_sensitive_lowercase():
    """Lowercase 'open' is not in _VALID_STATUSES — must raise."""
    with pytest.raises(ValidationError):
        DocumentStatusUpdate(status="open")


def test_document_status_update_empty_string_raises():
    with pytest.raises(ValidationError):
        DocumentStatusUpdate(status="")


def test_document_status_update_error_message_contains_sorted_options():
    """The error message should list the valid statuses."""
    with pytest.raises(ValidationError) as exc_info:
        DocumentStatusUpdate(status="WRONG")
    errors = exc_info.value.errors()
    assert any("OPEN" in str(e) or "opciones" in str(e).lower() for e in errors)


def test_document_status_update_valid_statuses_count():
    assert len(_VALID_STATUSES) == 10


# ── CompanyProfileUpdate ──────────────────────────────────────────────────────

def test_company_profile_update_all_none_is_valid():
    """Model with no fields provided — all default to None."""
    obj = CompanyProfileUpdate()
    assert obj.legal_name is None
    assert obj.city is None
    assert obj.region is None
    assert obj.is_active is None


def test_company_profile_update_partial_city_only():
    obj = CompanyProfileUpdate(city="Madrid")
    assert obj.city == "Madrid"
    assert obj.legal_name is None
    assert obj.region is None
    assert obj.is_active is None


def test_company_profile_update_is_active_true():
    obj = CompanyProfileUpdate(is_active=True)
    assert obj.is_active is True


def test_company_profile_update_is_active_false():
    obj = CompanyProfileUpdate(is_active=False)
    assert obj.is_active is False


def test_company_profile_update_all_fields():
    obj = CompanyProfileUpdate(legal_name="ACME SL", city="Valencia",
                               region="Valencia", is_active=True)
    assert obj.legal_name == "ACME SL"
    assert obj.city == "Valencia"

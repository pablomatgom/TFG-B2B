"""Unit tests for backend/api/models/auth.py."""
import pytest
from backend.api.models.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)

pytestmark = pytest.mark.unit


# ── LoginRequest ──────────────────────────────────────────────────────────────

def test_login_request_fields():
    req = LoginRequest(email="user@example.com", password="secret")
    assert req.email == "user@example.com"
    assert req.password == "secret"


# ── TokenResponse ─────────────────────────────────────────────────────────────

def test_token_response_defaults_bearer():
    r = TokenResponse(access_token="abc.def.ghi")
    assert r.token_type == "bearer"
    assert r.access_token == "abc.def.ghi"


def test_token_response_custom_type():
    r = TokenResponse(access_token="tok", token_type="custom")
    assert r.token_type == "custom"


# ── UserOut ───────────────────────────────────────────────────────────────────

def test_user_out_all_fields():
    u = UserOut(id=1, email="a@b.com", company_id="COMP-001", role="admin")
    assert u.id == 1
    assert u.full_name is None
    assert u.role == "admin"


def test_user_out_with_full_name():
    u = UserOut(id=2, email="x@y.com", company_id="C-001", role="company_user",
                full_name="John Doe")
    assert u.full_name == "John Doe"


def test_user_out_from_attributes_config():
    """model_config from_attributes=True allows ORM model construction."""
    assert UserOut.model_config.get("from_attributes") is True


# ── RegisterRequest ───────────────────────────────────────────────────────────

def test_register_request_defaults_role():
    r = RegisterRequest(email="new@test.com", password="pw", company_id="C-99")
    assert r.role == "company_user"
    assert r.full_name is None


def test_register_request_custom_role():
    r = RegisterRequest(email="a@b.com", password="pw", company_id="C-1", role="admin")
    assert r.role == "admin"

"""API tests for /auth/* endpoints."""
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.api


# ── POST /auth/login ──────────────────────────────────────────────────────────

def test_login_success(client: TestClient, admin_user):
    resp = client.post("/auth/login", json={"email": "admin@test.com", "password": "adminpass"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, admin_user):
    resp = client.post("/auth/login", json={"email": "admin@test.com", "password": "wrongpass"})
    assert resp.status_code == 401


def test_login_unknown_email(client: TestClient):
    resp = client.post("/auth/login", json={"email": "nobody@test.com", "password": "pass"})
    assert resp.status_code == 401


def test_login_inactive_user(client: TestClient, test_db):
    """Inactive user (is_active=0) is rejected with 401."""
    import datetime
    import bcrypt
    from backend.auth.db.database import User

    pw_hash = bcrypt.hashpw(b"pw", bcrypt.gensalt()).decode()
    user = User(email="inactive@test.com", hashed_password=pw_hash,
                company_id="C-999", role="company_user", is_active=0,
                created_at=datetime.datetime.utcnow())
    test_db.add(user)
    test_db.commit()

    resp = client.post("/auth/login", json={"email": "inactive@test.com", "password": "pw"})
    assert resp.status_code == 401


# ── GET /auth/me ──────────────────────────────────────────────────────────────

def test_get_me_valid_token(client: TestClient, admin_user, make_token):
    token = make_token("admin@test.com", role="admin", company_id="COMP-0000001")
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@test.com"


def test_get_me_expired_token(client: TestClient, admin_user, make_token):
    token = make_token("admin@test.com", expired=True)
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_get_me_malformed_token(client: TestClient):
    resp = client.get("/auth/me", headers={"Authorization": "Bearer garbage.not.valid"})
    assert resp.status_code == 401


def test_get_me_no_token(client: TestClient):
    """No auth header → HTTPBearer raises 401 or 403 depending on FastAPI version."""
    resp = client.get("/auth/me")
    assert resp.status_code in (401, 403)


# ── POST /auth/register ───────────────────────────────────────────────────────

def test_register_by_admin(client: TestClient, admin_user, make_token, test_db):
    token = make_token("admin@test.com", role="admin", company_id="COMP-0000001")
    resp = client.post(
        "/auth/register",
        json={"email": "new@test.com", "password": "pw123", "company_id": "C-NEW"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@test.com"
    assert "id" in data


def test_register_by_non_admin(client: TestClient, company_user, make_token):
    token = make_token("user@test.com", role="company_user", company_id="COMP-0000042")
    resp = client.post(
        "/auth/register",
        json={"email": "another@test.com", "password": "pw", "company_id": "C-X"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_register_duplicate_email_returns_409(client: TestClient, admin_user, make_token):
    """The 409 check happens BEFORE the INSERT, so it's not affected by the datetime bug."""
    token = make_token("admin@test.com", role="admin", company_id="COMP-0000001")
    # admin@test.com already exists (via admin_user fixture)
    resp = client.post(
        "/auth/register",
        json={"email": "admin@test.com", "password": "pw", "company_id": "C-DUP"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409

"""Shared fixtures for the TFG-B2B test suite.

No real Neo4j or Docker is needed. All Neo4j interactions are mocked
by patching ``GraphDatabase.driver`` before the first module import.
All FastAPI tests use an in-memory SQLite database.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import bcrypt
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

# ── Constants used across fixtures ────────────────────────────────────────────
TEST_SECRET = "test-secret-key-for-tests"
ALGORITHM = "HS256"


# ── Settings override ─────────────────────────────────────────────────────────

@pytest.fixture
def override_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Settings whose data paths point inside tmp_path — never touch real data/."""
    from backend.core.config import Settings

    s = Settings(
        project_root=tmp_path,
        data_raw_dir=tmp_path / "raw",
        data_synthetic_dir=tmp_path / "synthetic",
        data_processed_dir=tmp_path / "processed",
        data_export_dir=tmp_path / "export",
        sqlite_db_path=tmp_path / "users.db",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="test",
        neo4j_database="neo4j",
        jwt_secret_key=TEST_SECRET,
        seed=42,
    )
    monkeypatch.setattr("backend.core.config.load_settings", lambda: s)
    return s


# ── In-memory SQLite DB ───────────────────────────────────────────────────────

@pytest.fixture
def test_engine():
    """In-memory SQLite engine with all tables created — never touches data/users.db.

    Uses StaticPool so every Session gets the same single in-memory connection.
    Without StaticPool, each new SQLAlchemy connection would open a fresh empty
    in-memory database, causing 'no such table' errors.
    """
    from backend.auth.db.database import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def test_db(test_engine) -> Generator[Session, None, None]:
    """In-memory SQLite session — never writes to data/users.db."""
    with Session(test_engine) as session:
        yield session


# ── Pre-seeded test users ─────────────────────────────────────────────────────

@pytest.fixture
def admin_user(test_db: Session):
    """Admin user inserted into the in-memory DB."""
    import datetime
    from backend.auth.db.database import User

    pw_hash = bcrypt.hashpw(b"adminpass", bcrypt.gensalt()).decode()
    user = User(
        email="admin@test.com",
        hashed_password=pw_hash,
        company_id="COMP-0000001",
        role="admin",
        is_active=1,
        created_at=datetime.datetime.utcnow(),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def company_user(test_db: Session):
    """Regular company_user inserted into the in-memory DB."""
    import datetime
    from backend.auth.db.database import User

    pw_hash = bcrypt.hashpw(b"userpass", bcrypt.gensalt()).decode()
    user = User(
        email="user@test.com",
        hashed_password=pw_hash,
        company_id="COMP-0000042",
        role="company_user",
        is_active=1,
        created_at=datetime.datetime.utcnow(),
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


# ── JWT factory ───────────────────────────────────────────────────────────────

@pytest.fixture
def make_token():
    """Returns a factory that mints HS256 JWTs for testing."""

    def _factory(
        email: str,
        role: str = "company_user",
        company_id: str = "COMP-0000001",
        expired: bool = False,
    ) -> str:
        exp = datetime.datetime.utcnow() + (
            datetime.timedelta(hours=-1)
            if expired
            else datetime.timedelta(hours=24)
        )
        payload = {
            "sub": email,
            "role": role,
            "company_id": company_id,
            "full_name": None,
            "exp": exp,
        }
        return jwt.encode(payload, TEST_SECRET, algorithm=ALGORITHM)

    return _factory


# ── Mock Neo4j driver ─────────────────────────────────────────────────────────

@pytest.fixture
def mock_neo4j(mocker):
    """Patches GraphDatabase.driver everywhere so no real TCP connection is opened."""
    mock_driver = MagicMock()
    mocker.patch(
        "backend.etl.analytics.analyzer.GraphDatabase.driver",
        return_value=mock_driver,
    )
    mocker.patch(
        "backend.etl.loader.GraphDatabase.driver",
        return_value=mock_driver,
    )
    return mock_driver


# ── FastAPI TestClient ────────────────────────────────────────────────────────

@pytest.fixture
def client(test_engine, test_db: Session, mock_neo4j, monkeypatch, override_settings):
    """FastAPI TestClient with in-memory DB and Neo4j fully mocked."""
    from backend.api.main import app
    from backend.api.dependencies import get_analyzer_instance
    from backend.etl.analytics.analyzer import B2BGraphAnalyzer

    # Redirect the module-level SQLite engine to the in-memory test engine.
    # get_db() creates Session(engine) using this engine, so patching it
    # ensures all requests use the test DB instead of data/users.db.
    import backend.auth.db.database as _db_module
    monkeypatch.setattr(_db_module, "engine", test_engine)

    # Patch module-level constants so JWT validation uses the test secret
    monkeypatch.setattr("backend.api.dependencies.SECRET_KEY", TEST_SECRET)
    monkeypatch.setattr("backend.api.routers.auth.SECRET_KEY", TEST_SECRET)

    # Patch EXPORT_DIR to point at tmp export directory
    monkeypatch.setattr(
        "backend.api.dependencies.EXPORT_DIR",
        override_settings.data_export_dir,
    )

    analyzer_mock = MagicMock(spec=B2BGraphAnalyzer)

    def override_analyzer():
        yield analyzer_mock

    app.dependency_overrides[get_analyzer_instance] = override_analyzer

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


# ── Pipeline state reset ──────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_pipeline_state():
    """Resets the pipeline router's in-memory state between every test."""
    import backend.api.routers.pipeline as pipeline_module

    with pipeline_module._lock:
        pipeline_module._state.update(
            {"status": "idle", "started_at": None, "finished_at": None, "message": ""}
        )
    yield
    with pipeline_module._lock:
        pipeline_module._state.update(
            {"status": "idle", "started_at": None, "finished_at": None, "message": ""}
        )


# ── CSV fixture helpers ───────────────────────────────────────────────────────

@pytest.fixture
def municipios_csv(tmp_path: Path) -> Path:
    """Minimal municipios_espana.csv with 3 Spanish municipalities."""
    path = tmp_path / "municipios_espana.csv"
    path.write_text(
        "Provincia;Población;Latitud;Longitud;Habitantes\n"
        "Madrid;Madrid;40.4168;-3.7038;3300000\n"
        "Barcelona;Barcelona;41.3874;2.1686;1600000\n"
        "Sevilla;Sevilla;37.3886;-5.9823;690000\n",
        encoding="utf-8-sig",
    )
    return path


@pytest.fixture
def minimal_companies_csv(tmp_path: Path) -> Path:
    """3-row companies.csv matching the canonical CSV_SCHEMAS header."""
    path = tmp_path / "companies.csv"
    path.write_text(
        "company_id:ID(Company),legal_name:string,tax_id:string,edi_endpoint:string,"
        "node_role:string,country:string,region:string,city:string,"
        "latitude:float,longitude:float,industry_code:string,size_band:string,"
        "baseline_revenue:float,created_at:datetime,is_active:boolean\n"
        "COMP-0000001,Empresa A,ESA0000001,edi://a,SUPPLIER,Spain,Madrid,Madrid,"
        "40.4168,-3.7038,C10,pyme,500000.0,2020-01-01T00:00:00,true\n"
        "COMP-0000002,Empresa B,ESB0000002,edi://b,BUYER,Spain,Barcelona,Barcelona,"
        "41.3874,2.1686,G46,mid,2000000.0,2019-06-15T00:00:00,true\n"
        "COMP-0000003,Empresa C,ESC0000003,edi://c,HYBRID,Spain,Sevilla,Sevilla,"
        "37.3886,-5.9823,M71,pyme,750000.0,2021-03-10T00:00:00,true\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def minimal_supplies_csv(tmp_path: Path) -> Path:
    """Minimal rel_supplies.csv with 2 supply relationships."""
    path = tmp_path / "rel_supplies.csv"
    path.write_text(
        ":START_ID(Company),:END_ID(Company),since_date:date,lead_time_days:int,"
        "reliability_score:float,agreed_volume_baseline:float,"
        "is_exclusive_supplier:boolean,payment_terms_agreed:int,contract_type:string,:TYPE\n"
        "COMP-0000001,COMP-0000002,2020-06-01,5,0.95,50000.0,false,30,FRAME,SUPPLIES\n"
        "COMP-0000003,COMP-0000002,2021-01-15,3,0.92,30000.0,false,45,ANNUAL,SUPPLIES\n",
        encoding="utf-8",
    )
    return path


# ── Export dir JSON helper ────────────────────────────────────────────────────

@pytest.fixture
def write_export_json(override_settings):
    """Returns a helper that writes a JSON file to the export directory."""

    def _write(filename: str, content) -> Path:
        export_dir = override_settings.data_export_dir
        export_dir.mkdir(parents=True, exist_ok=True)
        p = export_dir / filename
        p.write_text(json.dumps(content), encoding="utf-8")
        return p

    return _write

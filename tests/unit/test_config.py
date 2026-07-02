"""Unit tests for backend/core/config.py."""
import dataclasses
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_load_settings_defaults(monkeypatch):
    """With no env vars set, default Neo4j URI is used."""
    for var in ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE",
                "JWT_SECRET_KEY", "TFG_SEED"):
        monkeypatch.delenv(var, raising=False)

    from backend.core.config import load_settings
    s = load_settings()
    assert s.neo4j_uri == "bolt://localhost:7687"
    assert s.neo4j_user == "neo4j"
    assert s.neo4j_database == "neo4j"
    assert s.seed is None


def test_load_settings_env_override(monkeypatch):
    """NEO4J_URI env var propagates to settings.neo4j_uri."""
    monkeypatch.setenv("NEO4J_URI", "bolt://custom-host:7687")
    monkeypatch.delenv("TFG_SEED", raising=False)

    from backend.core.config import load_settings
    s = load_settings()
    assert s.neo4j_uri == "bolt://custom-host:7687"


def test_seed_from_env_integer(monkeypatch):
    monkeypatch.setenv("TFG_SEED", "42")

    from backend.core.config import load_settings
    s = load_settings()
    assert s.seed == 42


def test_seed_empty_string_is_none(monkeypatch):
    """TFG_SEED='' (empty string) is falsy → seed=None (walrus operator)."""
    monkeypatch.setenv("TFG_SEED", "")

    from backend.core.config import load_settings
    s = load_settings()
    assert s.seed is None


def test_seed_unset_is_none(monkeypatch):
    monkeypatch.delenv("TFG_SEED", raising=False)

    from backend.core.config import load_settings
    s = load_settings()
    assert s.seed is None


def test_settings_is_frozen():
    """Settings is a frozen dataclass — direct mutation raises FrozenInstanceError."""
    from backend.core.config import load_settings
    s = load_settings()
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.seed = 1  # type: ignore[misc]


def test_settings_replace_works():
    """Use dataclasses.replace() to create a modified copy (the intended pattern)."""
    from backend.core.config import load_settings
    s = load_settings()
    s2 = dataclasses.replace(s, seed=99)
    assert s2.seed == 99
    assert s.seed != 99  # original unchanged


def test_ensure_data_directories_creates_paths(tmp_path: Path):
    """ensure_data_directories() creates all four data directories."""
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
        jwt_secret_key="k",
        seed=None,
    )
    s.ensure_data_directories()
    for d in (s.data_raw_dir, s.data_synthetic_dir, s.data_processed_dir, s.data_export_dir):
        assert d.is_dir()


def test_ensure_data_directories_is_idempotent(tmp_path: Path):
    """Calling ensure_data_directories() twice does not raise."""
    from backend.core.config import Settings

    s = Settings(
        project_root=tmp_path,
        data_raw_dir=tmp_path / "raw",
        data_synthetic_dir=tmp_path / "synth",
        data_processed_dir=tmp_path / "proc",
        data_export_dir=tmp_path / "exp",
        sqlite_db_path=tmp_path / "users.db",
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="test",
        neo4j_database="neo4j",
        jwt_secret_key="k",
        seed=None,
    )
    s.ensure_data_directories()
    s.ensure_data_directories()  # must not raise

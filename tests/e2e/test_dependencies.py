"""E2E tests for backend/api/dependencies.py helpers."""
import json
import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.e2e


# ── read_json ─────────────────────────────────────────────────────────────────

def test_read_json_file_missing_returns_empty_dict(tmp_path: Path, monkeypatch):
    """Missing file + default=None → returns {}."""
    monkeypatch.setattr("backend.api.dependencies.EXPORT_DIR", tmp_path)
    from backend.api.dependencies import read_json
    result = read_json("nonexistent.json")
    assert result == {}


def test_read_json_custom_default(tmp_path: Path, monkeypatch):
    """Missing file + default=[] → returns []."""
    monkeypatch.setattr("backend.api.dependencies.EXPORT_DIR", tmp_path)
    from backend.api.dependencies import read_json
    result = read_json("missing.json", default=[])
    assert result == []


def test_read_json_reads_existing_file(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("backend.api.dependencies.EXPORT_DIR", tmp_path)
    (tmp_path / "data.json").write_text(json.dumps({"key": "value"}), encoding="utf-8")
    from backend.api.dependencies import read_json
    result = read_json("data.json")
    assert result == {"key": "value"}


def test_read_json_reads_list_file(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("backend.api.dependencies.EXPORT_DIR", tmp_path)
    (tmp_path / "list.json").write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    from backend.api.dependencies import read_json
    result = read_json("list.json", default=[])
    assert result == [1, 2, 3]


def test_read_json_default_none_returns_dict(tmp_path: Path, monkeypatch):
    """Explicit default=None also falls back to {} (documented behavior)."""
    monkeypatch.setattr("backend.api.dependencies.EXPORT_DIR", tmp_path)
    from backend.api.dependencies import read_json
    result = read_json("x.json", default=None)
    assert result == {}


# ── neo4j_to_dict ─────────────────────────────────────────────────────────────

def test_neo4j_to_dict_plain_values():
    from backend.api.dependencies import neo4j_to_dict
    node = {"name": "ACME", "score": 1.5, "active": True}
    result = neo4j_to_dict(node)
    assert result == {"name": "ACME", "score": 1.5, "active": True}


def test_neo4j_to_dict_python_date():
    """Python date has isoformat() → converted to ISO string."""
    from backend.api.dependencies import neo4j_to_dict
    d = datetime.date(2024, 3, 15)
    result = neo4j_to_dict({"created_at": d, "name": "test"})
    assert result["created_at"] == "2024-03-15"
    assert result["name"] == "test"


def test_neo4j_to_dict_python_datetime():
    """Python datetime has isoformat() → converted."""
    from backend.api.dependencies import neo4j_to_dict
    dt = datetime.datetime(2024, 3, 15, 10, 0, 0)
    result = neo4j_to_dict({"ts": dt})
    assert "2024-03-15" in result["ts"]


def test_neo4j_to_dict_neo4j_date_object():
    """Object with iso_format() method (Neo4j native Date) → iso_format() called first."""
    from backend.api.dependencies import neo4j_to_dict

    class Neo4jDate:
        def iso_format(self) -> str:
            return "2024-03-15"
        # also has isoformat but iso_format takes priority
        def isoformat(self) -> str:
            return "should-not-be-called"

    result = neo4j_to_dict({"date": Neo4jDate()})
    assert result["date"] == "2024-03-15"


def test_neo4j_to_dict_none_value():
    """None values are kept as-is (no conversion)."""
    from backend.api.dependencies import neo4j_to_dict
    result = neo4j_to_dict({"field": None})
    assert result["field"] is None


def test_neo4j_to_dict_empty_dict():
    from backend.api.dependencies import neo4j_to_dict
    assert neo4j_to_dict({}) == {}

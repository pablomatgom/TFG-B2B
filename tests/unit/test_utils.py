"""Unit tests for backend/core/utils.py — pure functions, no I/O."""
import json
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from backend.core.utils import (
    export_df_to_json,
    export_dict_to_json,
    pick,
    safe_date,
    safe_float,
    safe_int,
    write_step_artifact,
)

pytestmark = pytest.mark.unit


# ── safe_int ──────────────────────────────────────────────────────────────────

def test_safe_int_integer_string():
    assert safe_int("42") == 42


def test_safe_int_float_string():
    # "5000.0" → strips all '.' → "50000" → 50000. Dots are treated as thousands separators.
    assert safe_int("5000.0") == 50000


def test_safe_int_european_thousands():
    # Strips '.' (European thousands separator) → "5000" → 5000
    assert safe_int("5.000") == 5000


def test_safe_int_decimal_asymmetry():
    # "14.5" strips '.' → "145" → int(float("145")) = 145.
    # This is a documented asymmetry: it's NOT 14 because dots are stripped first.
    assert safe_int("14.5") == 145


def test_safe_int_comma_decimal():
    # European decimal comma: "5,5" → strips nothing, replaces ',' → "5.5" → 5
    assert safe_int("5,5") == 5


def test_safe_int_none_returns_default():
    assert safe_int(None) == 0


def test_safe_int_empty_string_returns_default():
    assert safe_int("") == 0


def test_safe_int_whitespace_returns_default():
    assert safe_int("   ") == 0


def test_safe_int_non_numeric_returns_default():
    assert safe_int("abc") == 0


def test_safe_int_custom_default():
    assert safe_int(None, default=-1) == -1


def test_safe_int_negative():
    assert safe_int("-7") == -7


# ── safe_float ────────────────────────────────────────────────────────────────

def test_safe_float_basic():
    assert safe_float("3.14") == pytest.approx(3.14)


def test_safe_float_comma_decimal():
    assert safe_float("3,14") == pytest.approx(3.14)


def test_safe_float_european_thousands_not_stripped():
    # safe_float only replaces ','. Dots are NOT stripped — asymmetry with safe_int.
    assert safe_float("5.000") == pytest.approx(5.0)


def test_safe_float_none():
    assert safe_float(None) == 0.0


def test_safe_float_empty():
    assert safe_float("") == 0.0


def test_safe_float_whitespace():
    assert safe_float("  ") == 0.0


def test_safe_float_non_numeric():
    assert safe_float("abc") == 0.0


def test_safe_float_custom_default():
    assert safe_float(None, default=99.9) == pytest.approx(99.9)


def test_safe_float_negative():
    assert safe_float("-1.5") == pytest.approx(-1.5)


# ── safe_date ─────────────────────────────────────────────────────────────────

def test_safe_date_iso_date_only():
    result = safe_date("2024-03-15", default=date(2000, 1, 1))
    assert result == date(2024, 3, 15)


def test_safe_date_iso_datetime_with_z():
    result = safe_date("2024-03-15T10:00:00Z", default=date(2000, 1, 1))
    assert result == date(2024, 3, 15)


def test_safe_date_iso_datetime_with_offset():
    result = safe_date("2024-03-15T10:00:00+00:00", default=date(2000, 1, 1))
    assert result == date(2024, 3, 15)


def test_safe_date_none_returns_default():
    default = date(2000, 1, 1)
    assert safe_date(None, default=default) is default


def test_safe_date_empty_string_returns_default():
    default = date(2000, 1, 1)
    assert safe_date("", default=default) is default


def test_safe_date_invalid_string_returns_default():
    default = date(2000, 1, 1)
    assert safe_date("not-a-date", default=default) is default


def test_safe_date_whitespace_returns_default():
    default = date(2000, 1, 1)
    assert safe_date("   ", default=default) is default


# ── pick ──────────────────────────────────────────────────────────────────────

def test_pick_returns_first_match():
    assert pick({"a": "1", "b": "2"}, "a", "b") == "1"


def test_pick_skips_none_values():
    assert pick({"a": None, "b": "2"}, "a", "b") == "2"


def test_pick_returns_empty_string():
    # Empty string is NOT None — should be returned, not skipped
    assert pick({"a": ""}, "a") == ""


def test_pick_all_none_returns_none():
    assert pick({"a": None, "b": None}, "a", "b") is None


def test_pick_missing_key_returns_none():
    assert pick({}, "x") is None


def test_pick_mixed_none_and_value():
    assert pick({"x": None, "y": None, "z": "found"}, "x", "y", "z") == "found"


# ── write_step_artifact ───────────────────────────────────────────────────────

def test_write_step_artifact_creates_file(tmp_path: Path):
    payload = {"rows": 100, "elapsed": 1.23}
    result = write_step_artifact(tmp_path / "processed", "generate", payload)
    assert result.exists()
    assert result.name == "generate_last_run.json"
    data = json.loads(result.read_text(encoding="utf-8"))
    assert data["rows"] == 100


def test_write_step_artifact_creates_parent_dirs(tmp_path: Path):
    nested = tmp_path / "a" / "b" / "c"
    write_step_artifact(nested, "load", {"ok": True})
    assert nested.exists()
    assert (nested / "load_last_run.json").exists()


def test_write_step_artifact_overwrites_existing(tmp_path: Path):
    proc = tmp_path / "processed"
    write_step_artifact(proc, "test", {"v": 1})
    write_step_artifact(proc, "test", {"v": 2})
    data = json.loads((proc / "test_last_run.json").read_text())
    assert data["v"] == 2


# ── export_dict_to_json ───────────────────────────────────────────────────────

def test_export_dict_to_json(tmp_path: Path):
    data = {"key": "value", "nested": {"n": 1}}
    p = export_dict_to_json(data, tmp_path / "export", "out.json")
    assert p.exists()
    loaded = json.loads(p.read_text(encoding="utf-8"))
    assert loaded == data


def test_export_dict_to_json_creates_dir(tmp_path: Path):
    export_dict_to_json({}, tmp_path / "new" / "dir", "x.json")
    assert (tmp_path / "new" / "dir" / "x.json").exists()


# ── export_df_to_json ─────────────────────────────────────────────────────────

def test_export_df_to_json(tmp_path: Path):
    df = pd.DataFrame([{"a": 1, "b": "x"}, {"a": 2, "b": "y"}])
    p = export_df_to_json(df, tmp_path / "export", "df.json")
    assert p.exists()
    loaded = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(loaded, list)
    assert len(loaded) == 2
    assert loaded[0]["a"] == 1


def test_export_df_to_json_empty_df(tmp_path: Path):
    df = pd.DataFrame()
    p = export_df_to_json(df, tmp_path / "export", "empty.json")
    assert p.exists()

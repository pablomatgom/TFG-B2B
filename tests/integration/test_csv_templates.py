"""Integration tests for backend/etl/generation/csv_templates.py."""
import csv
from pathlib import Path

import pytest

from backend.etl.generation.csv_templates import (
    CSV_SCHEMAS,
    create_csv_templates,
    get_available_targets,
    resolve_csv_targets,
)

pytestmark = pytest.mark.integration

ALL_CSVS = sorted(CSV_SCHEMAS.keys())


# ── resolve_csv_targets ───────────────────────────────────────────────────────

def test_resolve_all_returns_all_csvs():
    result = resolve_csv_targets("all")
    assert result == ALL_CSVS


def test_resolve_single_with_extension():
    assert resolve_csv_targets("companies.csv") == ["companies.csv"]


def test_resolve_single_without_extension():
    assert resolve_csv_targets("companies") == ["companies.csv"]


def test_resolve_case_insensitive():
    assert resolve_csv_targets("COMPANIES.CSV") == ["companies.csv"]


def test_resolve_with_whitespace():
    assert resolve_csv_targets("  companies  ") == ["companies.csv"]


def test_resolve_invalid_raises_value_error():
    with pytest.raises(ValueError, match="inválido"):
        resolve_csv_targets("bogus_dataset")


def test_resolve_returns_sorted():
    result = resolve_csv_targets("all")
    assert result == sorted(result)


# ── get_available_targets ─────────────────────────────────────────────────────

def test_get_available_targets_sorted():
    targets = get_available_targets()
    assert targets == sorted(targets)


def test_get_available_targets_no_extension():
    targets = get_available_targets()
    for t in targets:
        assert not t.endswith(".csv")


def test_get_available_targets_count():
    assert len(get_available_targets()) == len(CSV_SCHEMAS)


# ── create_csv_templates ──────────────────────────────────────────────────────

def test_create_csv_templates_all_creates_five_files(tmp_path: Path):
    files = create_csv_templates(tmp_path / "synthetic", "all")
    assert len(files) == 5
    for f in files:
        assert f.exists()


def test_create_csv_templates_single(tmp_path: Path):
    files = create_csv_templates(tmp_path, "companies.csv")
    assert len(files) == 1
    assert files[0].name == "companies.csv"


def test_create_csv_templates_creates_parent_dir(tmp_path: Path):
    nested = tmp_path / "a" / "b" / "synthetic"
    create_csv_templates(nested, "companies.csv")
    assert nested.is_dir()


def test_create_csv_templates_invalid_raises(tmp_path: Path):
    with pytest.raises(ValueError):
        create_csv_templates(tmp_path, "not_a_real_csv")


def test_create_csv_templates_header_matches_schema(tmp_path: Path):
    """Every created CSV must have exactly the header from CSV_SCHEMAS."""
    files = create_csv_templates(tmp_path, "all")
    for f in files:
        with f.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader)
        assert header == CSV_SCHEMAS[f.name], f"Header mismatch for {f.name}"


def test_create_csv_templates_only_header_row(tmp_path: Path):
    """Newly created templates have exactly one row (the header)."""
    files = create_csv_templates(tmp_path, "companies.csv")
    with files[0].open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))
    assert len(rows) == 1


def test_create_csv_templates_idempotent(tmp_path: Path):
    """Running twice does not raise and overwrites cleanly."""
    create_csv_templates(tmp_path, "companies.csv")
    create_csv_templates(tmp_path, "companies.csv")
    files = list(tmp_path.glob("companies.csv"))
    assert len(files) == 1

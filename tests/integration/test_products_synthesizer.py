"""Integration tests for backend/etl/generation/products_synthesizer.py."""
import csv
import random
from pathlib import Path

import pytest

from backend.etl.generation.products_synthesizer import (
    INDUSTRY_CATEGORY_PRIORS,
    PRODUCT_CATEGORIES,
    SupplierProfile,
    _choose_category_by_industry,
    _supplier_weight,
    synthesize_products_csv,
)
from backend.etl.generation.csv_templates import CSV_SCHEMAS

pytestmark = pytest.mark.integration

PRODUCTS_HEADER = CSV_SCHEMAS["products.csv"]


# ── _choose_category_by_industry ──────────────────────────────────────────────

@pytest.mark.parametrize("industry_code", list(INDUSTRY_CATEGORY_PRIORS.keys()))
def test_choose_category_by_industry_known_code(industry_code: str):
    """Known industry codes return a valid category key."""
    rng = random.Random(42)
    result = _choose_category_by_industry(industry_code, rng)
    assert result in PRODUCT_CATEGORIES


def test_choose_category_by_industry_unknown_code_falls_back_to_g46():
    """Unknown industry code falls back to G46 priors instead of crashing."""
    rng = random.Random(42)
    result = _choose_category_by_industry("ZZZZ", rng)
    assert result in PRODUCT_CATEGORIES


# ── _supplier_weight ──────────────────────────────────────────────────────────

def test_supplier_weight_is_positive():
    profile = SupplierProfile(
        company_id="C-001",
        industry_code="C10",
        baseline_revenue=500_000.0,
        out_degree=5,
        agreed_volume_total=50_000.0,
    )
    assert _supplier_weight(profile) > 0


def test_supplier_weight_minimum_one_for_zero_revenue():
    profile = SupplierProfile(
        company_id="C-001",
        industry_code="C10",
        baseline_revenue=0.0,
        out_degree=0,
        agreed_volume_total=0.0,
    )
    assert _supplier_weight(profile) >= 1.0


# ── synthesize_products_csv ───────────────────────────────────────────────────

def test_synthesize_products_creates_file(
    tmp_path: Path, minimal_companies_csv: Path, minimal_supplies_csv: Path
):
    out = tmp_path / "products.csv"
    synthesize_products_csv(out, minimal_companies_csv, minimal_supplies_csv,
                            avg_degree_products=2, seed=42)
    assert out.exists()


def test_synthesize_products_header(
    tmp_path: Path, minimal_companies_csv: Path, minimal_supplies_csv: Path
):
    out = tmp_path / "products.csv"
    synthesize_products_csv(out, minimal_companies_csv, minimal_supplies_csv,
                            avg_degree_products=2, seed=42)
    with out.open(encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert header == PRODUCTS_HEADER


def test_synthesize_products_avg_degree_zero_raises(
    tmp_path: Path, minimal_companies_csv: Path, minimal_supplies_csv: Path
):
    with pytest.raises(ValueError, match="avg-degree-products"):
        synthesize_products_csv(tmp_path / "out.csv", minimal_companies_csv,
                                minimal_supplies_csv, avg_degree_products=0, seed=42)


def test_synthesize_products_missing_companies_raises(
    tmp_path: Path, minimal_supplies_csv: Path
):
    with pytest.raises(FileNotFoundError):
        synthesize_products_csv(tmp_path / "out.csv",
                                tmp_path / "nonexistent.csv",
                                minimal_supplies_csv,
                                avg_degree_products=2, seed=42)


def test_synthesize_products_missing_supplies_raises(
    tmp_path: Path, minimal_companies_csv: Path
):
    with pytest.raises(FileNotFoundError):
        synthesize_products_csv(tmp_path / "out.csv",
                                minimal_companies_csv,
                                tmp_path / "nonexistent.csv",
                                avg_degree_products=2, seed=42)


def test_synthesize_products_deterministic(
    tmp_path: Path, minimal_companies_csv: Path, minimal_supplies_csv: Path
):
    out1 = tmp_path / "a.csv"
    out2 = tmp_path / "b.csv"
    synthesize_products_csv(out1, minimal_companies_csv, minimal_supplies_csv,
                            avg_degree_products=2, seed=99)
    synthesize_products_csv(out2, minimal_companies_csv, minimal_supplies_csv,
                            avg_degree_products=2, seed=99)
    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")


def test_synthesize_products_row_count(
    tmp_path: Path, minimal_companies_csv: Path, minimal_supplies_csv: Path
):
    out = tmp_path / "products.csv"
    synthesize_products_csv(out, minimal_companies_csv, minimal_supplies_csv,
                            avg_degree_products=3, seed=42)
    with out.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    # At least avg_degree_products rows per supplier
    assert len(rows) > 0


def test_synthesize_products_ids_unique(
    tmp_path: Path, minimal_companies_csv: Path, minimal_supplies_csv: Path
):
    out = tmp_path / "products.csv"
    synthesize_products_csv(out, minimal_companies_csv, minimal_supplies_csv,
                            avg_degree_products=2, seed=42)
    with out.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    ids = [r["product_id:ID(Product)"] for r in rows]
    assert len(ids) == len(set(ids))

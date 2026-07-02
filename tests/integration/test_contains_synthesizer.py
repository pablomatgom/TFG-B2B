"""Integration tests for backend/etl/generation/rel_contains_synthesizer.py."""
import csv
from pathlib import Path

import pytest

from backend.etl.generation.rel_contains_synthesizer import synthesize_rel_contains_csv
from backend.etl.generation.companies_synthesizer import synthesize_companies_csv
from backend.etl.generation.supplies_synthesizer import synthesize_rel_supplies_csv
from backend.etl.generation.products_synthesizer import synthesize_products_csv
from backend.etl.generation.documents_synthesizer import synthesize_documents_csv
from backend.etl.generation.csv_templates import CSV_SCHEMAS

pytestmark = pytest.mark.integration

CONTAINS_HEADER = CSV_SCHEMAS["rel_contains.csv"]


@pytest.fixture
def pipeline_outputs(tmp_path: Path, municipios_csv: Path):
    """Runs the full generation pipeline into tmp_path."""
    companies_csv = tmp_path / "companies.csv"
    supplies_csv = tmp_path / "rel_supplies.csv"
    products_csv = tmp_path / "products.csv"
    documents_csv = tmp_path / "documents.csv"

    synthesize_companies_csv(companies_csv, municipios_csv, rows=20, seed=42,
                             gamma=2.4, beta=1.8, mu=0.3)
    synthesize_rel_supplies_csv(supplies_csv, companies_csv, avg_out_degree=2,
                                mu=0.3, seed=42)
    synthesize_products_csv(products_csv, companies_csv, supplies_csv,
                            avg_degree_products=3, seed=42)
    synthesize_documents_csv(documents_csv, companies_csv, supplies_csv,
                             seed=42, avg_out_degree=2)
    return {
        "companies": companies_csv,
        "supplies": supplies_csv,
        "products": products_csv,
        "documents": documents_csv,
        "tmp": tmp_path,
    }


# ── basic creation ────────────────────────────────────────────────────────────

def test_synthesize_contains_creates_file(pipeline_outputs):
    out = pipeline_outputs["tmp"] / "rel_contains.csv"
    synthesize_rel_contains_csv(
        out, pipeline_outputs["documents"], pipeline_outputs["products"], seed=42
    )
    assert out.exists()


def test_synthesize_contains_header(pipeline_outputs):
    out = pipeline_outputs["tmp"] / "rel_contains_h.csv"
    synthesize_rel_contains_csv(
        out, pipeline_outputs["documents"], pipeline_outputs["products"], seed=42
    )
    with out.open(encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert header == CONTAINS_HEADER


def test_synthesize_contains_has_rows(pipeline_outputs):
    out = pipeline_outputs["tmp"] / "rel_contains_r.csv"
    synthesize_rel_contains_csv(
        out, pipeline_outputs["documents"], pipeline_outputs["products"], seed=42
    )
    with out.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) > 0


def test_synthesize_contains_deterministic(pipeline_outputs):
    out1 = pipeline_outputs["tmp"] / "rc_a.csv"
    out2 = pipeline_outputs["tmp"] / "rc_b.csv"
    synthesize_rel_contains_csv(
        out1, pipeline_outputs["documents"], pipeline_outputs["products"], seed=7
    )
    synthesize_rel_contains_csv(
        out2, pipeline_outputs["documents"], pipeline_outputs["products"], seed=7
    )
    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")


# ── validation ────────────────────────────────────────────────────────────────

def test_synthesize_contains_missing_documents_raises(tmp_path: Path, pipeline_outputs):
    with pytest.raises(FileNotFoundError):
        synthesize_rel_contains_csv(
            tmp_path / "out.csv",
            tmp_path / "nonexistent_docs.csv",
            pipeline_outputs["products"],
            seed=42,
        )


def test_synthesize_contains_missing_products_raises(tmp_path: Path, pipeline_outputs):
    with pytest.raises(FileNotFoundError):
        synthesize_rel_contains_csv(
            tmp_path / "out.csv",
            pipeline_outputs["documents"],
            tmp_path / "nonexistent_products.csv",
            seed=42,
        )

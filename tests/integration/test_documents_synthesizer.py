"""Integration tests for backend/etl/generation/documents_synthesizer.py."""
import csv
from pathlib import Path

import pytest

from backend.etl.generation.documents_synthesizer import (
    synthesize_documents_csv,
)
from backend.etl.generation.csv_templates import CSV_SCHEMAS
from backend.etl.generation.companies_synthesizer import synthesize_companies_csv
from backend.etl.generation.supplies_synthesizer import synthesize_rel_supplies_csv

pytestmark = pytest.mark.integration

DOCS_HEADER = CSV_SCHEMAS["documents.csv"]


@pytest.fixture
def full_companies_csv(tmp_path: Path, municipios_csv: Path) -> Path:
    """Generates a real companies.csv with 15 rows for downstream tests."""
    out = tmp_path / "companies.csv"
    synthesize_companies_csv(out, municipios_csv, rows=15, seed=42,
                             gamma=2.4, beta=1.8, mu=0.3)
    return out


@pytest.fixture
def full_supplies_csv(tmp_path: Path, full_companies_csv: Path) -> Path:
    """Generates a real rel_supplies.csv based on the companies fixture."""
    out = tmp_path / "rel_supplies.csv"
    synthesize_rel_supplies_csv(out, full_companies_csv, avg_out_degree=2,
                                mu=0.3, seed=42)
    return out


# ── basic creation ────────────────────────────────────────────────────────────

def test_synthesize_documents_creates_file(
    tmp_path: Path, full_companies_csv: Path, full_supplies_csv: Path
):
    out = tmp_path / "documents.csv"
    synthesize_documents_csv(out, full_companies_csv, full_supplies_csv,
                             seed=42, avg_out_degree=2)
    assert out.exists()


def test_synthesize_documents_header(
    tmp_path: Path, full_companies_csv: Path, full_supplies_csv: Path
):
    out = tmp_path / "documents.csv"
    synthesize_documents_csv(out, full_companies_csv, full_supplies_csv,
                             seed=42, avg_out_degree=2)
    with out.open(encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert header == DOCS_HEADER


def test_synthesize_documents_has_rows(
    tmp_path: Path, full_companies_csv: Path, full_supplies_csv: Path
):
    out = tmp_path / "documents.csv"
    synthesize_documents_csv(out, full_companies_csv, full_supplies_csv,
                             seed=42, avg_out_degree=2)
    with out.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) > 0


# ── triplet structure ─────────────────────────────────────────────────────────

def test_synthesize_documents_triplet_structure(
    tmp_path: Path, full_companies_csv: Path, full_supplies_csv: Path
):
    """Rows come in triplets: ORDER, DESADV (shipment notice), INVOICE."""
    out = tmp_path / "documents.csv"
    synthesize_documents_csv(out, full_companies_csv, full_supplies_csv,
                             seed=42, avg_out_degree=2)
    with out.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) % 3 == 0, "Total rows must be divisible by 3 (ORDER+DESADV+INVOICE triplets)"


def test_synthesize_documents_reference_chain(
    tmp_path: Path, full_companies_csv: Path, full_supplies_csv: Path
):
    """DESADV.reference_id → ORDER doc_id; INVOICE.reference_id → DESADV doc_id."""
    out = tmp_path / "documents.csv"
    synthesize_documents_csv(out, full_companies_csv, full_supplies_csv,
                             seed=42, avg_out_degree=2)
    with out.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    for i in range(0, len(rows), 3):
        order, desadv, invoice = rows[i], rows[i + 1], rows[i + 2]
        assert order["doc_type:string"] == "ORDER"
        assert desadv["doc_type:string"] == "DESADV"
        assert invoice["doc_type:string"] == "INVOICE"
        assert desadv["reference_id:string"] == order["document_id:ID(Document)"]
        assert invoice["reference_id:string"] == desadv["document_id:ID(Document)"]


# ── validation ────────────────────────────────────────────────────────────────

def test_synthesize_documents_avg_out_degree_zero_raises(
    tmp_path: Path, full_companies_csv: Path, full_supplies_csv: Path
):
    with pytest.raises(ValueError, match="avg_out_degree"):
        synthesize_documents_csv(tmp_path / "out.csv", full_companies_csv,
                                 full_supplies_csv, seed=42, avg_out_degree=0)


def test_synthesize_documents_empty_supplies_raises(
    tmp_path: Path, full_companies_csv: Path
):
    empty_supplies = tmp_path / "empty_supplies.csv"
    empty_supplies.write_text(
        ":START_ID(Company),:END_ID(Company),since_date:date,lead_time_days:int,"
        "reliability_score:float,agreed_volume_baseline:float,"
        "is_exclusive_supplier:boolean,payment_terms_agreed:int,contract_type:string,:TYPE\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="rel_supplies"):
        synthesize_documents_csv(tmp_path / "out.csv", full_companies_csv,
                                 empty_supplies, seed=42, avg_out_degree=2)


# ── determinism ───────────────────────────────────────────────────────────────

def test_synthesize_documents_deterministic(
    tmp_path: Path, full_companies_csv: Path, full_supplies_csv: Path
):
    out1 = tmp_path / "docs_a.csv"
    out2 = tmp_path / "docs_b.csv"
    synthesize_documents_csv(out1, full_companies_csv, full_supplies_csv,
                             seed=7, avg_out_degree=2)
    synthesize_documents_csv(out2, full_companies_csv, full_supplies_csv,
                             seed=7, avg_out_degree=2)
    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")

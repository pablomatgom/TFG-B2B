"""Integration tests for backend/etl/generation/supplies_synthesizer.py."""
import csv
from pathlib import Path

import pytest

from backend.etl.generation.supplies_synthesizer import (
    load_companies,
    synthesize_rel_supplies_csv,
)
from backend.etl.generation.companies_synthesizer import synthesize_companies_csv
from backend.etl.generation.csv_templates import CSV_SCHEMAS

pytestmark = pytest.mark.integration

SUPPLIES_HEADER = CSV_SCHEMAS["rel_supplies.csv"]


@pytest.fixture
def generated_companies_csv(tmp_path: Path, municipios_csv: Path) -> Path:
    """Synthesize a 20-row companies.csv with enough structure for community detection."""
    out = tmp_path / "companies.csv"
    synthesize_companies_csv(out, municipios_csv, rows=20, seed=42,
                             gamma=2.4, beta=1.8, mu=0.3)
    return out


# ── load_companies ────────────────────────────────────────────────────────────

def test_load_companies_valid(generated_companies_csv: Path):
    companies = load_companies(generated_companies_csv)
    assert len(companies) == 20


def test_load_companies_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_companies(tmp_path / "nonexistent.csv")


def test_load_companies_empty_raises(tmp_path: Path):
    """CSV with only the header → ValueError (no valid records)."""
    p = tmp_path / "companies.csv"
    p.write_text(
        "company_id:ID(Company),legal_name:string,tax_id:string,edi_endpoint:string,"
        "node_role:string,country:string,region:string,city:string,"
        "latitude:float,longitude:float,industry_code:string,size_band:string,"
        "baseline_revenue:float,created_at:datetime,is_active:boolean\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_companies(p)


def test_load_companies_invalid_role_defaults_to_hybrid(tmp_path: Path):
    """Unknown node_role is silently upgraded to HYBRID."""
    p = tmp_path / "companies.csv"
    p.write_text(
        "company_id:ID(Company),legal_name:string,tax_id:string,edi_endpoint:string,"
        "node_role:string,country:string,region:string,city:string,"
        "latitude:float,longitude:float,industry_code:string,size_band:string,"
        "baseline_revenue:float,created_at:datetime,is_active:boolean\n"
        "C-001,Test,ESA001,edi://x,UNKNOWN_ROLE,Spain,Madrid,Madrid,"
        "40.0,-3.0,C10,pyme,500000.0,2020-01-01T00:00:00,true\n"
        "C-002,Test2,ESB002,edi://y,BUYER,Spain,Madrid,Madrid,"
        "40.0,-3.0,G46,mid,2000000.0,2019-06-15T00:00:00,true\n",
        encoding="utf-8",
    )
    companies = load_companies(p)
    assert any(c.node_role == "HYBRID" for c in companies)


# ── synthesize_rel_supplies_csv ───────────────────────────────────────────────

def test_synthesize_supplies_creates_file(tmp_path: Path, generated_companies_csv: Path):
    out = tmp_path / "rel_supplies.csv"
    synthesize_rel_supplies_csv(out, generated_companies_csv, avg_out_degree=1, mu=0.3, seed=42)
    assert out.exists()


def test_synthesize_supplies_has_data_rows(tmp_path: Path, generated_companies_csv: Path):
    out = tmp_path / "rel_supplies.csv"
    synthesize_rel_supplies_csv(out, generated_companies_csv, avg_out_degree=1, mu=0.3, seed=42)
    with out.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) > 0


def test_synthesize_supplies_header(tmp_path: Path, generated_companies_csv: Path):
    out = tmp_path / "rel_supplies.csv"
    synthesize_rel_supplies_csv(out, generated_companies_csv, avg_out_degree=1, mu=0.3, seed=42)
    with out.open(encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert header == SUPPLIES_HEADER


def test_synthesize_supplies_deterministic(tmp_path: Path, generated_companies_csv: Path):
    """Same seed → identical output."""
    out1 = tmp_path / "a.csv"
    out2 = tmp_path / "b.csv"
    synthesize_rel_supplies_csv(out1, generated_companies_csv, avg_out_degree=1, mu=0.3, seed=7)
    synthesize_rel_supplies_csv(out2, generated_companies_csv, avg_out_degree=1, mu=0.3, seed=7)
    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")


def test_synthesize_supplies_avg_out_degree_zero_raises(tmp_path: Path, generated_companies_csv: Path):
    with pytest.raises(ValueError, match="avg_out_degree"):
        synthesize_rel_supplies_csv(tmp_path / "out.csv", generated_companies_csv,
                                    avg_out_degree=0, mu=0.3, seed=42)


def test_synthesize_supplies_avg_out_degree_negative_raises(tmp_path: Path, generated_companies_csv: Path):
    with pytest.raises(ValueError):
        synthesize_rel_supplies_csv(tmp_path / "out.csv", generated_companies_csv,
                                    avg_out_degree=-1, mu=0.3, seed=42)


def test_synthesize_supplies_mu_equals_one_raises(tmp_path: Path, generated_companies_csv: Path):
    """mu=1.0 is INVALID for supplies (check is 0<=mu<1, exclusive upper bound).
    This is the asymmetry: companies synthesizer accepts mu=1.0."""
    with pytest.raises(ValueError, match="mu"):
        synthesize_rel_supplies_csv(tmp_path / "out.csv", generated_companies_csv,
                                    avg_out_degree=1, mu=1.0, seed=42)


def test_synthesize_supplies_mu_zero_is_valid(tmp_path: Path, generated_companies_csv: Path):
    """mu=0.0 is valid (all edges intra-community)."""
    out = tmp_path / "out.csv"
    synthesize_rel_supplies_csv(out, generated_companies_csv, avg_out_degree=1, mu=0.0, seed=42)
    assert out.exists()


def test_synthesize_supplies_no_self_loops(tmp_path: Path, generated_companies_csv: Path):
    """No edge should have the same supplier and buyer."""
    out = tmp_path / "out.csv"
    synthesize_rel_supplies_csv(out, generated_companies_csv, avg_out_degree=2, mu=0.3, seed=42)
    with out.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            supplier = row.get(":START_ID(Company)") or row.get("supplier_company_id", "")
            buyer = row.get(":END_ID(Company)") or row.get("buyer_company_id", "")
            assert supplier != buyer, f"Self-loop found: {supplier}"

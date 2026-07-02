"""Integration tests for backend/etl/generation/companies_synthesizer.py."""
import csv
from pathlib import Path

import pytest

from backend.etl.generation.companies_synthesizer import (
    load_municipalities,
    synthesize_companies_csv,
)
from backend.etl.generation.csv_templates import CSV_SCHEMAS

pytestmark = pytest.mark.integration

COMPANY_HEADER = CSV_SCHEMAS["companies.csv"]


# ── load_municipalities ───────────────────────────────────────────────────────

def test_load_municipalities_valid_csv(municipios_csv: Path):
    municipalities, weights = load_municipalities(municipios_csv)
    assert len(municipalities) == 3
    assert len(weights) == 3
    assert all(w > 0 for w in weights)


def test_load_municipalities_returns_names(municipios_csv: Path):
    municipalities, _ = load_municipalities(municipios_csv)
    names = [m.municipality for m in municipalities]
    assert "Madrid" in names


def test_load_municipalities_empty_csv_raises(tmp_path: Path):
    """Only header row → no valid municipalities → ValueError."""
    p = tmp_path / "empty.csv"
    p.write_text("Provincia;Población;Latitud;Longitud;Habitantes\n", encoding="utf-8-sig")
    with pytest.raises(ValueError):
        load_municipalities(p)


def test_load_municipalities_skips_missing_provincia(tmp_path: Path):
    """Rows without Provincia are silently skipped."""
    p = tmp_path / "muni.csv"
    p.write_text(
        "Provincia;Población;Latitud;Longitud;Habitantes\n"
        ";NoProvince;40.0;-3.0;1000\n"
        "Madrid;Madrid;40.4168;-3.7038;3300000\n",
        encoding="utf-8-sig",
    )
    municipalities, _ = load_municipalities(p)
    assert len(municipalities) == 1
    assert municipalities[0].province == "Madrid"


def test_load_municipalities_defaults_missing_habitantes(tmp_path: Path):
    """Rows with missing Habitantes default to 50_000."""
    p = tmp_path / "muni.csv"
    p.write_text(
        "Provincia;Población;Latitud;Longitud;Habitantes\n"
        "Madrid;Madrid;40.4168;-3.7038;\n",
        encoding="utf-8-sig",
    )
    municipalities, weights = load_municipalities(p)
    assert municipalities[0].population == 50_000
    assert weights[0] == 50_000


# ── synthesize_companies_csv ──────────────────────────────────────────────────

def test_synthesize_companies_creates_file(tmp_path: Path, municipios_csv: Path):
    out = tmp_path / "companies.csv"
    synthesize_companies_csv(out, municipios_csv, rows=10, seed=42,
                             gamma=2.4, beta=1.8, mu=0.30)
    assert out.exists()


def test_synthesize_companies_row_count(tmp_path: Path, municipios_csv: Path):
    out = tmp_path / "companies.csv"
    synthesize_companies_csv(out, municipios_csv, rows=15, seed=42,
                             gamma=2.4, beta=1.8, mu=0.30)
    with out.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 15


def test_synthesize_companies_header_matches_schema(tmp_path: Path, municipios_csv: Path):
    out = tmp_path / "companies.csv"
    synthesize_companies_csv(out, municipios_csv, rows=5, seed=1,
                             gamma=2.4, beta=1.8, mu=0.30)
    with out.open(encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert header == COMPANY_HEADER


def test_synthesize_companies_deterministic(tmp_path: Path, municipios_csv: Path):
    """Same seed produces the same company IDs, roles and regions (structural determinism).

    Note: full byte equality is not guaranteed because the module-level Faker singleton
    accumulates state across tests in the same process. We verify the structurally
    deterministic fields instead (company_id, node_role, region are LFR-derived, not Faker).
    """
    out1 = tmp_path / "a.csv"
    out2 = tmp_path / "b.csv"
    synthesize_companies_csv(out1, municipios_csv, rows=10, seed=7, gamma=2.4, beta=1.8, mu=0.3)
    synthesize_companies_csv(out2, municipios_csv, rows=10, seed=7, gamma=2.4, beta=1.8, mu=0.3)

    def read_key_fields(path):
        with path.open(encoding="utf-8") as fh:
            return [(r["company_id:ID(Company)"], r["node_role:string"], r["region:string"])
                    for r in csv.DictReader(fh)]

    assert read_key_fields(out1) == read_key_fields(out2)


def test_synthesize_companies_rows_zero_raises(tmp_path: Path, municipios_csv: Path):
    with pytest.raises(ValueError, match="filas"):
        synthesize_companies_csv(tmp_path / "out.csv", municipios_csv,
                                 rows=0, seed=42, gamma=2.4, beta=1.8, mu=0.3)


def test_synthesize_companies_rows_negative_raises(tmp_path: Path, municipios_csv: Path):
    with pytest.raises(ValueError):
        synthesize_companies_csv(tmp_path / "out.csv", municipios_csv,
                                 rows=-1, seed=42, gamma=2.4, beta=1.8, mu=0.3)


def test_synthesize_companies_gamma_le_one_raises(tmp_path: Path, municipios_csv: Path):
    with pytest.raises(ValueError, match="gamma"):
        synthesize_companies_csv(tmp_path / "out.csv", municipios_csv,
                                 rows=5, seed=42, gamma=1.0, beta=1.8, mu=0.3)


def test_synthesize_companies_beta_le_one_raises(tmp_path: Path, municipios_csv: Path):
    with pytest.raises(ValueError, match="gamma"):  # same ValueError message covers both
        synthesize_companies_csv(tmp_path / "out.csv", municipios_csv,
                                 rows=5, seed=42, gamma=2.4, beta=0.5, mu=0.3)


def test_synthesize_companies_mu_equals_one_is_valid(tmp_path: Path, municipios_csv: Path):
    """mu=1.0 is VALID for companies (check is 0<=mu<=1, inclusive).
    This is an asymmetry: supplies synthesizer rejects mu=1.0."""
    out = tmp_path / "out.csv"
    synthesize_companies_csv(out, municipios_csv, rows=5, seed=42,
                             gamma=2.4, beta=1.8, mu=1.0)
    assert out.exists()


def test_synthesize_companies_mu_negative_raises(tmp_path: Path, municipios_csv: Path):
    with pytest.raises(ValueError, match="mu"):
        synthesize_companies_csv(tmp_path / "out.csv", municipios_csv,
                                 rows=5, seed=42, gamma=2.4, beta=1.8, mu=-0.1)


def test_synthesize_companies_company_ids_unique(tmp_path: Path, municipios_csv: Path):
    out = tmp_path / "companies.csv"
    synthesize_companies_csv(out, municipios_csv, rows=20, seed=42,
                             gamma=2.4, beta=1.8, mu=0.3)
    with out.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    ids = [r["company_id:ID(Company)"] for r in rows]
    assert len(ids) == len(set(ids)), "company_id must be unique"


def test_synthesize_companies_tax_ids_unique(tmp_path: Path, municipios_csv: Path):
    out = tmp_path / "companies.csv"
    synthesize_companies_csv(out, municipios_csv, rows=20, seed=42,
                             gamma=2.4, beta=1.8, mu=0.3)
    with out.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    tax_ids = [r["tax_id:string"] for r in rows]
    assert len(tax_ids) == len(set(tax_ids)), "tax_id must be unique"


def test_synthesize_companies_node_roles_valid(tmp_path: Path, municipios_csv: Path):
    out = tmp_path / "companies.csv"
    synthesize_companies_csv(out, municipios_csv, rows=20, seed=42,
                             gamma=2.4, beta=1.8, mu=0.3)
    valid_roles = {"SUPPLIER", "BUYER", "HYBRID"}
    with out.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            assert row["node_role:string"] in valid_roles

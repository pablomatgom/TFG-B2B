"""Unit tests for Neo4jBulkLoader._iter_csv_batches."""
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _patch_driver():
    with patch("backend.etl.loader.GraphDatabase.driver", return_value=MagicMock()):
        yield


from backend.etl.loader import Neo4jBulkLoader


def _make_loader(batch_size: int = 10) -> Neo4jBulkLoader:
    with patch("backend.etl.loader.GraphDatabase.driver", return_value=MagicMock()):
        return Neo4jBulkLoader("bolt://x", "u", "p", "neo4j", batch_size)


def _write_csv(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_iter_batches_empty_string_becomes_none(tmp_path: Path):
    """Empty CSV values are normalized to None."""
    csv_path = _write_csv(
        tmp_path / "test.csv",
        "name:string,value:string\nAlice,\nBob,hello\n",
    )
    loader = _make_loader()
    batches = list(loader._iter_csv_batches(csv_path))
    assert len(batches) == 1
    rows = batches[0]
    assert rows[0]["value"] is None  # empty → None
    assert rows[1]["value"] == "hello"


def test_iter_batches_whitespace_becomes_none(tmp_path: Path):
    """Whitespace-only values are stripped to empty then set to None."""
    csv_path = _write_csv(
        tmp_path / "test.csv",
        "col:string\n   \nreal\n",
    )
    loader = _make_loader()
    batches = list(loader._iter_csv_batches(csv_path))
    rows = batches[0]
    assert rows[0]["col"] is None
    assert rows[1]["col"] == "real"


def test_iter_batches_respects_batch_size(tmp_path: Path):
    """5 rows with batch_size=2 → 3 batches (sizes 2, 2, 1)."""
    lines = ["a:string"] + [f"row{i}" for i in range(5)]
    csv_path = _write_csv(tmp_path / "test.csv", "\n".join(lines) + "\n")
    loader = _make_loader(batch_size=2)
    batches = list(loader._iter_csv_batches(csv_path))
    assert len(batches) == 3
    assert len(batches[0]) == 2
    assert len(batches[1]) == 2
    assert len(batches[2]) == 1


def test_iter_batches_headers_cleaned(tmp_path: Path):
    """Neo4j type-suffix headers are cleaned in the result dicts."""
    csv_path = _write_csv(
        tmp_path / "test.csv",
        "company_id:ID(Company),legal_name:string\nC-001,ACME\n",
    )
    loader = _make_loader()
    batches = list(loader._iter_csv_batches(csv_path))
    row = batches[0][0]
    assert "company_id" in row
    assert "legal_name" in row
    assert row["company_id"] == "C-001"


def test_iter_batches_single_row(tmp_path: Path):
    csv_path = _write_csv(tmp_path / "test.csv", "col:string\nvalue\n")
    loader = _make_loader()
    batches = list(loader._iter_csv_batches(csv_path))
    assert len(batches) == 1
    assert len(batches[0]) == 1


def test_iter_batches_empty_file(tmp_path: Path):
    """CSV with only headers → no batches yielded."""
    csv_path = _write_csv(tmp_path / "test.csv", "col:string\n")
    loader = _make_loader()
    batches = list(loader._iter_csv_batches(csv_path))
    assert batches == []


def test_loader_batch_size_clamped_to_one():
    """batch_size=0 is clamped to 1."""
    loader = _make_loader(batch_size=0)
    assert loader.batch_size == 1


def test_loader_batch_size_negative_clamped():
    """batch_size=-5 is clamped to 1."""
    loader = _make_loader(batch_size=-5)
    assert loader.batch_size == 1

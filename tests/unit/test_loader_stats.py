"""Unit tests for LoadStats in backend/etl/loader.py."""
import dataclasses
import pytest
from backend.etl.loader import LoadStats

pytestmark = pytest.mark.unit


def test_rows_per_second_normal():
    stats = LoadStats(dataset="a.csv", file_path="/tmp/a.csv",
                      rows=100, batches=1, elapsed_seconds=2.0)
    assert stats.rows_per_second == pytest.approx(50.0)


def test_rows_per_second_zero_elapsed():
    """elapsed_seconds=0 → returns float(rows) as upper bound."""
    stats = LoadStats(dataset="a.csv", file_path="/tmp/a.csv",
                      rows=100, batches=1, elapsed_seconds=0)
    assert stats.rows_per_second == 100.0


def test_rows_per_second_negative_elapsed():
    """elapsed_seconds<0 → same guard, returns float(rows)."""
    stats = LoadStats(dataset="a.csv", file_path="/tmp/a.csv",
                      rows=50, batches=1, elapsed_seconds=-1.0)
    assert stats.rows_per_second == 50.0


def test_rows_per_second_zero_rows():
    stats = LoadStats(dataset="a.csv", file_path="/tmp/a.csv",
                      rows=0, batches=0, elapsed_seconds=1.0)
    assert stats.rows_per_second == pytest.approx(0.0)


def test_loadstats_is_frozen():
    """LoadStats is a frozen dataclass — mutation must raise."""
    stats = LoadStats(dataset="a.csv", file_path="/f", rows=10, batches=1, elapsed_seconds=1.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        stats.rows = 999  # type: ignore[misc]

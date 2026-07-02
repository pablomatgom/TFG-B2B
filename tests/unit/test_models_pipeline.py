"""Unit tests for backend/api/models/pipeline.py — PipelineRequest."""
import pytest
from backend.api.models.pipeline import PipelineRequest

pytestmark = pytest.mark.unit


def test_pipeline_request_defaults():
    req = PipelineRequest()
    assert req.rows == 200
    assert req.avg_degree_supplies == 7
    assert req.avg_degree_documents == 5
    assert req.gamma == pytest.approx(2.4)
    assert req.beta == pytest.approx(1.8)
    assert req.mu == pytest.approx(0.30)
    assert req.avg_degree_products == 25
    assert req.batch_size == 10000
    assert req.clear_db is True
    assert req.use_random_seed is True
    assert req.seed_value == 42


def test_pipeline_request_custom_values():
    req = PipelineRequest(rows=100, gamma=2.2, mu=0.15, seed_value=7)
    assert req.rows == 100
    assert req.gamma == pytest.approx(2.2)
    assert req.seed_value == 7


# ── Validation gap documentation ──────────────────────────────────────────────
# These tests confirm that Pydantic does NOT currently enforce the documented
# constraints (gamma>1, beta>1, 0<=mu<1). They serve as regression markers:
# if a validator is added later, these tests will fail and should be updated.

def test_pipeline_request_gamma_no_validator():
    """gamma=0.5 should be rejected (>1 required) but Pydantic allows it — gap."""
    req = PipelineRequest(gamma=0.5)
    assert req.gamma == pytest.approx(0.5)


def test_pipeline_request_beta_no_validator():
    """beta=0.9 should be rejected (>1 required) but Pydantic allows it — gap."""
    req = PipelineRequest(beta=0.9)
    assert req.beta == pytest.approx(0.9)


def test_pipeline_request_mu_out_of_range_no_validator():
    """mu=1.5 should be rejected (0<=mu<1) but Pydantic allows it — gap."""
    req = PipelineRequest(mu=1.5)
    assert req.mu == pytest.approx(1.5)


def test_pipeline_request_rows_zero_no_validator():
    """rows=0 should be rejected but Pydantic allows it — gap."""
    req = PipelineRequest(rows=0)
    assert req.rows == 0


def test_pipeline_request_seed_value_none():
    req = PipelineRequest(use_random_seed=True, seed_value=None)
    assert req.seed_value is None

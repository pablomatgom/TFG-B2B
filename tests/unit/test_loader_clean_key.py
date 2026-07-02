"""Unit tests for Neo4jBulkLoader._clean_key (static method)."""
import pytest
from unittest.mock import MagicMock, patch

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _patch_driver():
    """Prevent real Neo4j connection when importing the loader module."""
    with patch("backend.etl.loader.GraphDatabase.driver", return_value=MagicMock()):
        yield


from backend.etl.loader import Neo4jBulkLoader


@pytest.mark.parametrize("key,expected", [
    (":START_ID(Company)",  "supplier_company_id"),
    (":END_ID(Company)",    "buyer_company_id"),
    (":START_ID(Document)", "document_id"),
    (":END_ID(Product)",    "product_id"),
    (":TYPE",               "type"),
    # Regular columns with Neo4j type suffixes
    ("legal_name:string",          "legal_name"),
    ("company_id:ID(Company)",     "company_id"),
    ("latitude:float",             "latitude"),
    ("is_active:boolean",          "is_active"),
    ("version_number:int",         "version_number"),
    # Plain key with no suffix
    ("plain_key",   "plain_key"),
    # Empty string
    ("",            ""),
])
def test_clean_key(key: str, expected: str):
    assert Neo4jBulkLoader._clean_key(key) == expected

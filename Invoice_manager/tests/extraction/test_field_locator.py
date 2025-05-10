"""
Test field locator functionality.
"""

import json
import os
from pathlib import Path

import pytest

from src.extraction.field_locator import FieldLocator
from src.utils.cfg import ConfigLoader


@pytest.fixture
def sample_invoice_text():
    """Load sample invoice text from fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_invoice_1.txt"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def sample_invoice_truth():
    """Load sample invoice ground truth from fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "sample_invoice_1_truth.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def field_locator():
    """Create a field locator instance."""
    config = ConfigLoader()._get_default_config()
    return FieldLocator(config)


def test_extract_fields(field_locator, sample_invoice_text, sample_invoice_truth):
    """Test that fields are correctly extracted from invoice text."""
    # Extract fields
    extracted_fields = field_locator.extract_fields(sample_invoice_text)
    
    # Remove metadata for comparison
    if "metadata" in extracted_fields:
        del extracted_fields["metadata"]
    
    # Check required fields
    assert "invoice_number" in extracted_fields
    assert extracted_fields["invoice_number"] == sample_invoice_truth["invoice_number"]
    
    assert "issue_date" in extracted_fields
    assert extracted_fields["issue_date"] == sample_invoice_truth["issue_date"]
    
    assert "total_eur" in extracted_fields
    # Allow for slight format variations but ensure the amount is correct
    assert extracted_fields["total_eur"].replace(" ", "") == sample_invoice_truth["total_eur"].replace(" ", "")
    
    assert "vat_rate" in extracted_fields
    assert extracted_fields["vat_rate"] == sample_invoice_truth["vat_rate"]
    
    assert "vendor_name" in extracted_fields
    assert extracted_fields["vendor_name"] == sample_invoice_truth["vendor_name"]
    
    assert "vendor_tax_id" in extracted_fields
    assert extracted_fields["vendor_tax_id"] == sample_invoice_truth["vendor_tax_id"]


def test_normalize_text(field_locator):
    """Test text normalization functionality."""
    # Test with extra whitespace and different line endings
    messy_text = "FACTURA  \r\nNúmero:  F2023-1234\r\nFecha:  15/06/2023"
    normalized = field_locator._normalize_text(messy_text)
    
    # Check that extra whitespace is removed and line endings are normalized
    assert "FACTURA" in normalized
    assert "Número: F2023-1234" in normalized
    assert "Fecha: 15/06/2023" in normalized


def test_extract_with_patterns(field_locator):
    """Test pattern-based extraction."""
    text = "Factura Nº: ABC123"
    patterns = [
        r"(?:factura|fact|fra)(?:\s+)(?:n[º|°|o]?\.?:?\s*)([A-Za-z0-9\-\/]+)",
        r"(?:invoice number|invoice no):?\s*([A-Za-z0-9\-\/]+)"
    ]
    
    result = field_locator._extract_with_patterns(text, patterns)
    assert result == "ABC123"
    
    # Test with no match
    text = "Document ID: ABC123"
    result = field_locator._extract_with_patterns(text, patterns)
    assert result is None


def test_extract_line_items(field_locator, sample_invoice_text):
    """Test line item extraction."""
    # Extract line items
    line_items = field_locator._extract_line_items(sample_invoice_text)
    
    # Check that line items were extracted
    assert line_items is not None
    assert len(line_items) > 0
    
    # Check structure of first line item
    first_item = line_items[0]
    assert "description" in first_item
    assert "qty" in first_item
    assert "unit_price" in first_item
    assert "line_total" in first_item 
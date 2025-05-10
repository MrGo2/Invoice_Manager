# Testing Strategy

This document outlines the testing strategy for the Invoice Processor system, including unit tests, integration tests, and sample datasets for validation.

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Unit Tests](#unit-tests)
3. [Integration Tests](#integration-tests)
4. [End-to-End Tests](#end-to-end-tests)
5. [Sample Datasets](#sample-datasets)
6. [Test Coverage](#test-coverage)
7. [CI/CD Pipeline](#cicd-pipeline)

## Testing Overview

The Invoice Processor employs a comprehensive testing strategy to ensure reliability and accuracy:

- **Unit Tests**: Validate individual components in isolation
- **Integration Tests**: Verify component interactions
- **End-to-End Tests**: Simulate complete invoice processing
- **Performance Tests**: Measure and optimize throughput
- **Validation Tests**: Compare extraction results against ground truth

## Unit Tests

Unit tests validate the functionality of individual components in isolation using mocked dependencies.

### Test Structure

Unit tests are located in the `tests/unit/` directory, mirroring the structure of the `src/` directory:

```
tests/unit/
├── preprocessing/
│   └── test_image_processor.py
├── ocr/
│   ├── test_mistral_wrapper.py
│   ├── test_tesseract_fallback.py
│   └── test_confidence_merger.py
├── extraction/
│   ├── test_field_locator.py
│   └── test_openai_refiner.py
├── validation/
│   └── test_schema_validator.py
├── export/
│   └── test_writers.py
└── utils/
    ├── test_cfg.py
    └── test_logger.py
```

### Running Unit Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run tests for a specific module
pytest tests/unit/ocr/

# Run tests with verbose output
pytest -v tests/unit/
```

### Example Unit Test

```python
# tests/unit/ocr/test_mistral_wrapper.py
import pytest
from unittest.mock import patch, MagicMock
from src.ocr.mistral_wrapper import MistralOCR

def test_run_ocr_with_valid_image():
    # Arrange
    config = {
        "language": "spa",
        "ocr": {
            "mistral": {
                "model": "test-model",
                "batch_size": 8,
                "greedy_decoding": True
            }
        }
    }
    
    mock_ocr = MagicMock()
    mock_ocr.process.return_value = [
        MagicMock(text="Invoice", conf=0.98, box=(10, 10, 100, 30), page=0),
        MagicMock(text="Total", conf=0.95, box=(10, 50, 100, 70), page=0)
    ]
    
    # Act
    with patch("mistral_ocr.OCR", return_value=mock_ocr):
        ocr = MistralOCR(config)
        results = ocr.run_ocr("test_image.png")
    
    # Assert
    assert len(results) == 2
    assert results[0]["text"] == "Invoice"
    assert results[0]["conf"] == 0.98
    assert results[1]["text"] == "Total"
```

## Integration Tests

Integration tests verify that components work correctly together, with minimal mocking.

### Test Structure

Integration tests are located in the `tests/integration/` directory:

```
tests/integration/
├── test_ocr_pipeline.py
├── test_extraction_pipeline.py
└── test_validation_export.py
```

### Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run a specific integration test
pytest tests/integration/test_ocr_pipeline.py
```

### Example Integration Test

```python
# tests/integration/test_ocr_pipeline.py
import os
import pytest
from pathlib import Path
from src.preprocessing.image_processor import ImageProcessor
from src.ocr.mistral_wrapper import MistralOCR
from src.ocr.confidence_merger import OCRMerger
from src.utils.cfg import ConfigLoader

@pytest.mark.integration
def test_ocr_pipeline_with_sample_invoice():
    # Skip if no API key is available
    if "MISTRAL_API_KEY" not in os.environ:
        pytest.skip("Mistral API key not available")
    
    # Arrange
    config = ConfigLoader().config
    image_processor = ImageProcessor(config)
    ocr = MistralOCR(config)
    
    # Get test image path
    test_invoice = Path("tests/fixtures/sample_invoice.png")
    
    # Act
    processed_images = image_processor.process(test_invoice)
    ocr_results = ocr.run_ocr(processed_images[0])
    
    # Assert
    assert len(ocr_results) > 0
    assert any("factura" in word["text"].lower() for word in ocr_results)
```

## End-to-End Tests

End-to-end tests validate the complete invoice processing pipeline.

### Test Structure

End-to-end tests are located in the `tests/e2e/` directory:

```
tests/e2e/
├── test_invoice_processor.py
└── test_cli.py
```

### Running End-to-End Tests

```bash
# Run all end-to-end tests
pytest tests/e2e/

# Run with slower tests marked as such
pytest tests/e2e/ -m "not slow"
```

### Example End-to-End Test

```python
# tests/e2e/test_invoice_processor.py
import json
import pytest
from pathlib import Path
from src.main import InvoiceProcessor

@pytest.mark.e2e
def test_process_sample_invoice():
    # Arrange
    processor = InvoiceProcessor()
    test_invoice = Path("tests/fixtures/sample_invoice.pdf")
    
    # Act
    result = processor.process(test_invoice)
    
    # Assert
    assert "invoice_number" in result
    assert "issue_date" in result
    assert "total_eur" in result
    assert "vendor_name" in result
    
    # Compare with ground truth
    truth_file = Path("tests/fixtures/sample_invoice_truth.json")
    with open(truth_file, 'r') as f:
        truth = json.load(f)
    
    assert result["invoice_number"] == truth["invoice_number"]
    assert result["total_eur"] == truth["total_eur"]
```

## Sample Datasets

The test suite includes sample datasets for comprehensive testing:

### Test Fixtures

Test fixtures are located in the `tests/fixtures/` directory:

```
tests/fixtures/
├── images/
│   ├── sample_invoice_1.png
│   ├── sample_invoice_2.jpg
│   └── sample_invoice_3.tiff
├── pdfs/
│   ├── sample_invoice_1.pdf
│   ├── sample_invoice_2.pdf
│   └── sample_invoice_multi_page.pdf
└── truth/
    ├── sample_invoice_1.json
    ├── sample_invoice_2.json
    └── sample_invoice_3.json
```

### Fixture Types

- **Sample Invoices**: Representative Spanish invoices in various formats
- **Ground Truth**: Expected extraction results for validation
- **Edge Cases**: Invoices with challenging layouts or content

### Creating Test Fixtures

When adding new test fixtures:

1. Place the sample invoice in the appropriate directory
2. Create a corresponding ground truth JSON file
3. Document the fixture's characteristics in a README

## Test Coverage

The project aims for >90% code coverage across all modules.

### Coverage Report

Generate a coverage report using pytest-cov:

```bash
# Generate coverage report
pytest --cov=src

# Generate HTML coverage report
pytest --cov=src --cov-report=html
```

### Coverage Thresholds

- **Critical Modules**: 95% coverage (field extraction, validation)
- **Core Modules**: 90% coverage (OCR, preprocessing)
- **Utility Modules**: 85% coverage

## CI/CD Pipeline

Automated testing is integrated into the CI/CD pipeline using GitHub Actions.

### Pipeline Stages

1. **Lint**: Run flake8 and black to ensure code quality
2. **Unit Tests**: Run all unit tests
3. **Integration Tests**: Run integration tests with API keys
4. **Coverage**: Check test coverage against thresholds
5. **Build**: Create distribution package

### Configuration

The CI pipeline is configured in `.github/workflows/ci.yml` and can be customized for specific needs.

```yaml
# Example of test section in CI configuration
- name: Run tests and coverage
  run: |
    pytest --cov=src --cov-report=xml
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    MISTRAL_API_KEY: ${{ secrets.MISTRAL_API_KEY }}
``` 
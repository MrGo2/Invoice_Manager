# Module Reference

This document provides a detailed reference for each module in the Invoice Processor codebase, including their interfaces, dependencies, and examples.

## Table of Contents

1. [Preprocessing](#preprocessing)
2. [OCR](#ocr)
3. [Extraction](#extraction)
4. [Validation](#validation)
5. [Export](#export)
6. [Utils](#utils)
7. [Main Module](#main-module)

## Preprocessing

The preprocessing module prepares invoice images for OCR processing.

### ImageProcessor (`src/preprocessing/image_processor.py`)

**Responsibility**: Converts input files to optimized images for OCR processing.

**Key Methods**:
- `process(file_path)`: Process a file (PDF/image) and return a list of optimized images
- `_convert_pdf_to_images(pdf_path)`: Convert PDF file to images
- `_preprocess_image(image_path)`: Apply preprocessing to an image
- `_deskew_image(image)`: Correct image skew
- `_enhance_contrast(image)`: Improve image contrast
- `_remove_noise(image)`: Reduce noise in the image

**Dependencies**:
- OpenCV (`cv2`)
- Pillow (`PIL`)
- pdf2image
- numpy

**Example**:
```python
from src.preprocessing.image_processor import ImageProcessor
from src.utils.cfg import ConfigLoader

config = ConfigLoader().config
processor = ImageProcessor(config)
image_paths = processor.process("invoice.pdf")
print(f"Generated {len(image_paths)} preprocessed images")
```

## OCR

The OCR module extracts text from invoice images using multiple engines.

### MistralOCR (`src/ocr/mistral_wrapper.py`)

**Responsibility**: Primary OCR engine specializing in Spanish language text recognition.

**Key Methods**:
- `run_ocr(image_path)`: Run OCR on an image and return results
- `get_text_from_results(results)`: Extract plain text from OCR results

**Dependencies**:
- mistral-ocr

**Example**:
```python
from src.ocr.mistral_wrapper import MistralOCR
from src.utils.cfg import ConfigLoader

config = ConfigLoader().config
ocr = MistralOCR(config)
results = ocr.run_ocr("preprocessed_image.png")
text = ocr.get_text_from_results(results)
```

### TesseractOCR (`src/ocr/tesseract_fallback.py`)

**Responsibility**: Fallback OCR engine using Tesseract.

**Key Methods**:
- `run_ocr(image_path)`: Run OCR on an image and return results
- `get_text_from_results(results)`: Extract plain text from OCR results
- `_check_tesseract_installed()`: Verify Tesseract installation
- `_check_language_pack(lang)`: Check if language pack is installed

**Dependencies**:
- pytesseract
- Pillow

**Example**:
```python
from src.ocr.tesseract_fallback import TesseractOCR
from src.utils.cfg import ConfigLoader

config = ConfigLoader().config
ocr = TesseractOCR(config)
results = ocr.run_ocr("preprocessed_image.png")
```

### OCRMerger (`src/ocr/confidence_merger.py`)

**Responsibility**: Merge results from multiple OCR engines based on confidence scores.

**Key Methods**:
- `merge(primary_results, fallback_results)`: Merge OCR results from different engines
- `_merge_highest_confidence(primary_results, fallback_results)`: Select results with highest confidence
- `_merge_line_by_line(primary_results, fallback_results)`: Merge results line by line
- `_merge_word_by_word(primary_results, fallback_results)`: Merge results word by word

**Dependencies**:
- numpy

**Example**:
```python
from src.ocr.confidence_merger import OCRMerger
from src.utils.cfg import ConfigLoader

config = ConfigLoader().config
merger = OCRMerger(config)
mistral_results = mistral_ocr.run_ocr("image.png")
tesseract_results = tesseract_ocr.run_ocr("image.png")
merged_results = merger.merge(mistral_results, tesseract_results)
```

## Extraction

The extraction module converts OCR text into structured invoice data.

### FieldLocator (`src/extraction/field_locator.py`)

**Responsibility**: Extract invoice fields from OCR text using regex patterns and heuristics.

**Key Methods**:
- `extract_fields(text)`: Extract invoice fields from OCR text
- `_normalize_text(text)`: Normalize OCR text for pattern matching
- `_extract_with_patterns(text, patterns)`: Extract field using regex patterns
- `_extract_line_items(text)`: Extract line items from invoice text

**Dependencies**:
- re (regex)
- datetime

**Example**:
```python
from src.extraction.field_locator import FieldLocator
from src.utils.cfg import ConfigLoader

config = ConfigLoader().config
locator = FieldLocator(config)
fields = locator.extract_fields(ocr_text)
print(f"Extracted fields: {fields.keys()}")
```

### OpenAIRefiner (`src/extraction/openai_refiner.py`)

**Responsibility**: Refine extracted invoice fields using OpenAI's GPT-4o model.

**Key Methods**:
- `refine(ocr_text, initial_fields)`: Refine extracted fields using OpenAI
- `_create_prompt(ocr_text, initial_fields, schema)`: Create prompt for OpenAI
- `_call_openai(messages)`: Call OpenAI API
- `_simplify_schema(schema)`: Simplify JSON schema for use in prompts
- `_get_few_shot_examples()`: Get few-shot examples for the prompt
- `_log_prompt(messages, initial_fields)`: Log prompt for auditing

**Dependencies**:
- openai
- jinja2
- json

**Example**:
```python
from src.extraction.openai_refiner import OpenAIRefiner
from src.utils.cfg import ConfigLoader

config = ConfigLoader().config
refiner = OpenAIRefiner(config)
refined_fields = refiner.refine(ocr_text, initial_fields)
```

## Validation

The validation module ensures extracted data conforms to the expected schema.

### SchemaValidator (`src/validation/schema_validator.py`)

**Responsibility**: Validate extracted invoice data against JSON schema.

**Key Methods**:
- `validate(data)`: Validate invoice data against schema
- `_check_required_fields(data)`: Check that required fields are present
- `_format_fields(data)`: Format fields according to schema patterns
- `_format_date(date_str)`: Format date string
- `_format_currency(currency_str)`: Format currency string
- `_get_default_value(field)`: Get default value for a field

**Dependencies**:
- jsonschema
- json

**Example**:
```python
from src.validation.schema_validator import SchemaValidator
from src.utils.cfg import ConfigLoader

config = ConfigLoader().config
validator = SchemaValidator(config)
validated_data = validator.validate(extracted_data)
```

## Export

The export module handles output of processed invoice data in various formats.

### Writers (`src/export/writers.py`)

**Responsibility**: Export invoice data in different formats.

**Classes**:
- `BaseWriter`: Abstract base class for writers
- `JSONWriter`: Exports data as JSON
- `CSVWriter`: Exports data as CSV
- `WebhookWriter`: Sends data to a webhook

**Key Methods**:
- `write(data, output_path)`: Write invoice data to output

**Dependencies**:
- json
- csv
- requests

**Example**:
```python
from src.export.writers import JSONWriter, CSVWriter
from src.utils.cfg import ConfigLoader

config = ConfigLoader().config
json_writer = JSONWriter()
csv_writer = CSVWriter()

# Export as JSON
json_path = json_writer.write(invoice_data, "invoice_output.json")

# Export as CSV
csv_path = csv_writer.write(invoice_data, "invoice_output.csv")
```

## Utils

Utility modules providing common functionality across the codebase.

### ConfigLoader (`src/utils/cfg.py`)

**Responsibility**: Load and manage configuration settings.

**Key Methods**:
- `__init__(config_path)`: Initialize the configuration loader
- `_load_config()`: Load configuration from YAML file
- `_apply_env_overrides()`: Apply environment variable overrides
- `_get_default_config()`: Get default configuration
- `get(key, default)`: Get a configuration value by key

**Dependencies**:
- yaml
- dotenv

**Example**:
```python
from src.utils.cfg import ConfigLoader

# Load default config
config = ConfigLoader().config

# Load custom config
custom_config = ConfigLoader("custom_config.yaml").config

# Get specific value
ocr_model = config.get("ocr.mistral.model")
```

### Logger (`src/utils/logger.py`)

**Responsibility**: Provide logging functionality.

**Key Functions**:
- `setup_logger(name, level)`: Set up and configure a logger instance

**Dependencies**:
- logging

**Example**:
```python
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
logger.info("Application starting")
logger.debug("Detailed debug information")
logger.error("Error occurred")
```

## Main Module

The main module ties everything together and provides the CLI and API interfaces.

### InvoiceProcessor (`src/main.py`)

**Responsibility**: Main class for processing invoices and extracting data.

**Key Methods**:
- `__init__(config_path)`: Initialize the invoice processor
- `process(file_path)`: Process a single invoice file
- `batch_process(directory_path)`: Process all invoice files in a directory
- `export(data, format, output_path)`: Export the extracted data

**Example**:
```python
from src.main import InvoiceProcessor

# Process a single invoice
processor = InvoiceProcessor()
result = processor.process("path/to/invoice.pdf")
output_path = processor.export(result, "json", "output.json")

# Batch process invoices
results = processor.batch_process("path/to/invoices/")
output_path = processor.export(results, "csv", "batch_output.csv")
```

### Command Line Interface (`src/main.py::main()`)

**Usage**:
```bash
# Process a single invoice
python -m src.main process path/to/invoice.pdf --output output.json

# Batch process invoices
python -m src.main batch path/to/invoices/ --output output_dir/ --format csv

# Custom configuration
python -m src.main process path/to/invoice.pdf --config custom_config.yaml
``` 
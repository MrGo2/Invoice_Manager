# Usage Guide

This guide provides detailed instructions on setting up and using the Invoice Processor system.

## Table of Contents

1. [Setup](#setup)
2. [Configuration](#configuration)
3. [Directory Structure](#directory-structure)
4. [Command Line Interface](#command-line-interface)
5. [Python API](#python-api)
6. [Sample Workflow](#sample-workflow)
7. [Troubleshooting](#troubleshooting)

## Setup

### Prerequisites

Before using the Invoice Processor, ensure you have:

- Python 3.10 or higher
- Tesseract OCR installed (optional, for fallback OCR)
- API keys for Mistral and OpenAI

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/invoice-processor.git
   cd invoice-processor
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Tesseract OCR** (if using the fallback OCR):
   
   - **macOS**:
     ```bash
     brew install tesseract tesseract-lang
     ```
   
   - **Ubuntu/Debian**:
     ```bash
     sudo apt-get update
     sudo apt-get install -y tesseract-ocr tesseract-ocr-spa
     ```
   
   - **Windows**:
     - Download the installer from [UB-Mannheim's GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
     - During installation, select Spanish language data
     - Add Tesseract to your PATH environment variable

5. **Set up environment variables**:

   Create a `.env` file in the project root with your API keys:
   ```
   OPENAI_API_KEY=sk-your-openai-api-key
   MISTRAL_API_KEY=your-mistral-api-key
   ```

## Configuration

The system can be configured using the `config.yaml` file in the project root.

### Default Configuration

The default configuration is suitable for most use cases, but you may want to customize:

- OCR engine settings
- OpenAI model parameters
- Export formats
- Logging levels

### Custom Configuration

To create a custom configuration:

1. Copy the default `config.yaml` file:
   ```bash
   cp config.yaml custom-config.yaml
   ```

2. Edit the custom configuration file:
   ```yaml
   # Example: Change OpenAI model and temperature
   openai:
     model: gpt-4o
     temperature: 0.1
     max_tokens: 1500
   
   # Example: Disable Tesseract fallback
   tesseract_fallback: false
   
   # Example: Change logging level
   logging:
     level: DEBUG
   ```

3. Use the custom configuration when running the processor:
   ```bash
   python -m src.main process invoices/my_invoice.pdf --config custom-config.yaml
   ```

### Environment Variable Overrides

You can override configuration values using environment variables with the prefix `INVOICE_CONFIG_`:

```bash
# Set OpenAI model
export INVOICE_CONFIG_OPENAI_MODEL="gpt-4o"

# Disable Tesseract fallback
export INVOICE_CONFIG_TESSERACT_FALLBACK="false"

# Set logging level
export INVOICE_CONFIG_LOGGING_LEVEL="DEBUG"
```

## Directory Structure

The project is organized into the following directories:

```
Invoice_manager/
├── invoices/             # Place invoice files (PDF, JPG, PNG) here
├── output/               # Processed results are stored here
├── logs/                 # Log files are stored here
├── schemas/              # JSON schemas for validation
├── src/                  # Source code
│   ├── export/           # Export functionality
│   ├── extraction/       # Field extraction
│   ├── ocr/              # OCR processing
│   ├── preprocessing/    # Image preprocessing
│   ├── utils/            # Utilities
│   └── validation/       # Schema validation
├── docs/                 # Documentation
└── tests/                # Tests
```

### Working with Invoices

- Place all your invoice files (PDF, JPG, PNG, TIFF) in the `invoices/` directory
- Processed results will be stored in the `output/` directory by default
- Log files are stored in the `logs/` directory
- Custom configurations can be saved anywhere, but are typically kept in the project root

## Command Line Interface

The Invoice Processor provides a command-line interface with the following commands:

### Process a Single Invoice

```bash
python -m src.main process <file> [options]
```

**Arguments**:
- `file`: Path to the invoice file (PDF, JPG, PNG, or TIFF)

**Options**:
- `--output`, `-o`: Output file path
- `--format`, `-f`: Output format (`json`, `csv`, or `webhook`)
- `--config`, `-c`: Path to custom configuration file

**Example**:
```bash
python -m src.main process invoices/sample.pdf -o output/result.json -f json
```

### Batch Process Multiple Invoices

```bash
python -m src.main batch <directory> [options]
```

**Arguments**:
- `directory`: Path to directory containing invoice files

**Options**:
- `--output`, `-o`: Output directory path
- `--format`, `-f`: Output format (`json`, `csv`, or `webhook`)
- `--config`, `-c`: Path to custom configuration file

**Example**:
```bash
python -m src.main batch invoices/ -o output/ -f csv
```

## Python API

The Invoice Processor can also be used programmatically in your Python code:

### Process a Single Invoice

```python
from src.main import InvoiceProcessor

# Initialize with default configuration
processor = InvoiceProcessor()

# Process an invoice
result = processor.process("invoices/my_invoice.pdf")

# Export the result
output_path = processor.export(result, format="json", output_path="output/result.json")
print(f"Invoice processed and saved to: {output_path}")
```

### Batch Process Multiple Invoices

```python
from src.main import InvoiceProcessor
from pathlib import Path

processor = InvoiceProcessor()

# Process all invoices in a directory
results = processor.batch_process("invoices/")

# Export the results
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

for i, result in enumerate(results):
    output_path = output_dir / f"invoice_{i}.json"
    processor.export(result, format="json", output_path=output_path)

print(f"Processed {len(results)} invoices")
```

### Using Custom Configuration

```python
from src.main import InvoiceProcessor

# Initialize with custom configuration
processor = InvoiceProcessor("custom-config.yaml")

# Process an invoice
result = processor.process("invoices/my_invoice.pdf")
```

## Sample Workflow

Here's a complete example workflow:

1. **Prepare your invoices**:
   - Collect Spanish invoice files (PDF, JPG, PNG)
   - Place them in the `invoices/` directory

2. **Configure environment**:
   - Set up API keys in `.env` file
   - Customize `config.yaml` if needed

3. **Process invoices**:
   ```bash
   # Process all invoices
   python -m src.main batch invoices/ -o output/ -f json
   ```

4. **Review results**:
   - Check JSON files in the `output/` directory
   - Verify extraction accuracy
   - Inspect logs in the `logs/` directory

## Troubleshooting

### Common Issues

1. **OCR Errors**:
   - Ensure invoice images are clear and high-resolution
   - Try improving preprocessing with custom configuration
   - Check if the correct language pack is installed for Tesseract

2. **API Key Issues**:
   - Verify API keys are correctly set in the `.env` file
   - Check API key permissions and quotas

3. **PDF Conversion Errors**:
   - Ensure `pdf2image` and its dependencies are correctly installed
   - Try converting PDFs to images manually before processing

4. **Field Extraction Issues**:
   - Check OpenAI prompt logs in `docs/prompt_log.md`
   - Try adjusting few-shot examples

### Logs

Check the logs for detailed information:

- `logs/invoice_processor.log`: Main application log
- `logs/ocr_confidence.log`: OCR confidence metrics
- `logs/openai_latency.log`: OpenAI API latency metrics

### Getting Help

If you encounter issues not covered in this guide:

1. Check the GitHub repository's Issues section for similar problems
2. Review the documentation in the `docs/` directory
3. Submit a new issue with detailed information about your problem 
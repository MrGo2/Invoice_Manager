# Invoice Processor

[![CI Status](https://github.com/yourusername/invoice-processor/workflows/CI/badge.svg)](https://github.com/yourusername/invoice-processor/actions)

A production-grade Python application that extracts, processes, and validates data from Spanish invoices.

## Features

- Ingests PDF, JPG, PNG invoice images
- OCR processing with Mistral (primary) and Tesseract (fallback)
- Advanced extraction with OpenAI LLMs
- JSON output conforming to a robust validation schema
- Comprehensive logging and error handling

## Directory Structure

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

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/invoice-processor.git
cd invoice-processor

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Tesseract (if using Tesseract fallback)
# macOS:
brew install tesseract tesseract-lang

# Ubuntu:
# sudo apt-get install tesseract-ocr tesseract-ocr-spa
```

## Configuration

Set up your environment variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export MISTRAL_API_KEY="your-mistral-api-key"
```

Or create a `.env` file in the project root (not tracked by git).

## Usage

### Command Line

```bash
# Process a single invoice
python -m src.main process invoices/my_invoice.pdf -o output/result.json

# Process a directory of invoices
python -m src.main batch invoices/ -o output/ -f json

# Run with custom config
python -m src.main process invoices/my_invoice.pdf --config path/to/custom-config.yaml
```

### Python API

```python
from src.main import InvoiceProcessor

processor = InvoiceProcessor()
result = processor.process("invoices/my_invoice.pdf")
print(result.to_json())
```

## Documentation

Comprehensive documentation can be found in the `docs/` directory:

- [Introduction](docs/00_introduction.md)
- [Architecture](docs/01_architecture.md)
- [Modules](docs/02_modules.md)
- [Usage Guide](docs/03_usage.md)
- [Testing Strategy](docs/04_testing.md)
- [Future Roadmap](docs/05_future.md)

## Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 
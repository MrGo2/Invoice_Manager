<<<<<<< HEAD
# Invoice Processor

[![CI Status](https://github.com/yourusername/invoice-processor/workflows/CI/badge.svg)](https://github.com/yourusername/invoice-processor/actions)

A production-grade Python application that extracts, processes, and validates data from Spanish invoices.

## Features

- Ingests PDF, JPG, PNG invoice images
- OCR processing with Mistral (primary) and Tesseract (fallback)
- Advanced extraction with OpenAI LLMs
- JSON output conforming to a robust validation schema
- Comprehensive logging and error handling
- **NEW: Mistral OCR structured extraction for complete field extraction**
- **UPDATED: Improved Mistral API integration using latest client interface**

## Directory Structure

```
Invoice_manager/
├── invoices/             # Place invoice files (PDF, JPG, PNG) here
├── output/               # Processed results are stored here
├── logs/                 # Log files are stored here
├── schemas/              # JSON schemas for validation
├── src/                  # Source code
└── docs/                 # Documentation
```

## Installation

1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies:
   ```
   pip install -r temp_requirements.txt
   ```
4. Set up environment variables in `.env` file:
   ```
   MISTRAL_API_KEY=your_mistral_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```

## Usage

### Processing a Single Invoice

```bash
# Using the enhanced Mistral OCR structured extraction (default)
./process_invoice.py process invoices/your_invoice.pdf

# Using the standard pipeline
./process_invoice.py process invoices/your_invoice.pdf --standard

# Specify output file
./process_invoice.py process invoices/your_invoice.pdf -o output/result.json
```

### Batch Processing

```bash
# Process all invoices in a directory
./process_invoice.py batch invoices/

# Use standard pipeline for batch processing
./process_invoice.py batch invoices/ --standard
```

### Output Formats

- JSON (default): `--format json`
- CSV: `--format csv`

### Testing the Integration

You can verify that the Mistral API integration is working correctly by running:

```bash
python test_mistral_integration.py
```

This script will:
1. Find an invoice image in the `invoices/` directory
2. Run OCR using the Mistral API
3. Extract structured data from the OCR results
4. Save the results to the `output/` directory

## New Feature: Mistral OCR Structured Extraction

The application now includes an advanced structured extraction approach using Mistral's OCR capabilities:

1. **Two-stage extraction**: Uses a text-only model for efficiency, followed by a vision model for any missing fields
2. **Complete field coverage**: Extracts all Spanish invoice fields including mandatory regulatory information
3. **Intelligent fallback**: Reverts to standard pipeline if structured extraction yields insufficient results
4. **Updated API integration**: Uses the latest Mistral client interface for improved reliability

This approach delivers more comprehensive invoice data extraction with higher accuracy.

## Schema Support

The system supports the complete Spanish invoice schema, including:

- Header & Party Information: invoice numbers, vendor/buyer details, tax IDs
- Financial Data: taxable base, VAT rates, totals, surcharges
- Line Items: product details, quantities, prices, discounts
- Payment Information: terms, methods, bank details
- Regulatory & Metadata: electronic signatures, SII information

## Performance Considerations

- **Memory Usage**: Vision models require more memory; ensure 4GB+ RAM
- **Processing Time**: Structured extraction takes ~5-10 seconds per invoice
- **API Costs**: Uses Mistral API calls; check pricing for production usage

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
=======
# Invoice_Manager
>>>>>>> 862bcdfd7e2ae7bc10cc203509d7cf2c06f2cc65

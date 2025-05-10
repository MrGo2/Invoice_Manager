# Introduction to Invoice Processor

## Problem Statement

Businesses processing Spanish invoices face several challenges:

1. **Manual Data Entry:** Traditional invoice processing requires manual data extraction, which is time-consuming and error-prone.
2. **Format Variability:** Spanish invoices come in multiple formats, layouts, and styles without standardization.
3. **Regulatory Compliance:** Spanish tax regulations require specific data extraction for compliance.
4. **Multilingual Content:** Some invoices contain both Spanish and other languages (English, Catalan, etc.).
5. **Data Accuracy:** Errors in extraction can lead to financial discrepancies and compliance issues.

## Goals

The Invoice Processor aims to solve these problems through:

1. **Automated Extraction:** Eliminate manual data entry by automatically extracting key information from invoices.
2. **High Accuracy:** Utilize multiple OCR engines and LLM refinement to achieve high extraction accuracy.
3. **Format Flexibility:** Process invoices in various formats (PDF, JPG, PNG) and layouts.
4. **Structured Output:** Produce standardized JSON output that conforms to a consistent schema.
5. **Validation:** Implement validation to ensure extracted data meets required format and completeness.
6. **Production Readiness:** Provide a robust, well-documented, and tested solution suitable for production use.

## Scope

### In Scope

- Processing Spanish invoices in PDF, JPG, PNG, and TIFF formats
- OCR using Mistral (primary) and Tesseract (fallback)
- Extraction of key invoice fields including:
  - Invoice number
  - Issue date
  - Total amount
  - VAT rate and amount
  - Vendor and buyer details
  - Line items (when available)
- Refinement of extraction using OpenAI GPT-4o
- JSON output conforming to a predefined schema
- Basic validation of extracted data
- Comprehensive logging and error handling
- CSV and webhook export options

### Out of Scope

- Real-time processing or streaming API
- Electronic invoice formats (XML, EDI, etc.)
- Integration with accounting software
- Invoice generation or modification
- Full-text search over processed invoices
- Fraud detection (planned for future versions)
- Languages other than Spanish (planned for future versions)

## Technology Stack

- **Python 3.10+:** Core programming language
- **Mistral OCR:** Primary OCR engine specialized for Spanish language
- **Tesseract OCR:** Fallback OCR engine for comparison and reliability
- **OpenAI GPT-4o:** LLM for refinement and extraction improvement
- **OpenCV & Pillow:** Image preprocessing
- **JSONSchema:** Data validation
- **PyYAML:** Configuration management

This document provides an overview of the Invoice Processor project. For detailed information on architecture, modules, and usage, please refer to the subsequent documentation sections. 
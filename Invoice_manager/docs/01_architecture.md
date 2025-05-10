# Architecture Overview

## System Architecture

The Invoice Processor is designed as a modular pipeline with distinct stages for transforming raw invoice images into structured data:

```
                      ┌────────────┐
                      │            │
                      │   Input    │
                      │  (PDF/IMG) │
                      │            │
                      └─────┬──────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │                 │
                   │  Preprocessing  │
                   │                 │
                   └────────┬────────┘
                            │
                            ▼
                  ┌──────────────────┐
                  │                  │
         ┌────────┤       OCR        ├────────┐
         │        │                  │        │
         │        └──────────────────┘        │
         ▼                                    ▼
┌─────────────────┐                  ┌─────────────────┐
│                 │                  │                 │
│   Mistral OCR   │                  │ Tesseract OCR   │
│                 │                  │                 │
└────────┬────────┘                  └────────┬────────┘
         │                                    │
         ▼                                    ▼
         ┌───────────────────────────────────┐
         │                                   │
         │         Confidence Merger         │
         │                                   │
         └─────────────────┬─────────────────┘
                           │
                           ▼
                ┌────────────────────┐
                │                    │
                │   Field Location   │
                │                    │
                └──────────┬─────────┘
                           │
                           ▼
                ┌────────────────────┐
                │                    │
                │   OpenAI Refiner   │
                │                    │
                └──────────┬─────────┘
                           │
                           ▼
                ┌────────────────────┐
                │                    │
                │ Schema Validation  │
                │                    │
                └──────────┬─────────┘
                           │
                           ▼
             ┌─────────────────────────┐
             │                         │
    ┌────────┤        Export           ├────────┐
    │        │                         │        │
    ▼        └─────────────────────────┘        ▼
┌──────────┐                             ┌────────────┐
│          │                             │            │
│   JSON   │                             │    CSV     │
│          │                             │            │
└──────────┘                             └────────────┘
```

## Data Flow

1. **Input**: The system accepts invoice documents in PDF, JPG, PNG, or TIFF formats.

2. **Preprocessing**:
   - PDF files are converted to images
   - Images are enhanced through deskewing, contrast adjustment, and noise removal
   - Optimized for OCR readability

3. **OCR Processing**:
   - **Primary OCR** (Mistral): Specialized for Spanish language documents
   - **Fallback OCR** (Tesseract): Used for comparison or when Mistral fails
   - **Confidence Merging**: Combines results based on confidence scores

4. **Field Extraction**:
   - **Initial Extraction**: Uses regex and heuristics to locate key invoice fields
   - **OpenAI Refinement**: Enhances extraction using few-shot prompting with GPT-4o

5. **Validation**:
   - Validates extracted data against JSON schema
   - Formats fields to comply with schema requirements
   - Flags inconsistencies or missing required data

6. **Export**:
   - JSON output (default): Structured, schema-compliant invoice data
   - CSV: Flattened format for spreadsheet compatibility
   - Webhook: Optional HTTP endpoint integration

## Component Architecture

### Core Components

1. **Image Processor** (`src/preprocessing/image_processor.py`)
   - Handles image preparation for optimal OCR
   - PDF conversion, image enhancement, deskewing
   - OpenCV-based processing algorithms

2. **OCR Engine** (`src/ocr/`)
   - Mistral wrapper (`mistral_wrapper.py`)
   - Tesseract fallback (`tesseract_fallback.py`)
   - Confidence merger (`confidence_merger.py`)
   - Common interface for OCR processing

3. **Extraction Engine** (`src/extraction/`)
   - Field locator for initial extraction (`field_locator.py`)
   - OpenAI refinement (`openai_refiner.py`)
   - Prompt templates for LLM processing (`prompts/`)

4. **Validation** (`src/validation/`)
   - Schema-based validation (`schema_validator.py`)
   - Format standardization and correction

5. **Export** (`src/export/`)
   - Multiple format writers (JSON, CSV)
   - Webhook integration

### Support Components

1. **Configuration** (`src/utils/cfg.py`)
   - YAML configuration loading
   - Environment variable support
   - Default configuration fallbacks

2. **Logging** (`src/utils/logger.py`)
   - Centralized logging system
   - Rotating file handlers
   - Special handlers for OCR confidence and LLM metrics

3. **CLI Interface** (`src/main.py`)
   - Command-line processing
   - Batch processing support
   - Python API for programmatic usage

## Dependency Design

The system follows a modular design with clear dependencies:

```
main.py
  ├── ConfigLoader
  ├── ImageProcessor
  │    └── OpenCV/Pillow
  ├── OCR Engines
  │    ├── MistralOCR
  │    ├── TesseractOCR
  │    └── OCRMerger
  ├── Extraction
  │    ├── FieldLocator
  │    └── OpenAIRefiner
  │         └── Jinja2 Templates
  ├── SchemaValidator
  │    └── JSONSchema
  └── Writers
       ├── JSONWriter
       ├── CSVWriter  
       └── WebhookWriter
```

## Error Handling Strategy

The system implements robust error handling:

1. **Fallback Mechanisms**:
   - Tesseract OCR when Mistral fails
   - Regex extraction when OpenAI refinement fails
   - Default values for missing required fields

2. **Exception Management**:
   - Granular exception handling at each stage
   - Contextual error information
   - Non-blocking error recovery when possible

3. **Logging**:
   - Detailed error reporting
   - Performance metrics
   - Confidence scores for traceability

## Configuration System

The configuration system provides flexibility through:

1. **Multiple Sources**:
   - YAML configuration file (default: `config.yaml`)
   - Environment variables with `INVOICE_CONFIG_` prefix
   - Command-line options for key settings

2. **Hierarchical Structure**:
   - Organized into logical sections
   - Inheritance of defaults
   - Environment variable overrides

3. **Validation**:
   - Type checking
   - Required setting verification
   - Sensible defaults

This architecture provides a robust, maintainable, and extensible system for invoice processing with clear separation of concerns and well-defined interfaces between components. 
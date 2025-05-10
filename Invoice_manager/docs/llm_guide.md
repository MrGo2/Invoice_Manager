# LLM Prompt Engineering Guide

This document provides guidelines and best practices for prompt engineering when working with Large Language Models (LLMs) in the Invoice Processor system.

## Table of Contents

1. [Introduction](#introduction)
2. [Prompt Design Principles](#prompt-design-principles)
3. [Few-Shot Learning](#few-shot-learning)
4. [Prompt Templates](#prompt-templates)
5. [Evaluation Metrics](#evaluation-metrics)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Techniques](#advanced-techniques)

## Introduction

The Invoice Processor uses OpenAI's GPT-4o model to refine and enhance invoice data extraction. Effective prompt engineering is critical for achieving high accuracy in the extraction process.

### Why Prompt Engineering Matters

For invoice processing, prompt engineering:
- Guides the model to extract structured data in the correct format
- Helps the model handle edge cases and unusual invoice layouts
- Improves accuracy for specific fields like dates, amounts, and tax IDs
- Ensures schema compliance for downstream processing

## Prompt Design Principles

When designing prompts for invoice extraction, follow these core principles:

### 1. Clear Instructions

Provide explicit, step-by-step instructions:

```
You are a meticulous Spanish invoice parser. Extract the following fields from the invoice text:
1. Invoice number
2. Issue date (in DD/MM/YYYY format)
3. Total amount (including currency symbol)
4. VAT information (rate and amount)
5. Vendor and buyer details
```

### 2. Structured Output Format

Clearly define the expected output format:

```
Output ONLY a valid JSON object with the following structure:
{
  "invoice_number": "string",
  "issue_date": "string (DD/MM/YYYY)",
  "total_eur": "string",
  "vat_rate": "string",
  "vat_amount": "string",
  "vendor_name": "string",
  "vendor_tax_id": "string",
  "buyer_name": "string"
}
```

### 3. Context Provision

Provide relevant context about Spanish invoices:

```
Spanish invoices typically include:
- "Factura" or "Fra." indicating the invoice number
- Dates in DD/MM/YYYY format
- VAT indicated as "IVA" (typically 21%, 10%, or 4%)
- Tax IDs (NIF/CIF) in the format X12345678
```

### 4. Error Handling Guidance

Include instructions for handling missing or ambiguous data:

```
If a required field cannot be confidently extracted:
- For dates, use the format "DD/MM/YYYY" with best estimate
- For monetary amounts, maintain the original format (with or without € symbol)
- For missing tax IDs, output "N/A"
- Include a confidence score for uncertain extractions
```

## Few-Shot Learning

Few-shot examples significantly improve extraction quality by demonstrating the expected parsing process.

### Example Structure

Each few-shot example should include:
1. Sample OCR text
2. Correct extraction result
3. (Optional) Explanation of reasoning

### Effective Examples

Select examples that represent:
- Different invoice layouts and formats
- Varying complexity levels
- Common edge cases
- Industry-specific variations

### Example Implementation

```
# Example 1: Standard Invoice

OCR Text:
```
EMPRESA EJEMPLO S.L.
C/ Ejemplo, 123
28001 Madrid, España
CIF: B12345678

FACTURA
Número: F2023-1234
Fecha: 15/06/2023

CLIENTE:
Cliente Ejemplo S.A.
C/ Cliente, 456
08001 Barcelona, España
CIF: A87654321

Base imponible: 1727,50 €
IVA (21%): 362,78 €
TOTAL FACTURA: 2090,28 €
```

Correct Extraction:
```json
{
  "invoice_number": "F2023-1234",
  "issue_date": "15/06/2023",
  "total_eur": "2090,28 €",
  "vat_rate": "21%",
  "vat_amount": "362,78 €",
  "vendor_name": "EMPRESA EJEMPLO S.L.",
  "vendor_tax_id": "B12345678",
  "buyer_name": "Cliente Ejemplo S.A."
}
```
```

## Prompt Templates

The system uses Jinja2 templates for generating prompts. These templates allow for dynamic content inclusion while maintaining a consistent structure.

### Base Template Structure

```jinja
You are a meticulous Spanish invoice parser. Your job is to extract structured data from invoice OCR text according to a specific schema.

# Schema
The extracted data must conform to this schema:
```json
{{ schema | tojson(indent=2) }}
```

# Instructions
1. Extract all required fields and any available optional fields from the OCR text.
2. Normalize all extracted values to match the expected format in the schema.
3. For dates, ensure they are in DD/MM/YYYY format.
4. For currency amounts, keep the original format (with or without € symbol).

# Example Extractions
{% for example in examples %}
## Example {{ loop.index }}

OCR Text:
```
{{ example.ocr_text }}
```

Correct Extraction:
```json
{{ example.extraction | tojson(indent=2) }}
```

{% endfor %}

# Output Format
Respond ONLY with a valid JSON object containing all extracted fields.
```

### Chain of Thought

The templates include hidden chain-of-thought instructions using HTML comments:

```html
<!--internal-->
# Analysis Process
1. First, identify the invoice structure and layout (header, items table, footer).
2. Look for key identifiers like "Factura", "Total", etc. to locate important sections.
3. Extract required fields first, then optional fields.
4. Validate data against the schema requirements.
<!--/internal-->
```

This provides the model with a reasoning framework without cluttering the final output.

## Evaluation Metrics

Use these metrics to evaluate and improve prompts:

### Accuracy Metrics

- **Field-level Accuracy**: Percentage of correctly extracted fields
- **Exact Match Accuracy**: Percentage of invoices with all fields correctly extracted
- **Format Compliance**: Percentage of fields matching expected format (dates, currency, etc.)

### Monitoring Process

1. Log all prompts and responses to `docs/prompt_log.md`
2. Review failures to identify patterns
3. Iteratively improve prompts based on failure analysis
4. A/B test prompt variations on challenging cases

## Troubleshooting

Common issues and solutions:

### Field Extraction Failures

If specific fields consistently fail to extract:

1. **Analyze OCR Quality**: Check if OCR correctly captures the text
2. **Review Field Patterns**: Update regex patterns in `field_locator.py`
3. **Add Specialized Examples**: Include examples that highlight the problematic field
4. **Field-Specific Instructions**: Add explicit instructions for the field

### Format Inconsistencies

If extracted formats are inconsistent:

1. **Strengthen Format Instructions**: Make format requirements more explicit
2. **Add Normalization Examples**: Show before/after normalization examples
3. **Update Validation Logic**: Enhance post-processing in `schema_validator.py`

## Advanced Techniques

### Hybrid Extraction Approach

The system uses a hybrid approach:
1. Initial extraction with regex patterns
2. LLM refinement with context of initial extraction
3. Schema validation and correction

This reduces hallucination risk while leveraging LLM capabilities.

### Progressive Enhancement

Start with simple prompts and progressively enhance:

1. **Basic Extraction**: Simple extraction without complex instructions
2. **Format Standardization**: Add format standardization rules
3. **Edge Case Handling**: Include examples for challenging cases
4. **Advanced Reasoning**: Add chain-of-thought for complex documents

### Customizing for Specific Vendors

For recurring vendors with consistent formats:

1. Create vendor-specific examples
2. Add vendor-specific instructions
3. Consider template-based extraction for highly structured invoices

### Continuous Improvement

- Regularly review extraction failures
- Update examples with challenging cases
- Benchmark prompt versions to measure improvements
- Monitor OpenAI model updates and adjust prompts accordingly 
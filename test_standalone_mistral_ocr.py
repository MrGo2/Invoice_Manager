#!/usr/bin/env python3
"""
Standalone test script for Mistral OCR PDF processing.
This script directly uses the Mistral API to process a PDF invoice without
relying on the project structure.
"""

import os
import sys
import json
import base64
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check for required packages
try:
    from mistralai import Mistral
except ImportError:
    print("❌ Mistral AI package not found. Please install it with:")
    print("pip install mistralai")
    sys.exit(1)

def test_mistral_pdf_ocr():
    """Test direct PDF processing with Mistral's OCR API."""
    print("\n=== Testing Mistral OCR Direct PDF Processing ===\n")
    
    # Check if API key is available
    mistral_api_key = os.environ.get("MISTRAL_API_KEY")
    if not mistral_api_key:
        print("❌ MISTRAL_API_KEY environment variable not found.")
        print("Please set your Mistral API key in the .env file.")
        return False
    
    # Path to sample invoice
    invoice_path = "invoices/invoice-5.pdf"
    
    # Verify the invoice exists
    if not Path(invoice_path).exists():
        print(f"❌ Sample invoice not found at: {invoice_path}")
        print("Please ensure there's an invoice file at this location.")
        return False
    
    print(f"✓ Found sample invoice: {invoice_path}")
    
    try:
        # Initialize Mistral client
        client = Mistral(api_key=mistral_api_key)
        
        # Process the PDF directly
        start_time = datetime.now()
        print(f"Processing PDF with Mistral OCR...")
        
        # Step 1: Upload the PDF file to Mistral
        with open(invoice_path, "rb") as pdf_file:
            upload_result = client.files.upload(
                file={
                    "file_name": Path(invoice_path).name,
                    "content": pdf_file
                },
                purpose="ocr"
            )
        print(f"✓ File uploaded with ID: {upload_result.id}")
        
        # Step 2: Get a signed URL for the uploaded file
        signed_url = client.files.get_signed_url(file_id=upload_result.id)
        print(f"✓ Got signed URL for processing")
        
        # Step 3: Process the PDF with Mistral OCR
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": signed_url.url
            }
        )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Display information about the OCR results
        print(f"\n✓ Successfully processed invoice in {processing_time:.2f} seconds")
        print(f"✓ Number of pages processed: {len(ocr_response.pages)}")
        
        # Save the OCR results to file
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "mistral_ocr_pdf_result.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, page in enumerate(ocr_response.pages):
                f.write(f"\n## Page {i+1}\n\n")
                f.write(page.markdown)
                f.write("\n\n")
        
        print(f"\n✓ Full OCR results saved to: {output_file}")
        
        # Display the first page content (for preview)
        if ocr_response.pages:
            print("\n=== First Page Preview ===\n")
            preview = ocr_response.pages[0].markdown[:500] + "..." if len(ocr_response.pages[0].markdown) > 500 else ocr_response.pages[0].markdown
            print(preview)
        
        # Extract structured information
        print("\n=== Extracting Structured Invoice Information ===\n")
        
        # Extract structured data with Mistral's chat model
        first_page_content = ocr_response.pages[0].markdown
        
        # Request structured extraction
        extraction_start = datetime.now()
        chat_response = client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {
                    "role": "user", 
                    "content": f"Extract the following information from this invoice: invoice number, date, vendor name, vendor tax id, vendor address, buyer name, buyer tax id, buyer address, line items (with descriptions, quantities, unit prices), taxable base, vat rate, vat amount, total amount, payment terms, currency. Return in JSON format only:\n\n{first_page_content}"
                }
            ]
        )
        
        extraction_time = (datetime.now() - extraction_start).total_seconds()
        
        # Get the structured data and parse as JSON
        structured_data = chat_response.choices[0].message.content
        
        # Save the structured data to a file
        structured_output_file = output_dir / "mistral_pdf_structured_data.json"
        
        try:
            # Try to parse and pretty-print if it's valid JSON
            json_data = json.loads(structured_data)
            with open(structured_output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
                
            # Display key extracted information
            print(f"✓ Structured data extraction completed in {extraction_time:.2f} seconds")
            print(f"✓ Structured data saved to: {structured_output_file}")
            
            # Display select fields from the extracted data
            print("\n=== Key Invoice Information ===\n")
            
            key_fields = [
                "invoice_number", "date", "vendor_name", "total_amount", 
                "vendor_tax_id", "buyer_name", "currency"
            ]
            
            for field in key_fields:
                if field in json_data:
                    print(f"{field.replace('_', ' ').title()}: {json_data[field]}")
                    
        except json.JSONDecodeError:
            # If not valid JSON, save as raw text
            with open(structured_output_file, 'w', encoding='utf-8') as f:
                f.write(structured_data)
            print(f"✓ Raw extraction results saved to: {structured_output_file}")
            print(structured_data)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during PDF processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_mistral_pdf_ocr() 
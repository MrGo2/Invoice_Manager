#!/usr/bin/env python3
"""
Test script to verify Mistral OCR integration with invoice processing.
This script processes a sample invoice PDF directly with Mistral OCR.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

try:
    from mistralai import Mistral
    
    # Get the Mistral API key from environment variables
    mistral_api_key = os.environ.get("MISTRAL_API_KEY")
    if not mistral_api_key:
        print("❌ MISTRAL_API_KEY environment variable not found.")
        sys.exit(1)
        
    # Initialize Mistral client
    client = Mistral(api_key=mistral_api_key)
    
except ImportError as e:
    print(f"❌ Error importing Mistral packages: {e}")
    print("Please install the required packages with: pip install mistralai python-dotenv")
    sys.exit(1)
    
def test_mistral_ocr_on_invoice():
    """Test processing an invoice PDF directly with Mistral OCR."""
    print("\n=== Testing Mistral OCR on Invoice PDF ===\n")
    
    # Path to sample invoice
    invoice_path = "invoices/invoice-5.pdf"
    
    # Verify the invoice exists
    if not Path(invoice_path).exists():
        print(f"❌ Sample invoice not found at: {invoice_path}")
        print("Please ensure there's an invoice file at this location.")
        return False
    
    print(f"✓ Found sample invoice: {invoice_path}")
    
    # Process the invoice
    start_time = datetime.now()
    print("Processing invoice with Mistral OCR...")
    
    try:
        # Step 1: Upload the PDF file to Mistral for processing
        upload_result = client.files.upload(
            file={
                "file_name": Path(invoice_path).name,
                "content": open(invoice_path, "rb")
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
        
        # Extract and display invoice data
        print("\n=== Extracted Invoice Content ===")
        
        # Save the full OCR results to a file for inspection
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "mistral_ocr_result.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, page in enumerate(ocr_response.pages):
                f.write(f"\n--- PAGE {i+1} ---\n\n")
                f.write(page.markdown)
        
        print(f"\n✓ Full OCR results saved to: {output_file}")
        
        # Display the first page content (for preview)
        if ocr_response.pages:
            print("\n=== First Page Preview ===\n")
            print(ocr_response.pages[0].markdown[:500] + "..." if len(ocr_response.pages[0].markdown) > 500 else ocr_response.pages[0].markdown)
        
        # Now process this with an LLM to extract structured information
        print("\n=== Extracting Structured Invoice Information ===\n")
        
        # Use Mistral chat to extract structured information from the OCR result
        first_page_content = ocr_response.pages[0].markdown
        chat_response = client.chat.complete(
            model="mistral-large-latest",
            messages=[
                {
                    "role": "user", 
                    "content": f"Extract the following information from this invoice: invoice number, date, vendor name, total amount, and line items. Return in JSON format:\n\n{first_page_content}"
                }
            ]
        )
        
        # Extract structured data from response
        structured_data = chat_response.choices[0].message.content
        print(structured_data)
        
        # Save the structured data to a file
        structured_output_file = output_dir / "invoice_structured_data.json"
        
        try:
            # Try to parse and pretty-print if it's valid JSON
            json_data = json.loads(structured_data)
            with open(structured_output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            # If not valid JSON, save as raw text
            with open(structured_output_file, 'w', encoding='utf-8') as f:
                f.write(structured_data)
        
        print(f"\n✓ Structured data saved to: {structured_output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error during invoice processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_mistral_ocr_on_invoice() 
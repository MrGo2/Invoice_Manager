#!/usr/bin/env python3
"""
Test script to verify the updated MistralOCR class with direct PDF processing.
This script tests the native Mistral OCR API for PDF documents without conversion to images.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# Add the Invoice_manager directory to the Python path
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))

try:
    # Import our updated OCR class
    from Invoice_manager.src.ocr.mistral_wrapper import MistralOCR
    from Invoice_manager.src.utils.cfg import ConfigLoader
    
except ImportError as e:
    print(f"❌ Error importing required modules: {e}")
    print("Please ensure the Invoice_manager module is in your Python path.")
    sys.exit(1)

def test_pdf_direct_processing():
    """Test direct PDF processing with the updated MistralOCR class."""
    print("\n=== Testing Direct PDF Processing with Mistral OCR ===\n")
    
    # Path to sample invoice
    invoice_path = "invoices/invoice-5.pdf"
    
    # Verify the invoice exists
    if not Path(invoice_path).exists():
        print(f"❌ Sample invoice not found at: {invoice_path}")
        print("Please ensure there's an invoice file at this location.")
        return False
    
    print(f"✓ Found sample invoice: {invoice_path}")
    
    try:
        # Load configuration
        config_loader = ConfigLoader("config.yaml")
        # The config is already loaded during initialization, we can access it directly
        config = config_loader.config
        
        # Initialize the OCR class with the configuration
        ocr = MistralOCR(config)
        
        # Process the PDF directly
        start_time = datetime.now()
        print(f"Processing PDF with Mistral OCR...")
        
        # Run OCR on the PDF file - this should use the new direct PDF processing method
        ocr_results = ocr.run_ocr(invoice_path)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Display OCR results
        if ocr_results:
            total_words = len(ocr_results)
            print(f"✓ Successfully processed PDF in {processing_time:.2f} seconds")
            print(f"✓ Extracted {total_words} words from the document")
            
            # Get unique pages in results
            pages = set(word["page"] for word in ocr_results)
            print(f"✓ Document has {len(pages)} page(s)")
            
            # Save the raw OCR text to a file
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            # Get the markdown from the OCR response
            markdown_pages = ocr.get_markdown_from_last_ocr()
            
            if markdown_pages:
                # Save complete markdown
                output_file = output_dir / "pdf_ocr_result.md"
                with open(output_file, 'w', encoding='utf-8') as f:
                    for i, page_md in enumerate(markdown_pages):
                        f.write(f"\n## Page {i+1}\n\n")
                        f.write(page_md)
                        f.write("\n\n")
                
                print(f"✓ OCR results saved to: {output_file}")
                
                # Preview first part of the OCR text
                print("\n=== OCR Text Preview ===\n")
                preview = markdown_pages[0][:500] + "..." if len(markdown_pages[0]) > 500 else markdown_pages[0]
                print(preview)
                print("\n")
            else:
                # Fallback to word-by-word text assembly if markdown isn't available
                text = ocr.get_text_from_results(ocr_results)
                output_file = output_dir / "pdf_ocr_result.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"✓ OCR text saved to: {output_file}")
                
                # Preview OCR text
                print("\n=== OCR Text Preview ===\n")
                preview = text[:500] + "..." if len(text) > 500 else text
                print(preview)
                print("\n")
            
            # Now extract structured data from the OCR results
            print("Extracting structured data from OCR results...")
            start_extract_time = datetime.now()
            structured_data = ocr.extract_structured_data(invoice_path)
            extract_time = (datetime.now() - start_extract_time).total_seconds()
            
            # Save the structured data to a file
            structured_output_file = output_dir / "pdf_structured_data.json"
            with open(structured_output_file, 'w', encoding='utf-8') as f:
                json.dump(structured_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Structured data extraction completed in {extract_time:.2f} seconds")
            print(f"✓ Structured data saved to: {structured_output_file}")
            
            # Display key information from the structured data
            print("\n=== Extracted Invoice Information ===\n")
            
            # Fields to display (adjust based on your schema)
            key_fields = [
                "invoice_number", "date", "vendor_name", "total_amount", 
                "vendor_tax_id", "buyer_name", "currency"
            ]
            
            for field in key_fields:
                if field in structured_data:
                    print(f"{field.replace('_', ' ').title()}: {structured_data[field]}")
            
            return True
            
        else:
            print("❌ No OCR results returned")
            return False
            
    except Exception as e:
        print(f"❌ Error during PDF processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_pdf_direct_processing() 
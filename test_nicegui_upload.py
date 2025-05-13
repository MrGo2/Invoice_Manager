#!/usr/bin/env python3
"""
Test the NiceGUI app's upload handling with a real invoice
"""

import sys
import json
import asyncio
from pathlib import Path
import tempfile
import shutil

# Add the project root to path
sys.path.insert(0, '.')

async def simulate_nicegui_upload():
    """Simulate the GUI's handle_invoice_upload with a real invoice"""
    
    print("=== Testing NiceGUI Upload with Real Invoice ===\n")
    
    # Import dependencies
    from process_invoice import process_single_invoice
    
    # Path to the real invoice
    invoice_path = "invoices/invoice-5.pdf"
    print(f"Testing with invoice: {invoice_path}")
    
    # Create a temporary copy to simulate the upload
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        shutil.copy2(invoice_path, tmp_file.name)
        temp_path = tmp_file.name
        
    print(f"Created temporary copy at: {temp_path}")
    
    try:
        # Simulate the processing part of handle_invoice_upload
        print("Simulating OCR processing...")
        
        if asyncio.iscoroutinefunction(process_single_invoice):
            # If it's already async
            ocr_result = await process_single_invoice(
                str(temp_path),
                use_mistral_structured=True,
                direct_pdf_processing=True
            )
        else:
            # Run in a thread pool if it's synchronous
            ocr_result = await asyncio.to_thread(
                process_single_invoice,
                str(temp_path),
                use_mistral_structured=True,
                direct_pdf_processing=True
            )
        
        # Check result type
        print(f"\nOCR Result type: {type(ocr_result)}")
        print(f"OCR Result content is dict: {isinstance(ocr_result, dict)}")
        
        if isinstance(ocr_result, dict):
            # Print key fields
            print("\nExtracted Key Fields:")
            print(f"Invoice Number: {ocr_result.get('invoice_number', 'N/A')}")
            print(f"Vendor Name: {ocr_result.get('vendor_name', 'N/A')}")
            print(f"Total Amount: {ocr_result.get('total_amount', 'N/A')}")
            
            # Check metadata
            if "metadata" in ocr_result:
                print("\nMetadata:")
                meta = ocr_result["metadata"]
                for key in ['source_file', 'extraction_method', 'ocr_engine', 'confidence_score']:
                    if key in meta:
                        print(f"{key}: {meta[key]}")
                
                # Check for errors
                if "error" in meta:
                    print(f"\nERROR DETECTED: {meta['error_type']}")
                    print(f"Error: {meta['error']}")
    
    except Exception as e:
        print(f"\nException during processing: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        
    finally:
        # Clean up the temporary file
        try:
            Path(temp_path).unlink()
            print(f"\nRemoved temporary file: {temp_path}")
        except Exception as e:
            print(f"Error removing temp file: {e}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(simulate_nicegui_upload()) 
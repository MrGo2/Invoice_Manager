#!/usr/bin/env python3
"""
Test how process_invoice.py works with the handle_invoice_upload logic
"""

import sys
import json
import asyncio
from pathlib import Path
import tempfile

# Add the project root to path
sys.path.insert(0, '.')

# Import process_single_invoice directly to avoid loading NiceGUI
from process_invoice import process_single_invoice

async def simulate_upload_handling():
    """Simulate the logic in handle_invoice_upload from invoice_app_main.py"""
    
    test_file = "test_error.pdf"
    print(f"Simulating upload of: {test_file}")
    
    try:
        # This simulates the core OCR processing logic of handle_invoice_upload
        ocr_result = None
        
        if asyncio.iscoroutinefunction(process_single_invoice):
            # If it's already async
            ocr_result = await process_single_invoice(
                str(test_file),
                use_mistral_structured=True,
                direct_pdf_processing=True
            )
        else:
            # Run in a thread pool if it's synchronous
            ocr_result = await asyncio.to_thread(
                process_single_invoice,
                str(test_file),
                use_mistral_structured=True,
                direct_pdf_processing=True
            )
        
        # Print the OCR result to debug
        print(f"OCR Result type: {type(ocr_result)}")
        
        # Check if OCR result is None or not a dictionary
        if ocr_result is None:
            print("PROBLEM: OCR result is None")
            # This would've triggered an error in the original code
            return
        
        if not isinstance(ocr_result, dict):
            print(f"PROBLEM: OCR result is not a dictionary but {type(ocr_result)}")
            return
            
        # Print the structured OCR result
        print("\nStructured OCR result received:")
        print(f"invoice_number: {ocr_result.get('invoice_number', 'N/A')}")
        print(f"vendor_name: {ocr_result.get('vendor_name', 'N/A')}")
        print(f"total_amount: {ocr_result.get('total_amount', 'N/A')}")
        
        # Check if there's error information
        if "metadata" in ocr_result and ocr_result["metadata"].get("error"):
            print("\nError details found in metadata:")
            print(f"Error type: {ocr_result['metadata'].get('error_type')}")
            print(f"Error message: {ocr_result['metadata'].get('error')[:150]}...")
            
    except Exception as e:
        print(f"Exception during processing: {type(e).__name__}: {str(e)}")
        
async def main():
    print("=== Testing GUI Integration Logic ===\n")
    await simulate_upload_handling()
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(main()) 
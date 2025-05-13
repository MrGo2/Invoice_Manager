#!/usr/bin/env python3
"""
Test process_single_invoice with a real invoice file
"""

import sys
import json
from pathlib import Path

# Add the project root to path
sys.path.insert(0, '.')

from process_invoice import process_single_invoice

def test_with_real_invoice():
    """Test processing with a real invoice file"""
    
    invoice_path = "invoices/invoice-5.pdf"
    print(f"=== Testing with real invoice: {invoice_path} ===\n")
    
    # Process with default settings
    print("Processing with default settings...")
    result = process_single_invoice(invoice_path)
    
    # Analyze result
    print(f"\nResult type: {type(result)}")
    
    if isinstance(result, dict):
        # Print key extracted fields
        print("\nExtracted fields:")
        print(f"Invoice Number: {result.get('invoice_number', 'N/A')}")
        print(f"Issue Date: {result.get('issue_date', 'N/A')}")
        print(f"Vendor Name: {result.get('vendor_name', 'N/A')}")
        print(f"Total Amount: {result.get('total_amount', 'N/A')}")
        
        # Check for errors
        if "metadata" in result and result["metadata"].get("error"):
            print("\nERROR DETECTED:")
            print(f"Error type: {result['metadata'].get('error_type')}")
            print(f"Error: {result['metadata'].get('error')}")
    else:
        print(f"Unexpected result type: {type(result)}")
    
    # Now test with direct PDF processing
    print("\n\nProcessing with direct_pdf_processing=True...")
    result_direct = process_single_invoice(invoice_path, direct_pdf_processing=True)
    
    # Analyze direct PDF result
    print(f"\nResult type: {type(result_direct)}")
    
    if isinstance(result_direct, dict):
        # Print key extracted fields
        print("\nExtracted fields (direct PDF mode):")
        print(f"Invoice Number: {result_direct.get('invoice_number', 'N/A')}")
        print(f"Issue Date: {result_direct.get('issue_date', 'N/A')}")
        print(f"Vendor Name: {result_direct.get('vendor_name', 'N/A')}")
        print(f"Total Amount: {result_direct.get('total_amount', 'N/A')}")
        
        # Check for errors
        if "metadata" in result_direct and result_direct["metadata"].get("error"):
            print("\nERROR DETECTED (direct PDF mode):")
            print(f"Error type: {result_direct['metadata'].get('error_type')}")
            print(f"Error: {result_direct['metadata'].get('error')}")
    else:
        print(f"Unexpected result type: {type(result_direct)}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_with_real_invoice() 
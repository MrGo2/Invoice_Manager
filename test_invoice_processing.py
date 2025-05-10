#!/usr/bin/env python3
"""
Test script to verify invoice processing with OCR.
This script processes a sample invoice and displays the extracted data.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the Invoice_manager directory to the Python path
script_dir = Path(__file__).resolve().parent
invoice_manager_dir = script_dir / "Invoice_manager"
sys.path.insert(0, str(invoice_manager_dir))

# Import directly from the src module
try:
    from Invoice_manager.src.utils.logger import setup_logger
    from Invoice_manager.src.utils.cfg import ConfigLoader
    from Invoice_manager.src.main import InvoiceProcessor
    
    logger = setup_logger(__name__)
    
except ImportError as e:
    print(f"Error importing Invoice Manager modules: {e}")
    print("Make sure all dependencies are installed.")
    sys.exit(1)

def test_invoice_processing():
    """Test processing a sample invoice with OCR and display results."""
    print("\n=== Testing Invoice Processing ===\n")
    
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
    print("Processing invoice using standard pipeline...")
    
    try:
        # Initialize the processor directly
        processor = InvoiceProcessor()
        
        # Process the invoice using the standard process method
        result = processor.process(invoice_path)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if not result:
            print("❌ Failed to process invoice.")
            return False
        
        # Display processing results
        print(f"\n✓ Successfully processed invoice in {processing_time:.2f} seconds")
        print("\n=== Extracted Data ===")
        
        # Pretty print the extracted fields
        for key, value in result.items():
            if key != "metadata":
                print(f"{key}: {value}")
        
        print("\n=== Metadata ===")
        if "metadata" in result:
            for key, value in result["metadata"].items():
                print(f"{key}: {value}")
        
        # Save the result to a JSON file for inspection
        output_file = Path("output/test_result.json")
        os.makedirs(output_file.parent, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Full results saved to: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error during invoice processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_invoice_processing() 
#!/usr/bin/env python3
"""
Test script for MistralOCR markdown saving functionality.

This script tests the ability of the MistralOCR class to save OCR results
as markdown files in the output/ocr_markdown directory.
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

# Import after path is set up
try:
    from src.utils.logger import setup_logger
    from src.utils.cfg import ConfigLoader
    from src.ocr.mistral_wrapper import MistralOCR
    
    logger = setup_logger(__name__)
    
except ImportError as e:
    print(f"Error importing Invoice Manager modules: {e}")
    print("Make sure all dependencies are installed with:")
    print("pip install -r temp_requirements.txt")
    sys.exit(1)

def test_ocr_markdown_saving():
    """Test the OCR markdown saving functionality."""
    print("\n=== Testing Mistral OCR Markdown Saving ===\n")
    
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
        # Load config - the config is already loaded in the ConfigLoader __init__ method
        config_loader = ConfigLoader()
        config = config_loader.config  # Access the config directly
        
        # Ensure output directory exists
        output_dir = Path("output/ocr_markdown")
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Output directory created/confirmed: {output_dir}")
        
        # Initialize MistralOCR
        mistral_ocr = MistralOCR(config)
        print(f"✓ MistralOCR initialized with model: {mistral_ocr.model}")
        
        # Process the PDF with OCR
        print("Processing PDF with Mistral OCR...")
        start_time = datetime.now()
        
        # Run OCR on the PDF file
        ocr_results = mistral_ocr.run_ocr(invoice_path)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        print(f"✓ OCR processing completed in {processing_time:.2f} seconds")
        
        # Check if markdown was saved
        markdown_files = list(output_dir.glob(f"{Path(invoice_path).stem}*.md"))
        
        if markdown_files:
            most_recent_file = max(markdown_files, key=lambda p: p.stat().st_mtime)
            print(f"✓ Markdown file was successfully saved: {most_recent_file}")
            
            # Display the content of the file
            print("\n=== Preview of Saved Markdown ===\n")
            with open(most_recent_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"{content[:500]}...\n") if len(content) > 500 else print(f"{content}\n")
                
            return True
        else:
            print("❌ No markdown file was saved in the output directory.")
            return False
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_ocr_markdown_saving() 
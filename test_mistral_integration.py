#!/usr/bin/env python3
"""
Mistral OCR Integration Test

This script tests the Mistral OCR integration using the fixed client interface.
"""

import os
import sys
import base64
import json
from pathlib import Path
from datetime import datetime

# Configure path
script_dir = Path(__file__).resolve().parent
invoice_manager_dir = script_dir / "Invoice_manager"
sys.path.insert(0, str(invoice_manager_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import after path setup
try:
    from mistralai import Mistral
    from Invoice_manager.src.utils.logger import setup_logger
    from Invoice_manager.src.utils.cfg import ConfigLoader
    from Invoice_manager.src.ocr.mistral_wrapper import MistralOCR
    
    logger = setup_logger(__name__)
    
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure all dependencies are installed with:")
    print("pip install -r temp_requirements.txt")
    sys.exit(1)

def test_mistral_ocr():
    """Test the Mistral OCR functionality."""
    print("Testing Mistral OCR integration")
    
    # Get API key
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("Error: MISTRAL_API_KEY not found in environment variables")
        sys.exit(1)
    
    # Find a test image
    invoices_dir = Path("invoices")
    if not invoices_dir.exists() or not any(invoices_dir.iterdir()):
        print("Error: No invoices found in the 'invoices' directory")
        print("Please add at least one invoice file to test")
        sys.exit(1)
    
    # Get first image file
    image_files = []
    for ext in ["pdf", "jpg", "jpeg", "png"]:
        image_files.extend(list(invoices_dir.glob(f"*.{ext}")))
    
    if not image_files:
        print("Error: No image files found in invoices/ directory")
        sys.exit(1)
    
    test_image = image_files[0]
    print(f"Using test image: {test_image}")
    
    try:
        # Load configuration
        config = ConfigLoader().config
        
        # Initialize OCR wrapper
        mistral_ocr = MistralOCR(config)
        
        # Test OCR
        print("Running OCR...")
        ocr_results = mistral_ocr.run_ocr(test_image)
        
        # Get OCR text
        ocr_text = mistral_ocr.get_text_from_results(ocr_results)
        print(f"\nExtracted OCR text (first 200 chars):\n{ocr_text[:200]}...\n")
        
        # Test structured extraction
        print("Extracting structured data...")
        structured_data = mistral_ocr.extract_structured_data(test_image, ocr_text)
        
        # Save results
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"mistral_test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
        
        print(f"Extraction successful! Results saved to: {output_file}")
        if structured_data.get("metadata", {}).get("confidence_score"):
            confidence = structured_data["metadata"]["confidence_score"]
            print(f"Extraction confidence: {confidence:.2f}")
        
        extracted_fields = [field for field in structured_data.keys() if field != "metadata"]
        print(f"Extracted fields: {', '.join(extracted_fields)}")
        
        return True
        
    except Exception as e:
        print(f"Error during testing: {e}")
        return False

if __name__ == "__main__":
    success = test_mistral_ocr()
    sys.exit(0 if success else 1) 
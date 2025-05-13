#!/usr/bin/env python3
"""
Invoice Processing Test with Detailed Logging

This script runs a complete test of the invoice processing pipeline with detailed
logging for each step to help diagnose errors.
"""

import os
import sys
import argparse
import tempfile
import traceback
import json
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_error_trace.log', mode='w')
    ]
)
logger = logging.getLogger("test_error_trace")

# Add the Invoice_manager directory to the Python path
script_dir = Path(__file__).resolve().parent
invoice_manager_dir = script_dir / "Invoice_manager"
sys.path.insert(0, str(invoice_manager_dir))

# Import after path is set up
try:
    from src.utils.cfg import ConfigLoader
    from src.main import InvoiceProcessor
    from process_invoice import process_single_invoice
    
    logger.info("Successfully imported required modules")
except ImportError as e:
    logger.error(f"Error importing Invoice Manager modules: {e}")
    logger.error("Make sure all dependencies are installed with:")
    logger.error("pip install -r temp_requirements.txt")
    sys.exit(1)

def test_invoice_processing(file_path, use_mistral=True, direct_pdf=True):
    """
    Process a single invoice file with detailed logging.
    
    Args:
        file_path: Path to the invoice file
        use_mistral: Whether to use Mistral's structured extraction
        direct_pdf: Whether to use direct PDF processing for PDF files
    """
    logger.info(f"="*80)
    logger.info(f"STARTING TEST: Processing {file_path}")
    logger.info(f"="*80)
    
    start_time = datetime.now()
    
    try:
        # Check if the file exists
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return
        
        logger.info(f"File exists and is accessible: {file_path}")
        logger.info(f"File size: {file_path.stat().st_size} bytes")
        logger.info(f"File format: {file_path.suffix}")
        
        # Load config
        logger.info("Loading configuration...")
        config = ConfigLoader().config
        logger.info(f"Preprocessing enabled: {config['ocr']['preprocessing'].get('enable_preprocessing', True)}")
        logger.info(f"OCR engine: {config['ocr_engine']}")
        logger.info(f"Using Mistral structured extraction: {use_mistral}")
        logger.info(f"Using direct PDF processing: {direct_pdf}")
        
        # Initialize processor
        logger.info("Initializing invoice processor...")
        processor = InvoiceProcessor()
        logger.info("Processor initialized successfully")
        
        # Log if this is a PDF and direct processing is enabled
        is_pdf = file_path.suffix.lower() == '.pdf'
        use_direct_pdf = is_pdf and direct_pdf
        logger.info(f"Is PDF file: {is_pdf}")
        logger.info(f"Will use direct PDF processing: {use_direct_pdf}")
        
        # Start timing 
        processing_start = datetime.now()
        
        # Log the processing parameters
        logger.info(f"Processing with:")
        logger.info(f"- Mistral structured: {use_mistral}")
        logger.info(f"- Direct PDF: {direct_pdf}")
        
        # Process the invoice
        logger.info("Starting invoice processing...")
        try:
            # Try loading the file content
            with open(file_path, "rb") as f:
                content = f.read(1024)  # Read first KB to check file
                logger.info(f"Successfully read file header: {len(content)} bytes")
                
            # Process the invoice with detailed output
            result = process_single_invoice(
                str(file_path),
                use_mistral_structured=use_mistral,
                direct_pdf_processing=direct_pdf,
                format="json"  # Default to JSON format
            )
            
            processing_time = (datetime.now() - processing_start).total_seconds()
            logger.info(f"Processing completed in {processing_time:.2f} seconds")
            
            # Validate result
            if result is None:
                logger.error("Processing returned None result")
            elif not isinstance(result, dict):
                logger.error(f"Processing returned non-dictionary result: {type(result)}")
            else:
                logger.info(f"Processing successful - extracted {len(result)} fields")
                
                # Log key fields
                key_fields = ["invoice_number", "issue_date", "vendor_name", "total_amount"]
                for field in key_fields:
                    if field in result:
                        logger.info(f"Field '{field}': {result[field]}")
                    else:
                        logger.warning(f"Field '{field}' not found in result")
                
                # Log metadata if available
                if "metadata" in result:
                    logger.info("Metadata:")
                    for key, value in result["metadata"].items():
                        logger.info(f"  {key}: {value}")
                
                # Save the result to a file for inspection
                output_file = Path(f"test_result_{file_path.stem}.json")
                with open(output_file, "w") as f:
                    json.dump(result, f, indent=2, default=str)
                logger.info(f"Result saved to {output_file}")
                
        except Exception as e:
            logger.error(f"Error during processing: {e}")
            logger.error(traceback.format_exc())
    
    except Exception as e:
        logger.error(f"Test error: {e}")
        logger.error(traceback.format_exc())
    
    finally:
        total_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"="*80)
        logger.info(f"TEST COMPLETED in {total_time:.2f} seconds")
        logger.info(f"="*80)
        logger.info(f"Check test_error_trace.log for full details")

def main():
    parser = argparse.ArgumentParser(description="Test Invoice Processing with Detailed Logging")
    parser.add_argument("file", help="Path to invoice file to process")
    parser.add_argument("--standard", action="store_true", 
                      help="Use standard extraction instead of Mistral structured extraction")
    parser.add_argument("--no-direct-pdf", action="store_true",
                      help="Disable direct PDF processing (convert PDFs to images first)")
    
    args = parser.parse_args()
    
    # Determine processing options
    use_mistral = not args.standard
    direct_pdf = not args.no_direct_pdf
    
    # Run the test
    test_invoice_processing(args.file, use_mistral, direct_pdf)

if __name__ == "__main__":
    main() 
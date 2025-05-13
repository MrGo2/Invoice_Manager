#!/usr/bin/env python3
"""
Production-ready wrapper for the Invoice Manager.

This script serves as a simple entry point to process invoices using the 
full Invoice Manager pipeline. It handles path configuration to ensure
modules are imported correctly regardless of where the script is run from.
"""

import os
import sys
import argparse
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
    from src.main import InvoiceProcessor
    
    logger = setup_logger(__name__)
    
except ImportError as e:
    print(f"Error importing Invoice Manager modules: {e}")
    print("Make sure all dependencies are installed with:")
    print("pip install -r temp_requirements.txt")
    sys.exit(1)

def process_single_invoice(invoice_path, output_path=None, format="json", config_path=None, 
                           use_mistral_structured=True, direct_pdf_processing=True):
    """
    Process a single invoice file.
    
    Args:
        invoice_path: Path to the invoice file
        output_path: Path to save the output
        format: Output format (json or csv)
        config_path: Path to custom config file
        use_mistral_structured: Whether to use Mistral's structured extraction
        direct_pdf_processing: Whether to use direct PDF processing for PDF files
        
    Returns:
        A dictionary containing the structured invoice data or error information
    """
    try:
        # Initialize processor
        processor = InvoiceProcessor(config_path)
        
        # Check if preprocessing is enabled in the config
        preprocessing_enabled = processor.config["ocr"]["preprocessing"].get("enable_preprocessing", True)
        if not preprocessing_enabled:
            print("Image preprocessing is disabled in config.")
        
        # Process invoice
        print(f"Processing invoice: {invoice_path}")
        invoice_path = Path(invoice_path)
        
        # Check if this is a PDF and direct processing is enabled
        is_pdf = invoice_path.suffix.lower() == '.pdf'
        use_direct_pdf = is_pdf and direct_pdf_processing
        
        if use_mistral_structured:
            # Use the enhanced Mistral OCR + structured extraction
            start_time = datetime.now()
            
            # Initialize variables to avoid UnboundLocalError
            preprocessed_images = None
            ocr_results = None
            structured_data = None
            
            if use_direct_pdf:
                # For PDFs, use direct Mistral OCR processing without conversion to images
                print("Using direct PDF processing with Mistral OCR")
                
                # Run OCR directly on the PDF file
                ocr_results = processor.mistral_ocr.run_ocr(str(invoice_path))
                
                # Extract structured data directly from the PDF
                structured_data = processor.mistral_ocr.extract_structured_data(
                    str(invoice_path)  # We don't need to pass OCR text when using native OCR
                )
                
            else:
                # For images or when direct PDF processing is disabled, use the standard flow
                # 1. Preprocess the image (this converts PDFs to images)
                preprocessed_images = processor.image_processor.process(str(invoice_path))
                if not preprocessed_images:
                    raise RuntimeError("Failed to preprocess invoice images")
                    
                # 2. Run OCR on the first preprocessed image
                ocr_results = processor.mistral_ocr.run_ocr(preprocessed_images[0])
                ocr_text = processor.mistral_ocr.get_text_from_results(ocr_results)
            
                # 3. Use Mistral's structured extraction capability
                structured_data = processor.mistral_ocr.extract_structured_data(
                    preprocessed_images[0], 
                    ocr_text
                )
            
            # Check if structured_data was successfully generated
            if not structured_data or not isinstance(structured_data, dict):
                raise ValueError(f"Failed to extract structured data. Result: {structured_data}")
                
            # 4. Validate the structured data
            is_valid = processor.validator.validate(structured_data)
            
            if not is_valid and len(structured_data) < 5:
                print("Structured extraction produced limited results. Falling back to standard pipeline.")
                result = processor.process(str(invoice_path))
            else:
                # Add additional metadata
                if "metadata" not in structured_data:
                    structured_data["metadata"] = {}
                    
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                method = "mistral_direct_pdf" if use_direct_pdf else "mistral_structured"
                
                structured_data["metadata"].update({
                    "source_file": invoice_path.name,
                    "processing_duration_ms": int(processing_time),
                    "extraction_method": method,
                    "preprocessing_enabled": preprocessing_enabled
                })
                
                result = structured_data
                print(f"Successfully extracted {len(result) - 1} fields using Mistral" + 
                      (" direct PDF processing" if use_direct_pdf else " structured extraction"))
        else:
            # Use the standard processing pipeline
            result = processor.process(str(invoice_path))
            
            # Check if result is valid
            if not result or not isinstance(result, dict):
                raise ValueError(f"Standard processing pipeline failed. Result: {result}")
        
        # Export result
        if output_path:
            output_file = processor.export(result, format=format, output_path=output_path)
            print(f"Result saved to: {output_file}")
        else:
            # Default output location
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            invoice_name = invoice_path.stem
            default_output = output_dir / f"{invoice_name}_result.{format}"
            output_file = processor.export(result, format=format, output_path=str(default_output))
            print(f"Result saved to: {output_file}")
            
        return result
        
    except Exception as e:
        print(f"Error processing invoice: {e}")
        import traceback
        traceback.print_exc()
        
        # Return a structured error response instead of None
        error_result = {
            "invoice_number": "ERROR",
            "issue_date": "ERROR",
            "vendor_name": "ERROR",
            "total_amount": "ERROR",
            "metadata": {
                "source_file": Path(invoice_path).name if 'invoice_path' in locals() else "unknown",
                "ocr_engine": "error",
                "confidence_score": 0.0,
                "error": str(e),
                "error_type": type(e).__name__
            }
        }
        return error_result

def batch_process_invoices(directory_path, output_dir=None, format="json", config_path=None, 
                          use_mistral_structured=True, direct_pdf_processing=True):
    """
    Process all invoices in a directory.
    
    Args:
        directory_path: Path to directory containing invoices
        output_dir: Directory to save output files
        format: Output format (json or csv)
        config_path: Path to custom config file
        use_mistral_structured: Whether to use Mistral's structured extraction
        direct_pdf_processing: Whether to use direct PDF processing for PDF files
        
    Returns:
        A list of structured invoice data dictionaries or an error result dictionary
    """
    try:
        # Initialize processor
        processor = InvoiceProcessor(config_path)
        
        # Create default output directory if needed
        if not output_dir:
            output_dir = Path("output")
        else:
            output_dir = Path(output_dir)
            
        output_dir.mkdir(exist_ok=True)
        
        # Get list of invoice files
        directory = Path(directory_path)
        supported_formats = processor.config["input"]["allowed_formats"]
        invoice_files = []
        
        for file_format in supported_formats:
            invoice_files.extend(list(directory.glob(f"*.{file_format}")))
        
        if not invoice_files:
            print(f"No supported invoice files found in {directory_path}")
            return []
            
        print(f"Found {len(invoice_files)} invoice files to process")
        
        # Process each invoice
        results = []
        for invoice_file in invoice_files:
            try:
                invoice_name = invoice_file.stem
                output_file = output_dir / f"{invoice_name}_result.{format}"
                
                result = process_single_invoice(
                    str(invoice_file),
                    output_path=str(output_file),
                    format=format,
                    config_path=config_path,
                    use_mistral_structured=use_mistral_structured,
                    direct_pdf_processing=direct_pdf_processing
                )
                
                if result:
                    results.append(result)
                    
            except Exception as e:
                print(f"Error processing {invoice_file}: {e}")
                continue
            
        print(f"Processed {len(results)} invoices. Results saved to {output_dir}/")
        return results
        
    except Exception as e:
        print(f"Error batch processing invoices: {e}")
        import traceback
        traceback.print_exc()
        
        # Return a structured error response instead of None
        error_result = [{
            "invoice_number": "BATCH_ERROR",
            "issue_date": "ERROR",
            "vendor_name": "ERROR",
            "total_amount": "ERROR",
            "metadata": {
                "source_directory": str(directory_path) if 'directory_path' in locals() else "unknown",
                "error": str(e),
                "error_type": type(e).__name__
            }
        }]
        return error_result

def main():
    """Parse command line arguments and call appropriate processing function."""
    parser = argparse.ArgumentParser(description="Production-ready Invoice Manager")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process a single invoice")
    process_parser.add_argument("invoice", help="Path to invoice file")
    process_parser.add_argument("--output", "-o", help="Output file path")
    process_parser.add_argument("--format", "-f", choices=["json", "csv"], default="json", help="Output format")
    process_parser.add_argument("--config", "-c", help="Path to custom config file")
    process_parser.add_argument("--standard", action="store_true", 
                              help="Use standard extraction instead of Mistral structured extraction")
    process_parser.add_argument("--no-direct-pdf", action="store_true",
                              help="Disable direct PDF processing (convert PDFs to images first)")
    
    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Process multiple invoices")
    batch_parser.add_argument("directory", help="Directory containing invoices")
    batch_parser.add_argument("--output", "-o", help="Output directory path")
    batch_parser.add_argument("--format", "-f", choices=["json", "csv"], default="json", help="Output format")
    batch_parser.add_argument("--config", "-c", help="Path to custom config file")
    batch_parser.add_argument("--standard", action="store_true", 
                            help="Use standard extraction instead of Mistral structured extraction")
    batch_parser.add_argument("--no-direct-pdf", action="store_true",
                            help="Disable direct PDF processing (convert PDFs to images first)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Determine whether to use Mistral structured extraction
    use_mistral_structured = not getattr(args, "standard", False)
    
    # Determine whether to use direct PDF processing
    direct_pdf_processing = not getattr(args, "no_direct_pdf", False)
    
    if args.command == "process":
        process_single_invoice(
            args.invoice, 
            output_path=args.output, 
            format=args.format, 
            config_path=args.config,
            use_mistral_structured=use_mistral_structured,
            direct_pdf_processing=direct_pdf_processing
        )
    elif args.command == "batch":
        batch_process_invoices(
            args.directory, 
            output_dir=args.output, 
            format=args.format, 
            config_path=args.config,
            use_mistral_structured=use_mistral_structured,
            direct_pdf_processing=direct_pdf_processing
        )

if __name__ == "__main__":
    main() 
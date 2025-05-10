#!/usr/bin/env python3
"""
Invoice Processor - Main Entry Point

This module provides both CLI and API interfaces for the Invoice Processor application.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

from src.ocr.confidence_merger import OCRMerger
from src.ocr.mistral_wrapper import MistralOCR
from src.ocr.tesseract_fallback import TesseractOCR
from src.preprocessing.image_processor import ImageProcessor
from src.extraction.field_locator import FieldLocator
from src.extraction.openai_refiner import OpenAIRefiner
from src.validation.schema_validator import SchemaValidator
from src.export.writers import JSONWriter, CSVWriter, WebhookWriter
from src.utils.logger import setup_logger
from src.utils.cfg import ConfigLoader

# Set up logger
logger = setup_logger(__name__)


class InvoiceProcessor:
    """Main class for processing invoices and extracting data."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the invoice processor with configuration.
        
        Args:
            config_path: Optional path to a custom config file.
        """
        self.config = ConfigLoader(config_path).config
        self.image_processor = ImageProcessor(self.config)
        self.mistral_ocr = MistralOCR(self.config)
        self.tesseract_ocr = TesseractOCR(self.config)
        self.ocr_merger = OCRMerger(self.config)
        self.field_locator = FieldLocator(self.config)
        self.openai_refiner = OpenAIRefiner(self.config)
        self.validator = SchemaValidator(self.config)
        
        # Set up exporters
        self.exporters = {
            "json": JSONWriter(),
            "csv": CSVWriter(),
            "webhook": WebhookWriter(self.config)
        }
        
        logger.info("Invoice Processor initialized")

    def process(self, file_path: Union[str, Path]) -> Dict:
        """
        Process a single invoice file and extract structured data.
        
        Args:
            file_path: Path to the invoice file (PDF, JPG, PNG)
            
        Returns:
            Dict containing the extracted and validated invoice data
        """
        file_path = Path(file_path)
        logger.info(f"Processing invoice: {file_path}")
        
        # Step 1: Preprocess the image
        processed_images = self.image_processor.process(file_path)
        
        # Step 2: Perform OCR with primary and fallback engines
        all_results = []
        for i, image in enumerate(processed_images):
            logger.debug(f"OCR processing page {i+1}/{len(processed_images)}")
            
            # Primary OCR with Mistral
            mistral_results = self.mistral_ocr.run_ocr(image)
            
            # Fallback OCR with Tesseract if enabled
            tesseract_results = None
            if self.config["tesseract_fallback"]:
                tesseract_results = self.tesseract_ocr.run_ocr(image)
            
            # Merge OCR results if both are available
            if tesseract_results:
                merged_results = self.ocr_merger.merge(mistral_results, tesseract_results)
                all_results.append(merged_results)
            else:
                all_results.append(mistral_results)
        
        # Step 3: Perform field detection with heuristics
        ocr_text = "\n".join([" ".join([word["text"] for word in page]) for page in all_results])
        initial_fields = self.field_locator.extract_fields(ocr_text)
        
        # Step 4: Refine with OpenAI
        refined_data = self.openai_refiner.refine(ocr_text, initial_fields)
        
        # Step 5: Validate against schema
        validated_data = self.validator.validate(refined_data)
        
        # Add metadata
        validated_data["metadata"] = {
            "source_file": file_path.name,
            "ocr_engine": "hybrid" if self.config["tesseract_fallback"] else "mistral",
            "extraction_timestamp": self.openai_refiner.last_timestamp,
            "confidence_score": self.ocr_merger.last_confidence
        }
        
        logger.info(f"Successfully processed invoice: {file_path}")
        return validated_data
    
    def batch_process(self, directory_path: Union[str, Path]) -> List[Dict]:
        """
        Process all invoice files in a directory.
        
        Args:
            directory_path: Path to directory containing invoice files
            
        Returns:
            List of dictionaries containing extracted and validated data
        """
        directory_path = Path(directory_path)
        logger.info(f"Batch processing invoices in: {directory_path}")
        
        results = []
        allowed_extensions = self.config["input"]["allowed_formats"]
        
        for file_path in directory_path.iterdir():
            if file_path.suffix.lower()[1:] in allowed_extensions:
                try:
                    result = self.process(file_path)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {str(e)}")
        
        logger.info(f"Batch processing complete. Processed {len(results)} invoices.")
        return results
    
    def export(self, data: Union[Dict, List[Dict]], format: str = None, output_path: Optional[str] = None) -> str:
        """
        Export the extracted data in the specified format.
        
        Args:
            data: Invoice data to export (single invoice or list)
            format: Output format (json, csv, webhook)
            output_path: Path to save the exported data
            
        Returns:
            Path to the exported file or confirmation message
        """
        format = format or self.config["export"]["default_format"]
        
        if format not in self.exporters:
            raise ValueError(f"Unsupported export format: {format}")
        
        return self.exporters[format].write(data, output_path)


def main():
    """Command-line interface for the Invoice Processor."""
    parser = argparse.ArgumentParser(description="Invoice Processor - Extract data from Spanish invoices")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Process single invoice
    process_parser = subparsers.add_parser("process", help="Process a single invoice")
    process_parser.add_argument("file", help="Path to the invoice file")
    process_parser.add_argument("--output", "-o", help="Output file path")
    process_parser.add_argument("--format", "-f", choices=["json", "csv", "webhook"], default="json", help="Output format")
    process_parser.add_argument("--config", "-c", help="Path to custom config file")
    
    # Batch process invoices
    batch_parser = subparsers.add_parser("batch", help="Process multiple invoices in a directory")
    batch_parser.add_argument("directory", help="Directory containing invoice files")
    batch_parser.add_argument("--output", "-o", help="Output directory path")
    batch_parser.add_argument("--format", "-f", choices=["json", "csv", "webhook"], default="json", help="Output format")
    batch_parser.add_argument("--config", "-c", help="Path to custom config file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    processor = InvoiceProcessor(args.config if hasattr(args, "config") else None)
    
    if args.command == "process":
        result = processor.process(args.file)
        output = processor.export(result, args.format, args.output)
        print(f"Invoice processed successfully. Output: {output}")
    
    elif args.command == "batch":
        results = processor.batch_process(args.directory)
        output = processor.export(results, args.format, args.output)
        print(f"Batch processing complete. Processed {len(results)} invoices. Output: {output}")


if __name__ == "__main__":
    main() 
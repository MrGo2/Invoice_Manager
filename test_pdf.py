#!/usr/bin/env python3
"""
Simple test script to process a PDF file using pdf2image and pytesseract.
This is a basic version that doesn't use the full Invoice Manager application.
"""

import os
import sys
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
import json

def process_pdf(pdf_path):
    """Process a PDF file and extract text using pytesseract."""
    print(f"Processing PDF: {pdf_path}")
    
    try:
        # Convert PDF to images
        print("Converting PDF to images...")
        images = convert_from_path(pdf_path, dpi=300)
        print(f"Converted PDF to {len(images)} page(s)")
        
        # Extract text from each page
        all_text = []
        for i, image in enumerate(images):
            print(f"Processing page {i+1}/{len(images)}...")
            text = pytesseract.image_to_string(image, lang='spa')
            all_text.append(text)
            
        # Combine text from all pages
        full_text = "\n\n".join(all_text)
        
        # Save the extracted text
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        pdf_name = Path(pdf_path).stem
        output_path = output_dir / f"{pdf_name}_text.txt"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_text)
            
        print(f"Extracted text saved to: {output_path}")
        
        # Display a preview of the extracted text
        preview_length = min(500, len(full_text))
        print("\nPreview of extracted text:")
        print("-" * 50)
        print(full_text[:preview_length] + "..." if len(full_text) > preview_length else full_text)
        print("-" * 50)
        
        return full_text
        
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return None

def main():
    """Main function to process a PDF file."""
    # Check command line arguments
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Default to the invoice-5.pdf in the invoices directory
        pdf_path = "invoices/invoice-5.pdf"
    
    # Check if the file exists
    if not Path(pdf_path).exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    # Process the PDF
    process_pdf(pdf_path)

if __name__ == "__main__":
    main() 
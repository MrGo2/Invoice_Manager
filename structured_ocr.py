#!/usr/bin/env python3
"""
Structured OCR processing example using Mistral OCR API.
This script demonstrates how to process PDF and image files through OCR 
and extract structured data.
"""

import os
import json
import base64
from pathlib import Path
from mistralai import Mistral, DocumentURLChunk, ImageURLChunk, TextChunk
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Mistral client with API key from environment
api_key = os.environ.get("MISTRAL_API_KEY")
if not api_key:
    raise ValueError("MISTRAL_API_KEY environment variable not set")

client = Mistral(api_key=api_key)

def process_pdf_with_ocr(pdf_path):
    """Process a PDF file with Mistral OCR and return the results"""
    print(f"Processing PDF: {pdf_path}")
    
    # Verify PDF file exists
    pdf_file = Path(pdf_path)
    if not pdf_file.is_file():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
    # Upload PDF file to Mistral's OCR service
    uploaded_file = client.files.upload(
        file={
            "file_name": pdf_file.stem,
            "content": pdf_file.read_bytes(),
        },
        purpose="ocr",
    )
    
    # Get URL for the uploaded file
    signed_url = client.files.get_signed_url(file_id=uploaded_file.id)
    
    # Process PDF with OCR
    pdf_response = client.ocr.process(
        document=DocumentURLChunk(document_url=signed_url.url),
        model="mistral-ocr-latest",
        include_image_base64=True
    )
    
    # Print summary of results
    total_text = ""
    for i, page in enumerate(pdf_response.pages):
        page_text = page.markdown
        total_text += page_text
        print(f"Page {i+1}: Extracted {len(page_text.split())} words")
        
    print(f"Total: Extracted {len(total_text.split())} words from {len(pdf_response.pages)} pages")
    return pdf_response

def process_image_with_ocr(image_path):
    """Process an image file with Mistral OCR and return the results"""
    print(f"Processing image: {image_path}")
    
    # Verify image exists
    image_file = Path(image_path)
    if not image_file.is_file():
        raise FileNotFoundError(f"Image file not found: {image_path}")
        
    # Encode image as base64 for API
    encoded = base64.b64encode(image_file.read_bytes()).decode()
    base64_data_url = f"data:image/jpeg;base64,{encoded}"
    
    # Process image with OCR
    image_response = client.ocr.process(
        document=ImageURLChunk(image_url=base64_data_url),
        model="mistral-ocr-latest"
    )
    
    # Print summary
    page_text = image_response.pages[0].markdown
    print(f"Extracted {len(page_text.split())} words from image")
    
    return image_response

def extract_structured_data(ocr_response, image_url=None):
    """Extract structured data from OCR results using Mistral models"""
    print("Extracting structured data from OCR results...")
    
    # Get OCR text from the first page
    ocr_markdown = ocr_response.pages[0].markdown
    
    # Create content list based on whether we have an image
    content = []
    if image_url:
        content.append(ImageURLChunk(image_url=image_url))
    
    content.append(TextChunk(
        text=(
            f"This is OCR text in markdown:\n\n{ocr_markdown}\n\n"
            "Convert this into a JSON structure with the following fields:\n"
            "- document_type: type of document (invoice, receipt, etc.)\n"
            "- date: date on the document\n"
            "- total_amount: total amount with currency\n"
            "- vendor: issuing company/merchant\n"
            "- line_items: array of items with descriptions and prices\n"
            "- payment_method: payment method if available\n"
            "The output should be strictly valid JSON with no extra commentary."
        )
    ))
    
    # Use the appropriate model based on whether we have an image
    model = "pixtral-12b-latest" if image_url else "mistral-large-latest"
    
    # Get structured response from model
    chat_response = client.chat.complete(
        model=model,
        messages=[{"role": "user", "content": content}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    
    # Parse and return JSON response
    response_dict = json.loads(chat_response.choices[0].message.content)
    return response_dict

class StructuredOCR(BaseModel):
    file_name: str
    topics: list[str]
    languages: str
    ocr_contents: dict

def structured_ocr(image_path: str) -> StructuredOCR:
    """
    Process an image using OCR and extract structured data.
    
    Args:
        image_path: Path to the image file to process
        
    Returns:
        StructuredOCR object containing the extracted data
    """
    # Validate input file
    image_file = Path(image_path)
    if not image_file.is_file():
        raise FileNotFoundError("The provided image path does not exist.")
        
    # Read and encode the image file
    encoded_image = base64.b64encode(image_file.read_bytes()).decode()
    base64_data_url = f"data:image/jpeg;base64,{encoded_image}"
    
    # Process the image using OCR
    image_response = client.ocr.process(
        document=ImageURLChunk(image_url=base64_data_url),
        model="mistral-ocr-latest"
    )
    image_ocr_markdown = image_response.pages[0].markdown
    
    # Parse the OCR result into a structured format
    try:
        chat_response = client.chat.parse(
            model="pixtral-12b-latest",
            messages=[
                {
                    "role": "user",
                    "content": [
                        ImageURLChunk(image_url=base64_data_url),
                        TextChunk(text=(
                            f"This is the image's OCR in markdown:\n{image_ocr_markdown}\n.\n"
                            "Convert this into a structured JSON response "
                            "with the OCR contents in a sensible dictionary."
                            )
                        )
                    ]
                }
            ],
            response_format=StructuredOCR,
            temperature=0
        )
        
        return chat_response.choices[0].message.parsed
    except Exception as e:
        print(f"Error parsing structured data: {str(e)}")
        # Fallback to normal completion if parse fails
        chat_response = client.chat.complete(
            model="pixtral-12b-latest",
            messages=[
                {
                    "role": "user",
                    "content": [
                        ImageURLChunk(image_url=base64_data_url),
                        TextChunk(text=(
                            f"This is the image's OCR in markdown:\n{image_ocr_markdown}\n.\n"
                            "Convert this into a structured JSON response with fields:\n"
                            "- file_name: the name of the file\n"
                            "- topics: list of topics in the document\n"
                            "- languages: languages detected\n"
                            "- ocr_contents: dictionary with structured content\n\n"
                            "The output should be strictly valid JSON with no extra commentary."
                            )
                        )
                    ]
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        response_dict = json.loads(chat_response.choices[0].message.content)
        return StructuredOCR(**response_dict)

def main():
    """Main function to demonstrate OCR processing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Process files with Mistral OCR")
    parser.add_argument("file_path", help="Path to the PDF or image file")
    parser.add_argument("--structured", action="store_true", help="Extract structured data")
    parser.add_argument("--output", help="Output file for results (JSON)")
    args = parser.parse_args()
    
    file_path = args.file_path
    file_ext = Path(file_path).suffix.lower()
    
    try:
        # Process based on file type
        if file_ext == ".pdf":
            ocr_response = process_pdf_with_ocr(file_path)
            
            # Extract structured data if requested
            if args.structured:
                structured_data = extract_structured_data(ocr_response)
                print("\nStructured Data:")
                print(json.dumps(structured_data, indent=2))
                
                # Save to output file if specified
                if args.output:
                    with open(args.output, "w", encoding="utf-8") as f:
                        json.dump(structured_data, f, indent=2, ensure_ascii=False)
                    print(f"Results saved to {args.output}")
            
        elif file_ext in [".jpg", ".jpeg", ".png", ".tiff", ".tif"]:
            # For images, use the structured_ocr function directly if --structured is set
            if args.structured:
                image_file = Path(file_path)
                encoded = base64.b64encode(image_file.read_bytes()).decode()
                base64_data_url = f"data:image/jpeg;base64,{encoded}"
                
                # First get OCR response
                ocr_response = process_image_with_ocr(file_path)
                
                # Then extract structured data
                structured_data = extract_structured_data(ocr_response, base64_data_url)
                print("\nStructured Data:")
                print(json.dumps(structured_data, indent=2))
                
                # Save to output file if specified
                if args.output:
                    with open(args.output, "w", encoding="utf-8") as f:
                        json.dump(structured_data, f, indent=2, ensure_ascii=False)
                    print(f"Results saved to {args.output}")
            else:
                # Just process the image with OCR
                ocr_response = process_image_with_ocr(file_path)
        else:
            print(f"Unsupported file format: {file_ext}")
            return
            
    except Exception as e:
        print(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()


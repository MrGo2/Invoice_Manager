#!/usr/bin/env python3
"""
Test OCR functionality with a sample image using Mistral API.
"""

import os
import sys
import base64
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_mistral_ocr():
    """
    Test OCR functionality using Mistral API's OCR model.
    
    We'll check if we can send an OCR request to the API and get a response.
    Note: This requires a valid Mistral API key with access to OCR models.
    """
    try:
        # Import Mistral client
        from mistralai import Mistral
        
        # Get API key from environment
        mistral_api_key = os.environ.get("MISTRAL_API_KEY")
        if not mistral_api_key:
            print("❌ MISTRAL_API_KEY environment variable not found.")
            return False
        
        # Initialize Mistral client
        client = Mistral(api_key=mistral_api_key)
        
        # Check if sample image exists (if not, we'll need to provide instructions)
        sample_path = Path("sample_invoice.jpg")  # Change this if you have a different file
        
        if not sample_path.exists():
            print(f"❌ Sample image not found: {sample_path}")
            print("Please provide a sample image file to test OCR functionality.")
            return False
        
        # Convert image to base64
        with open(sample_path, "rb") as img_file:
            img_data = img_file.read()
            base64_image = base64.b64encode(img_data).decode('utf-8')
        
        print(f"✓ Successfully loaded sample image: {sample_path}")
        
        # Create OCR request
        try:
            response = client.ocr.process(
                model="mistral-ocr-latest",  
                document={
                    "type": "document_base64",
                    "document_base64": base64_image
                }
            )
            
            # Output result
            text = response.text
            print("✓ Successfully processed image with OCR")
            print("\nExtracted text:")
            print("-" * 50)
            print(text[:500] + "..." if len(text) > 500 else text)
            print("-" * 50)
            
            # Output confidence score
            confidence = response.confidence
            print(f"Confidence score: {confidence:.2f}")
            
            return True
            
        except Exception as e:
            print(f"❌ OCR processing failed: {str(e)}")
            return False
            
    except ImportError:
        print("❌ Required package not found. Install with 'pip install mistralai'")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_openai_ocr():
    """
    Test OCR functionality using OpenAI's Vision API as an alternative.
    
    This doesn't provide OCR specifically but can analyze images and extract text.
    """
    try:
        # Import OpenAI client
        from openai import OpenAI
        import base64
        
        # Get API key from environment
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            print("❌ OPENAI_API_KEY environment variable not found.")
            return False
        
        # Initialize OpenAI client
        client = OpenAI(api_key=openai_api_key)
        
        # Check if sample image exists
        sample_path = Path("sample_invoice.jpg")  # Change this if you have a different file
        
        if not sample_path.exists():
            print(f"❌ Sample image not found: {sample_path}")
            print("Please provide a sample image file to test Vision API functionality.")
            return False
        
        # Convert image to base64
        with open(sample_path, "rb") as img_file:
            img_data = img_file.read()
            base64_image = base64.b64encode(img_data).decode('utf-8')
        
        print(f"✓ Successfully loaded sample image: {sample_path}")
        
        # Create Vision API request
        try:
            response = client.responses.create(
                model="gpt-4o",  # Vision capabilities
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": "Extract all text from this invoice image. Return just the text content, don't analyze it."},
                            {"type": "input_image", "image_url": f"data:image/jpeg;base64,{base64_image}"}
                        ]
                    }
                ]
            )
            
            # Output result
            text = response.output_text  # Get the text output
            print("✓ Successfully processed image with OpenAI Vision API")
            print("\nExtracted text:")
            print("-" * 50)
            print(text[:500] + "..." if len(text) > 500 else text)
            print("-" * 50)
            
            return True
            
        except Exception as e:
            print(f"❌ Vision API processing failed: {str(e)}")
            return False
            
    except ImportError:
        print("❌ Required package not found. Install with 'pip install openai'")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing OCR functionality...")
    
    # First check for sample image
    sample_path = Path("sample_invoice.jpg")
    if not sample_path.exists():
        print(f"\n⚠️ Sample image not found: {sample_path}")
        print("You need a sample image to test OCR functionality.")
        print("Please add a sample invoice image named 'sample_invoice.jpg' to the current directory.")
        print("After adding the image, run this script again.")
        sys.exit(1)
    
    print("\n--- Testing Mistral OCR ---")
    mistral_ocr_success = test_mistral_ocr()
    
    print("\n--- Testing OpenAI Vision API for OCR ---")
    openai_ocr_success = test_openai_ocr()
    
    # Summary
    print("\n=== Summary ===")
    print(f"Mistral OCR: {'✓ Working' if mistral_ocr_success else '❌ Failed'}")
    print(f"OpenAI Vision API: {'✓ Working' if openai_ocr_success else '❌ Failed'}")
    
    if mistral_ocr_success or openai_ocr_success:
        print("\n✅ OCR functionality is available through at least one provider.")
        sys.exit(0)
    else:
        print("\n❌ Both OCR providers failed. Check the errors above for details.")
        sys.exit(1) 
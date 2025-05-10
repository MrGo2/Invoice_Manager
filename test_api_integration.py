#!/usr/bin/env python3
"""
API Integration Test Script

This script tests the API integrations for Mistral OCR and OpenAI,
and logs the findings and outputs to a file.
"""

import os
import sys
import json
import base64
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"api_test_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("api_test")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class APITester:
    """Tests API integrations for Mistral OCR and OpenAI."""
    
    def __init__(self):
        """Initialize API tester."""
        self.mistral_api_key = os.environ.get("MISTRAL_API_KEY")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        
        if not self.mistral_api_key:
            logger.error("MISTRAL_API_KEY not found in environment variables")
        else:
            logger.info(f"MISTRAL_API_KEY found: {self.mistral_api_key[:5]}{'*' * 10}")
            
        if not self.openai_api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
        else:
            logger.info(f"OPENAI_API_KEY found: {self.openai_api_key[:5]}{'*' * 10}")
        
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "mistral_connection": False,
            "openai_connection": False,
            "mistral_ocr_test": False,
            "mistral_structured_extraction": False,
            "openai_extraction": False,
            "tests": []
        }
        
        # Add the Invoice_manager directory to the Python path if needed
        script_dir = Path(__file__).resolve().parent
        invoice_manager_dir = script_dir / "Invoice_manager"
        if invoice_manager_dir.exists():
            sys.path.insert(0, str(invoice_manager_dir))
            logger.info(f"Added {invoice_manager_dir} to Python path")
    
    def test_mistral_connection(self) -> bool:
        """Test connection to Mistral API."""
        logger.info("Testing Mistral API connection...")
        test_name = "Mistral API Connection"
        
        try:
            from mistralai import Mistral
            
            client = Mistral(api_key=self.mistral_api_key)
            
            # Simple chat completion to test connection
            response = client.chat(
                model="mistral-tiny",
                messages=[{"role": "user", "content": "Hello, are you working?"}],
                max_tokens=10
            )
            
            message = response.choices[0].message.content
            logger.info(f"Mistral API response: {message}")
            
            self._add_test_result(test_name, True, {"response": message})
            self.test_results["mistral_connection"] = True
            return True
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error connecting to Mistral API: {error_message}")
            self._add_test_result(test_name, False, {"error": error_message})
            return False
    
    def test_openai_connection(self) -> bool:
        """Test connection to OpenAI API."""
        logger.info("Testing OpenAI API connection...")
        test_name = "OpenAI API Connection"
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            # Simple chat completion to test connection
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello, are you working?"}],
                max_tokens=10
            )
            
            message = response.choices[0].message.content
            logger.info(f"OpenAI API response: {message}")
            
            self._add_test_result(test_name, True, {"response": message})
            self.test_results["openai_connection"] = True
            return True
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error connecting to OpenAI API: {error_message}")
            self._add_test_result(test_name, False, {"error": error_message})
            return False
    
    def test_mistral_ocr(self, image_path: Union[str, Path]) -> bool:
        """Test Mistral OCR on an image."""
        logger.info(f"Testing Mistral OCR with image: {image_path}")
        test_name = "Mistral OCR Test"
        
        try:
            from mistralai import Mistral
            
            client = Mistral(api_key=self.mistral_api_key)
            
            # Check if image exists
            image_path = Path(image_path)
            if not image_path.is_file():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Encode image as base64
            with open(image_path, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode()
            
            # Process using Mistral Vision Model
            start_time = time.time()
            
            # Call Mistral API with vision capability
            response = client.chat(
                model="mistral-large-vision-latest",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract all text from this image, exactly as written."},
                            {"type": "image", "image": encoded}
                        ]
                    }
                ]
            )
            
            ocr_text = response.choices[0].message.content
            ocr_confidence = 0.9  # Estimated since vision model doesn't provide confidence
            
            processing_time = time.time() - start_time
            logger.info(f"OCR processing time: {processing_time:.2f} seconds")
            logger.info(f"Vision model OCR text (first 100 chars): {ocr_text[:100]}...")
            
            # Save OCR text to output file
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            output_file = output_dir / f"{image_path.stem}_ocr.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(ocr_text)
            
            logger.info(f"OCR text saved to {output_file}")
            
            self._add_test_result(
                test_name, 
                True, 
                {
                    "ocr_text_sample": ocr_text[:200] + ("..." if len(ocr_text) > 200 else ""),
                    "confidence": ocr_confidence,
                    "processing_time": processing_time,
                    "output_file": str(output_file)
                }
            )
            self.test_results["mistral_ocr_test"] = True
            return True
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error running Mistral OCR: {error_message}")
            self._add_test_result(test_name, False, {"error": error_message})
            return False
    
    def test_mistral_structured_extraction(self, image_path: Union[str, Path], schema_path: Union[str, Path]) -> bool:
        """Test Mistral structured data extraction."""
        logger.info(f"Testing Mistral structured extraction with image: {image_path}")
        test_name = "Mistral Structured Extraction"
        
        try:
            from mistralai import Mistral
            
            client = Mistral(api_key=self.mistral_api_key)
            
            # Check if files exist
            image_path = Path(image_path)
            schema_path = Path(schema_path)
            
            if not image_path.is_file():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            if not schema_path.is_file():
                raise FileNotFoundError(f"Schema file not found: {schema_path}")
            
            # Load schema
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            
            # Simplify schema for prompt
            schema_description = {}
            for key, value in schema.get("properties", {}).items():
                if not key.startswith("//") and not key == "metadata":
                    schema_description[key] = value.get("description", "")
            
            # Encode image
            with open(image_path, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode()
            
            # First get OCR text (using vision model for simplicity)
            logger.info("Getting OCR text first...")
            
            ocr_response = client.chat(
                model="mistral-large-vision-latest",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract all text from this image, exactly as written."},
                            {"type": "image", "image": encoded}
                        ]
                    }
                ]
            )
            
            ocr_text = ocr_response.choices[0].message.content
            logger.info(f"Extracted OCR text (first 100 chars): {ocr_text[:100]}...")
            
            # Now extract structured data using text-only model
            logger.info("Extracting structured data with text model...")
            
            prompt = (
                "Extract structured data from this Spanish invoice OCR text according to this schema:\n\n"
                f"{json.dumps(schema_description, indent=2)}\n\n"
                "The OCR text of the invoice is:\n\n"
                f"{ocr_text}\n\n"
                "Return ONLY a valid JSON object with the extracted fields according to the schema. "
                "For Spanish invoices, look for fields like: 'Factura', 'Número', 'Fecha', 'NIF/CIF', "
                "'Emisor', 'Destinatario', 'Base Imponible', 'IVA', etc."
            )
            
            text_response = client.chat(
                model="mistral-medium",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0
            )
            
            structured_data = json.loads(text_response.choices[0].message.content)
            
            logger.info(f"Extracted {len(structured_data)} fields from text model")
            
            # Try vision model for any missing fields
            required_fields = schema.get("required", [])
            missing_fields = [field for field in required_fields 
                             if field not in structured_data or not structured_data[field]]
            
            if missing_fields:
                logger.info(f"Missing fields: {missing_fields}. Trying vision model...")
                
                vision_prompt = (
                    "This is a Spanish invoice image. Extract structured data according to this schema:\n\n"
                    f"{json.dumps(schema_description, indent=2)}\n\n"
                    "For reference, this is the OCR text already extracted:\n\n"
                    f"{ocr_text[:500]}...\n\n"
                    "Return ONLY a valid JSON object with the extracted fields. Pay special attention to "
                    f"these missing fields: {', '.join(missing_fields)}."
                )
                
                vision_response = client.chat(
                    model="mistral-large-vision-latest",
                    messages=[
                        {
                            "role": "user", 
                            "content": [
                                {"type": "text", "text": vision_prompt},
                                {"type": "image", "image": encoded}
                            ]
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0
                )
                
                vision_data = json.loads(vision_response.choices[0].message.content)
                logger.info(f"Extracted {len(vision_data)} fields from vision model")
                
                # Merge results
                for field in missing_fields:
                    if field in vision_data and vision_data[field]:
                        structured_data[field] = vision_data[field]
                
                # Add other new fields found by vision model
                for field, value in vision_data.items():
                    if field not in structured_data and value:
                        structured_data[field] = value
            
            # Save structured data to output file
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            output_file = output_dir / f"{image_path.stem}_structured.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(structured_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Structured data saved to {output_file}")
            
            # Check if extraction got required fields
            final_missing = [field for field in required_fields 
                            if field not in structured_data or not structured_data[field]]
            
            extraction_quality = "high" if not final_missing else "partial"
            
            self._add_test_result(
                test_name, 
                True, 
                {
                    "extracted_fields": list(structured_data.keys()),
                    "missing_fields": final_missing,
                    "extraction_quality": extraction_quality,
                    "output_file": str(output_file)
                }
            )
            self.test_results["mistral_structured_extraction"] = True
            return True
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error running structured extraction: {error_message}")
            self._add_test_result(test_name, False, {"error": error_message})
            return False
    
    def test_openai_extraction(self, ocr_text: str, schema_path: Union[str, Path]) -> bool:
        """Test OpenAI extraction with OCR text."""
        logger.info("Testing OpenAI extraction with OCR text")
        test_name = "OpenAI Extraction"
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            # Check if schema file exists
            schema_path = Path(schema_path)
            if not schema_path.is_file():
                raise FileNotFoundError(f"Schema file not found: {schema_path}")
            
            # Load schema
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            
            # Create prompt
            system_prompt = (
                "You are a meticulous Spanish invoice parser. "
                "Extract structured data from the invoice OCR text according to this schema:\n\n"
                f"{json.dumps(schema, indent=2)}\n\n"
                "Return ONLY a valid JSON object with the extracted fields."
            )
            
            user_prompt = f"OCR Text from invoice:\n\n{ocr_text}\n\nExtract the structured data."
            
            # Call OpenAI API
            start_time = time.time()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=2000
            )
            
            processing_time = time.time() - start_time
            
            # Parse response
            extraction_result = json.loads(response.choices[0].message.content)
            
            # Save structured data to output file
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            output_file = output_dir / f"openai_extraction_{timestamp}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(extraction_result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"OpenAI extraction saved to {output_file}")
            
            # Check if extraction got required fields
            required_fields = schema.get("required", [])
            missing_fields = [field for field in required_fields 
                             if field not in extraction_result or not extraction_result[field]]
            
            extraction_quality = "high" if not missing_fields else "partial"
            
            self._add_test_result(
                test_name, 
                True, 
                {
                    "extracted_fields": list(extraction_result.keys()),
                    "missing_fields": missing_fields,
                    "extraction_quality": extraction_quality,
                    "processing_time": processing_time,
                    "output_file": str(output_file)
                }
            )
            self.test_results["openai_extraction"] = True
            return True
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error running OpenAI extraction: {error_message}")
            self._add_test_result(test_name, False, {"error": error_message})
            return False
    
    def _add_test_result(self, test_name: str, success: bool, details: Dict[str, Any]) -> None:
        """Add a test result to the results list."""
        self.test_results["tests"].append({
            "name": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details
        })
    
    def save_results(self) -> None:
        """Save all test results to a JSON file."""
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"api_test_results_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Test results saved to {output_file}")
        
        # Print summary
        success_count = sum(1 for test in self.test_results["tests"] if test["success"])
        total_count = len(self.test_results["tests"])
        
        logger.info(f"Test Summary: {success_count}/{total_count} tests passed")
        logger.info(f"Log file: {log_file}")
        logger.info(f"Results file: {output_file}")
        
        print("\n===== API TEST SUMMARY =====")
        print(f"Tests Passed: {success_count}/{total_count}")
        print(f"Mistral Connection: {'✅' if self.test_results['mistral_connection'] else '❌'}")
        print(f"OpenAI Connection: {'✅' if self.test_results['openai_connection'] else '❌'}")
        print(f"Mistral OCR: {'✅' if self.test_results['mistral_ocr_test'] else '❌'}")
        print(f"Mistral Structured Extraction: {'✅' if self.test_results['mistral_structured_extraction'] else '❌'}")
        print(f"OpenAI Extraction: {'✅' if self.test_results['openai_extraction'] else '❌'}")
        print(f"Log file: {log_file}")
        print(f"Results file: {output_file}")
        print("============================\n")


def main():
    """Run the API integration tests."""
    parser = argparse.ArgumentParser(description="Test API integrations and log results")
    
    parser.add_argument("--image", "-i", 
                      help="Path to test image for OCR (default: first image in invoices/ dir)",
                      default=None)
    
    parser.add_argument("--schema", "-s", 
                      help="Path to JSON schema file (default: schemas/invoice.json)",
                      default="schemas/invoice.json")
    
    parser.add_argument("--skip-mistral", action="store_true", 
                      help="Skip Mistral API tests")
    
    parser.add_argument("--skip-openai", action="store_true", 
                      help="Skip OpenAI API tests")
    
    args = parser.parse_args()
    
    # Find test image if not specified
    if not args.image:
        invoices_dir = Path("invoices")
        if invoices_dir.exists():
            image_files = []
            for ext in ["pdf", "jpg", "jpeg", "png"]:
                image_files.extend(list(invoices_dir.glob(f"*.{ext}")))
            
            if image_files:
                args.image = str(image_files[0])
                logger.info(f"Using first found image: {args.image}")
            else:
                logger.error("No image files found in invoices/ directory")
                print("Error: No image files found. Please specify an image with --image")
                sys.exit(1)
        else:
            logger.error("Invoices directory not found")
            print("Error: Invoices directory not found. Please specify an image with --image")
            sys.exit(1)
    
    # Run tests
    tester = APITester()
    
    if not args.skip_mistral:
        tester.test_mistral_connection()
        
        if tester.test_results["mistral_connection"]:
            tester.test_mistral_ocr(args.image)
            
            # Only run structured extraction if OCR succeeded
            if tester.test_results["mistral_ocr_test"]:
                tester.test_mistral_structured_extraction(args.image, args.schema)
    
    if not args.skip_openai:
        tester.test_openai_connection()
        
        # Only run OpenAI extraction if we have OCR text
        if not args.skip_mistral and tester.test_results["mistral_ocr_test"]:
            # Read OCR text from output file
            ocr_file = Path("output") / f"{Path(args.image).stem}_ocr.txt"
            if ocr_file.exists():
                with open(ocr_file, "r", encoding="utf-8") as f:
                    ocr_text = f.read()
                tester.test_openai_extraction(ocr_text, args.schema)
    
    # Save results
    tester.save_results()


if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    main() 
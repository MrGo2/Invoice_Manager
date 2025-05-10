"""
Mistral OCR Wrapper

This module provides a wrapper around the Mistral OCR API for extracting text from invoice images and PDFs.
Supports direct PDF processing as well as image-based OCR with fallback to Tesseract.
"""

import os
import base64
import json
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Union, Any, Optional
from datetime import datetime
import random

from mistralai import Mistral, SDKError

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class MistralOCR:
    """Wrapper for Mistral OCR for text extraction from images and PDFs."""
    
    def __init__(self, config: Dict):
        """
        Initialize the Mistral OCR wrapper.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.lang = config.get("language", "spa")
        self.model = config["ocr"]["mistral"]["model"]
        self.timeout = config["ocr"]["mistral"].get("timeout", 60)
        
        # Retry settings
        self.max_retries = config["ocr"]["mistral"].get("max_retries", 3)
        self.base_retry_delay = config["ocr"]["mistral"].get("base_retry_delay", 2)
        self.max_retry_delay = config["ocr"]["mistral"].get("max_retry_delay", 30)
        
        # Ensure API key is set
        self.api_key = os.environ.get("MISTRAL_API_KEY")
        if not self.api_key:
            logger.warning("MISTRAL_API_KEY environment variable not set. OCR functionality will be limited.")
        
        # Initialize Mistral client
        self.client = Mistral(api_key=self.api_key)
        
        # Schema path for structured extraction
        self.schema_path = Path(config["validation"]["schema"])
        if not self.schema_path.exists():
            logger.warning(f"Schema file not found at {self.schema_path}. Structured extraction may be limited.")
        
        logger.info(f"Initialized Mistral OCR with model: {self.model}")
    
    def _execute_with_retry(self, func, *args, **kwargs):
        """
        Execute a function with retry logic for handling rate limits.
        
        Args:
            func: Function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function call
        """
        retries = 0
        while True:
            try:
                return func(*args, **kwargs)
            except SDKError as e:
                # Check if this is a rate limit error (status code 429)
                if hasattr(e, 'status_code') and e.status_code == 429 and retries < self.max_retries:
                    retries += 1
                    # Exponential backoff with jitter
                    delay = min(self.base_retry_delay * (2 ** retries) + random.uniform(0, 1), self.max_retry_delay)
                    logger.warning(f"Rate limit exceeded. Retrying in {delay:.2f} seconds (attempt {retries}/{self.max_retries})")
                    time.sleep(delay)
                else:
                    # Re-raise for other errors or if max retries exceeded
                    raise
            except Exception as e:
                # Re-raise any other exceptions
                raise
    
    def run_ocr(self, file_path: Union[str, Path]) -> List[Dict]:
        """
        Run OCR on the provided file using Mistral API.
        Automatically detects if the file is a PDF or an image and processes accordingly.
        
        Args:
            file_path: Path to the PDF or image file
            
        Returns:
            List of dictionaries containing text and confidence scores
        """
        logger.debug(f"Running Mistral OCR on: {file_path}")
        
        try:
            # Convert path to string if it's a Path object
            file_path = str(file_path)
            start_time = datetime.now()
            
            # Check if file exists
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Determine file type
            file_ext = Path(file_path).suffix.lower()
            
            # Process based on file type
            if file_ext == ".pdf":
                return self.process_pdf(file_path)
            elif file_ext in [".jpg", ".jpeg", ".png", ".tiff", ".tif"]:
                return self.process_image(file_path)
            else:
                logger.warning(f"Unsupported file format: {file_ext}. Attempting to process as image.")
                return self.process_image(file_path)
                
        except Exception as e:
            logger.error(f"Error running Mistral OCR: {str(e)}")
            raise RuntimeError(f"Mistral OCR failed: {str(e)}")
    
    def process_pdf(self, pdf_path: str) -> List[Dict]:
        """
        Process a PDF file directly with Mistral OCR.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing text and confidence scores
        """
        try:
            start_time = datetime.now()
            
            # Upload PDF to Mistral API
            with open(pdf_path, "rb") as pdf_file:
                upload_result = self._execute_with_retry(
                    self.client.files.upload,
                    file={
                        "file_name": Path(pdf_path).name,
                        "content": pdf_file
                    },
                    purpose="ocr"
                )
            
            # Get a signed URL for processing
            signed_url = self._execute_with_retry(
                self.client.files.get_signed_url,
                file_id=upload_result.id
            )
            
            # Process the PDF with Mistral OCR
            ocr_response = self._execute_with_retry(
                self.client.ocr.process,
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": signed_url.url
                }
            )
            
            # Convert OCR response to a format compatible with existing code
            results = []
            confidence = 0.95  # Native OCR has high confidence
            
            # Extract text from all pages
            for page_idx, page in enumerate(ocr_response.pages):
                words = page.markdown.split()
                
                # Add each word to results
                for word in words:
                    results.append({
                        "text": word,
                        "conf": confidence,
                        "box": (0, 0, 0, 0),  # Placeholder box coordinates
                        "page": page_idx
                    })
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds() * 1000  # in milliseconds
            
            num_words = len(results)
            num_pages = len(ocr_response.pages)
            logger.info(f"Mistral OCR processed {num_words} words across {num_pages} pages with confidence: {confidence:.2f} in {processing_time:.2f}ms")
            
            # Store the OCR response in the instance for later use
            self.last_ocr_response = ocr_response
            
            return results
                
        except Exception as e:
            logger.error(f"Error processing PDF with Mistral OCR: {str(e)}")
            # Try to convert PDF to image and use image processing as fallback
            logger.info("Attempting to convert PDF to image and process with fallback method")
            from pdf2image import convert_from_path
            
            try:
                # Convert first page of PDF to image
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                    temp_path = temp_file.name
                
                images = convert_from_path(pdf_path, first_page=1, last_page=1)
                if images:
                    images[0].save(temp_path)
                    return self.process_image(temp_path)
                else:
                    raise RuntimeError("Failed to convert PDF to image")
            except Exception as conv_error:
                logger.error(f"Error converting PDF to image: {str(conv_error)}")
                raise RuntimeError(f"PDF processing failed: {str(e)}")
    
    def process_image(self, image_path: str) -> List[Dict]:
        """
        Process an image file with Mistral OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of dictionaries containing text and confidence scores
        """
        try:
            start_time = datetime.now()
            
            # First try with native Mistral OCR
            try:
                with open(image_path, "rb") as img_file:
                    img_data = img_file.read()
                    
                # Create base64 encoded image
                encoded = base64.b64encode(img_data).decode()
                
                # Process with Mistral OCR
                ocr_response = self._execute_with_retry(
                    self.client.ocr.process,
                    model="mistral-ocr-latest",
                    document={
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{encoded}"
                    }
                )
                
                # Convert OCR response to expected format
                results = []
                confidence = 0.95
                
                # Extract text from response
                if ocr_response.pages and len(ocr_response.pages) > 0:
                    words = ocr_response.pages[0].markdown.split()
                    
                    # Add each word to results
                    for word in words:
                        results.append({
                            "text": word,
                            "conf": confidence,
                            "box": (0, 0, 0, 0),  # Placeholder
                            "page": 0
                        })
                    
                    # Store the OCR response
                    self.last_ocr_response = ocr_response
                    
                    end_time = datetime.now()
                    processing_time = (end_time - start_time).total_seconds() * 1000
                    
                    num_words = len(results)
                    logger.info(f"Mistral OCR processed {num_words} words with confidence: {confidence:.2f} in {processing_time:.2f}ms")
                    
                    return results
                else:
                    raise RuntimeError("No text extracted from image")
                    
            except Exception as ocr_error:
                logger.error(f"Error in Mistral OCR API call: {str(ocr_error)}")
                # Fall back to legacy approach
                return self._legacy_process_image(image_path)
                
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise RuntimeError(f"Image processing failed: {str(e)}")
    
    def _legacy_process_image(self, image_path: str) -> List[Dict]:
        """
        Legacy method to process images using alternative approaches.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of dictionaries containing text and confidence scores
        """
        try:
            # Try with vision model first
            with open(image_path, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode()
            
            try:
                # Call Mistral API with vision capability
                response = self._execute_with_retry(
                    self.client.chat.complete,
                    model="mistral-large-vision-latest",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Extract all text from this image, exactly as written."},
                                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{encoded}"}
                            ]
                        }
                    ]
                )
                
                # Get the OCR text result
                image_ocr_text = response.choices[0].message.content
                confidence = 0.9  # Estimated since vision model doesn't provide confidence
                
                # For compatibility with existing code, create word-level structure
                words = image_ocr_text.split()
                results = [
                    {
                        "text": word,
                        "conf": confidence,
                        "box": (0, 0, 0, 0),  # Placeholder box coordinates
                        "page": 0  # Default page number
                    }
                    for word in words
                ]
                
                num_words = len(results)
                logger.info(f"Vision model OCR processed {num_words} words with confidence: {confidence:.2f}")
                
                return results
                
            except Exception as e:
                logger.error(f"Error in vision model OCR: {str(e)}")
                # Fall back to Tesseract
                return self._run_tesseract_fallback(image_path)
            
        except Exception as e:
            logger.error(f"Error in legacy image processing: {str(e)}")
            return self._run_tesseract_fallback(image_path)
    
    def _run_tesseract_fallback(self, image_path: str) -> List[Dict]:
        """
        Fall back to Tesseract OCR if Mistral OCR fails.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of dictionaries containing text and confidence scores
        """
        try:
            # Process using Tesseract
            import pytesseract
            from PIL import Image
            
            logger.info(f"Using Tesseract fallback for OCR processing of {image_path}")
            
            # Convert to PIL Image
            pil_image = Image.open(image_path)
            
            # Perform OCR with Tesseract
            text = pytesseract.image_to_string(pil_image, lang=self.lang)
            
            # For compatibility with the existing code, create a word-level structure
            words = text.split()
            results = [
                {
                    "text": word,
                    "conf": 0.90,  # Default confidence 
                    "box": (0, 0, 0, 0),  # Placeholder bounding box
                    "page": 0  # Default page
                }
                for word in words
            ]
            
            num_words = len(results)
            logger.info(f"Processed {num_words} words with Tesseract fallback")
            return results
            
        except Exception as e:
            logger.error(f"Error running Tesseract fallback OCR: {str(e)}")
            raise RuntimeError(f"OCR processing failed: {str(e)}")
    
    def get_text_from_results(self, results: List[Dict]) -> str:
        """
        Extract plain text from OCR results.
        
        Args:
            results: List of OCR result dictionaries
            
        Returns:
            Plain text extracted from results
        """
        return " ".join([word["text"] for word in results])
    
    def get_markdown_from_last_ocr(self) -> Optional[List[str]]:
        """
        Get the full markdown text from the last OCR response.
        
        Returns:
            List of markdown strings for each page, or None if no OCR response is available
        """
        if hasattr(self, 'last_ocr_response'):
            return [page.markdown for page in self.last_ocr_response.pages]
        return None
    
    def extract_structured_data(self, file_path: Union[str, Path], ocr_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Use Mistral to extract structured data from OCR text based on our invoice schema.
        If native OCR results are available, they will be used instead of the ocr_text parameter.
        
        Args:
            file_path: Path to the original file (PDF or image)
            ocr_text: OCR text extracted from the file (optional if native OCR was used)
            
        Returns:
            Dictionary with structured invoice data
        """
        try:
            file_path = str(file_path)
            start_time = datetime.now()
            
            # Check if we have native OCR results
            has_native_results = hasattr(self, 'last_ocr_response')
            
            # If we have native OCR results, process directly
            if has_native_results:
                logger.info("Using native OCR results for structured extraction")
                
                # Get the first page's markdown
                first_page_md = self.last_ocr_response.pages[0].markdown if self.last_ocr_response.pages else ""
                
                # Extract structured data using an LLM with a schema-aligned prompt
                chat_response = self._execute_with_retry(
                    self.client.chat.complete,
                    model="mistral-large-latest", 
                    messages=[
                        {
                            "role": "user",
                            "content": (
                                "Extract the following information from this Spanish invoice, using EXACTLY these field names and formats:\n\n"
                                "- invoice_number: The invoice identifier\n"
                                "- issue_date: Date in DD/MM/YYYY format (e.g., 01/05/2024)\n"
                                "- vendor_name: Company issuing the invoice\n"
                                "- vendor_tax_id: Spanish tax ID (NIF/CIF) with format like B12345678\n"
                                "- vendor_address: Full address of vendor\n"
                                "- buyer_name: Name of customer\n"
                                "- buyer_tax_id: Customer tax ID\n"
                                "- buyer_address: Full address of buyer\n"
                                "- taxable_base: Base amount before tax, with comma as decimal separator (e.g., 100,50 €)\n"
                                "- vat_rate: VAT percentage with % symbol (e.g., 21%)\n"
                                "- vat_amount: VAT amount with comma as decimal separator (e.g., 21,11 €)\n"
                                "- total_amount: Total invoice amount with comma as decimal separator (e.g., 121,61 €)\n"
                                "- payment_terms: Payment terms if available\n"
                                "- currency: EUR, USD, or GBP\n"
                                "- line_items: Array of items with description, qty, unit_price, and line_total fields\n\n"
                                f"Here is the invoice text:\n\n{first_page_md}"
                            )
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0
                )
                
                # Parse the structured data
                structured_data = json.loads(chat_response.choices[0].message.content)
                
                # Add metadata
                if "metadata" not in structured_data:
                    structured_data["metadata"] = {}
                
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                
                structured_data["metadata"].update({
                    "source_file": Path(file_path).name,
                    "processing_duration_ms": int(processing_time),
                    "extraction_method": "mistral_structured",
                    "ocr_engine": "mistral_ocr_native",
                    "confidence_score": 0.95
                })
                
                logger.info(f"Extracted {len(structured_data)} fields using Mistral OCR + LLM structure extraction")
                return structured_data
                
            # If we don't have native OCR results, fallback to original method
            if not ocr_text:
                logger.warning("No OCR text provided and no native OCR results available")
                return {}
            
            # Load schema file
            with open(self.schema_path, 'r') as f:
                schema = json.load(f)
            
            # Simplify schema description for prompt
            schema_description = {}
            for key, value in schema.get("properties", {}).items():
                if not key.startswith("//") and not key == "metadata":
                    schema_description[key] = value.get("description", "")
            
            # Create base64 encoded image for visual context (if needed)
            with open(file_path, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode()
            
            # First extract with text-only model for efficiency
            prompt = (
                "Extract structured data from this Spanish invoice OCR text according to this schema:\n\n"
                f"{json.dumps(schema_description, indent=2)}\n\n"
                "The OCR text of the invoice is:\n\n"
                f"{ocr_text}\n\n"
                "Return ONLY a valid JSON object with the extracted fields according to the schema. "
                "For Spanish invoices, look for fields like: 'Factura', 'Número', 'Fecha', 'NIF/CIF', "
                "'Emisor', 'Destinatario', 'Base Imponible', 'IVA', etc. For date fields, use DD/MM/YYYY format."
            )
            
            response = self._execute_with_retry(
                self.client.chat.complete,
                model="mistral-medium",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            
            # Parse initial extraction
            structured_data = json.loads(response.choices[0].message.content)
            confidence = 0.85  # Base confidence with text-only model
            
            # If text-only extraction misses critical fields, try with vision model
            missing_fields = [field for field in schema.get("required", []) 
                             if field not in structured_data or not structured_data[field]]
            
            if missing_fields:
                logger.info(f"Text-only extraction missing fields: {missing_fields}. Trying vision model.")
                
                # Vision model extraction (with both image and text)
                vision_prompt = (
                    "This is a Spanish invoice image. Extract ALL the structured data according to this schema:\n\n"
                    f"{json.dumps(schema_description, indent=2)}\n\n"
                    "For reference, this is the OCR text already extracted:\n\n"
                    f"{ocr_text[:500]}...\n\n"
                    "Return ONLY a valid JSON object with the extracted fields. Pay special attention to "
                    f"these missing fields: {', '.join(missing_fields)}."
                )
                
                vision_response = self._execute_with_retry(
                    self.client.chat.complete,
                    model="mistral-large-vision-latest",
                    messages=[
                        {
                            "role": "user", 
                            "content": [
                                {"type": "text", "text": vision_prompt},
                                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{encoded}"}
                            ]
                        }
                    ],
                    temperature=0
                )
                
                try:
                    vision_data = json.loads(vision_response.choices[0].message.content)
                    
                    # Merge results, preferring vision model for previously missing fields
                    for field in missing_fields:
                        if field in vision_data and vision_data[field]:
                            structured_data[field] = vision_data[field]
                    
                    # Add other new fields found by vision model
                    for field, value in vision_data.items():
                        if field not in structured_data and value:
                            structured_data[field] = value
                    
                    confidence = 0.92  # Higher confidence with vision model assist
                    
                except Exception as e:
                    logger.error(f"Error parsing vision model response: {str(e)}")
            
            # Add metadata
            if "metadata" not in structured_data:
                structured_data["metadata"] = {}
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            structured_data["metadata"].update({
                "confidence_score": confidence,
                "extraction_timestamp": datetime.now().isoformat(),
                "ocr_engine": "mistral",
                "ocr_engine_version": "latest",
                "source_file": Path(file_path).name,
                "processing_duration_ms": int(processing_time),
                "extraction_method": "legacy"
            })
            
            logger.info(f"Extracted structured data with {len(structured_data)} fields using legacy method")
            return structured_data
            
        except Exception as e:
            logger.error(f"Error extracting structured data: {str(e)}")
            return {} 
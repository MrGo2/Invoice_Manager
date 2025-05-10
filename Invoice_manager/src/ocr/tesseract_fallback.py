"""
Tesseract OCR Fallback

This module provides a fallback OCR option using Tesseract when Mistral OCR fails or for comparison.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Union, Optional

import pytesseract
from PIL import Image

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TesseractOCR:
    """Wrapper for Tesseract OCR as a fallback for text extraction."""
    
    def __init__(self, config: Dict):
        """
        Initialize the Tesseract OCR wrapper.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.lang = config.get("language", "spa")
        self.options = config["ocr"]["tesseract"]["options"]
        
        # Check if Tesseract is installed
        self._check_tesseract_installed()
        
        logger.info(f"Initialized Tesseract OCR with language: {self.lang}")
    
    def _check_tesseract_installed(self) -> None:
        """
        Check if Tesseract is properly installed on the system.
        """
        try:
            version = pytesseract.get_tesseract_version()
            logger.debug(f"Detected Tesseract version: {version}")
        except Exception as e:
            logger.warning(f"Tesseract not properly configured: {str(e)}")
            logger.warning("Make sure Tesseract is installed and properly configured.")
    
    def _check_language_pack(self, lang: str) -> bool:
        """
        Check if the required language pack is installed.
        
        Args:
            lang: Language code to check
            
        Returns:
            True if language pack is installed, False otherwise
        """
        try:
            result = subprocess.run(
                ["tesseract", "--list-langs"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            installed_langs = result.stdout.strip().split("\n")[1:]  # Skip first line (header)
            return lang in installed_langs
        except subprocess.SubprocessError:
            logger.warning(f"Could not check if language pack '{lang}' is installed")
            return False
    
    def run_ocr(self, image_path: Union[str, Path]) -> List[Dict]:
        """
        Run OCR on the provided image using Tesseract.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of dictionaries containing text and confidence scores
        """
        logger.debug(f"Running Tesseract OCR on: {image_path}")
        
        # Ensure the language pack is installed
        if not self._check_language_pack(self.lang):
            logger.warning(f"Tesseract language pack '{self.lang}' not installed. Using default language.")
            lang_param = None
        else:
            lang_param = self.lang
        
        try:
            # Open the image
            image = Image.open(image_path)
            
            # Get detailed OCR results with confidence levels
            config = f"{self.options} --psm 6"
            data = pytesseract.image_to_data(
                image, 
                lang=lang_param,
                config=config,
                output_type=pytesseract.Output.DICT
            )
            
            # Convert to standardized format
            results = []
            for i in range(len(data["text"])):
                # Skip empty text
                if not data["text"][i].strip():
                    continue
                    
                # Calculate confidence as probability (0-1)
                conf = float(data["conf"][i]) / 100.0
                
                # Create box coordinates
                left = data["left"][i]
                top = data["top"][i]
                width = data["width"][i]
                height = data["height"][i]
                box = (left, top, left + width, top + height)
                
                results.append({
                    "text": data["text"][i],
                    "conf": conf,
                    "box": box,
                    "page": 0  # Tesseract processes one page at a time
                })
            
            num_words = len(results)
            avg_conf = sum(word["conf"] for word in results) / max(1, num_words)
            
            logger.info(f"Tesseract OCR processed {num_words} words with average confidence: {avg_conf:.2f}")
            return results
            
        except Exception as e:
            logger.error(f"Error running Tesseract OCR: {str(e)}")
            raise RuntimeError(f"Tesseract OCR failed: {str(e)}")
    
    def get_text_from_results(self, results: List[Dict]) -> str:
        """
        Extract plain text from OCR results.
        
        Args:
            results: List of OCR result dictionaries
            
        Returns:
            Plain text extracted from results
        """
        return " ".join([word["text"] for word in results]) 
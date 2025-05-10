"""
Image Preprocessing

This module handles preprocessing of invoice images before OCR, including:
- PDF to image conversion
- Deskewing
- Contrast enhancement
- Noise removal
- DPI adjustment
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ImageProcessor:
    """Preprocesses invoice images to optimize OCR quality."""
    
    def __init__(self, config: Dict):
        """
        Initialize the image processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.target_dpi = config["ocr"]["preprocessing"]["dpi"]
        self.deskew = config["ocr"]["preprocessing"]["deskew"]
        self.denoise = config["ocr"]["preprocessing"]["denoise"]
        self.contrast_enhancement = config["ocr"]["preprocessing"]["contrast_enhancement"]
        self.allowed_formats = config["input"]["allowed_formats"]
        
        logger.info(f"Initialized image processor with target DPI: {self.target_dpi}")
    
    def process(self, file_path: Union[str, Path]) -> List[str]:
        """
        Process an invoice file, converting it to images and applying preprocessing.
        
        Args:
            file_path: Path to the invoice file (PDF, PNG, JPG, etc.)
            
        Returns:
            List of paths to processed images
        """
        file_path = Path(file_path)
        
        logger.info(f"Processing file: {file_path}")
        
        # Validate file format
        if file_path.suffix.lower()[1:] not in self.allowed_formats:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        # Convert to images if PDF
        if file_path.suffix.lower() == '.pdf':
            image_paths = self._convert_pdf_to_images(file_path)
        else:
            # Create a temporary file for the processed image
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Copy the original image to the temp location for processing
            image = Image.open(file_path)
            image.save(temp_path)
            image_paths = [temp_path]
        
        # Apply preprocessing to each image
        processed_paths = []
        for img_path in image_paths:
            processed_path = self._preprocess_image(img_path)
            processed_paths.append(processed_path)
        
        logger.info(f"Processed {len(processed_paths)} images")
        return processed_paths
    
    def _convert_pdf_to_images(self, pdf_path: Path) -> List[str]:
        """
        Convert PDF to images.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of paths to generated images
        """
        logger.debug(f"Converting PDF to images: {pdf_path}")
        
        try:
            # Convert PDF to images at target DPI
            images = convert_from_path(
                pdf_path, 
                dpi=self.target_dpi,
                output_folder=tempfile.gettempdir(),
                fmt="png"
            )
            
            # Save images to temporary files
            image_paths = []
            for i, image in enumerate(images):
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                    temp_path = temp_file.name
                    image.save(temp_path)
                    image_paths.append(temp_path)
                    logger.debug(f"Saved PDF page {i+1} to {temp_path}")
            
            return image_paths
        
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            raise RuntimeError(f"PDF conversion failed: {str(e)}")
    
    def _preprocess_image(self, image_path: str) -> str:
        """
        Apply preprocessing steps to an image.
        
        Args:
            image_path: Path to the input image
            
        Returns:
            Path to the processed image
        """
        logger.debug(f"Preprocessing image: {image_path}")
        
        try:
            # Read the image with OpenCV
            img = cv2.imread(image_path)
            
            # Convert to grayscale if it's not already
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img
            
            # Apply deskewing if enabled
            if self.deskew:
                gray = self._deskew_image(gray)
            
            # Apply contrast enhancement if enabled
            if self.contrast_enhancement:
                gray = self._enhance_contrast(gray)
            
            # Apply denoising if enabled
            if self.denoise:
                gray = self._remove_noise(gray)
            
            # Create a temporary file for the processed image
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                processed_path = temp_file.name
            
            # Save the processed image
            cv2.imwrite(processed_path, gray)
            logger.debug(f"Saved preprocessed image to {processed_path}")
            
            return processed_path
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            # Return original image if preprocessing fails
            return image_path
    
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """
        Deskew an image by detecting and correcting rotation.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Deskewed image
        """
        try:
            # Detect edges
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            
            # Detect lines using Hough transform
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
            
            if lines is None or len(lines) == 0:
                logger.debug("No lines detected for deskewing, returning original image")
                return image
            
            # Calculate angles
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 - x1 == 0:  # Avoid division by zero
                    continue
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                angles.append(angle)
            
            if not angles:
                return image
            
            # Find the most common angle (histogram with bins of 1 degree)
            hist, bin_edges = np.histogram(angles, bins=np.arange(-90, 91, 1))
            angle_index = np.argmax(hist)
            skew_angle = bin_edges[angle_index]
            
            # Only correct if angle is within reasonable bounds
            if abs(skew_angle) < 10:
                # Calculate rotation center
                h, w = image.shape[:2]
                center = (w // 2, h // 2)
                
                # Perform rotation
                rotation_matrix = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
                rotated = cv2.warpAffine(image, rotation_matrix, (w, h), 
                                         flags=cv2.INTER_CUBIC, 
                                         borderMode=cv2.BORDER_CONSTANT, 
                                         borderValue=255)
                
                logger.debug(f"Deskewed image by {skew_angle:.2f} degrees")
                return rotated
            else:
                logger.debug(f"Skew angle {skew_angle:.2f} too large, skipping deskew")
                return image
                
        except Exception as e:
            logger.warning(f"Deskew failed: {str(e)}")
            return image
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Contrast-enhanced image
        """
        try:
            # Apply CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)
            
            logger.debug("Applied CLAHE contrast enhancement")
            return enhanced
            
        except Exception as e:
            logger.warning(f"Contrast enhancement failed: {str(e)}")
            return image
    
    def _remove_noise(self, image: np.ndarray) -> np.ndarray:
        """
        Remove noise from image.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Denoised image
        """
        try:
            # Apply bilateral filter for edge-preserving denoising
            denoised = cv2.bilateralFilter(image, 9, 75, 75)
            
            logger.debug("Applied bilateral filter for noise removal")
            return denoised
            
        except Exception as e:
            logger.warning(f"Noise removal failed: {str(e)}")
            return image 
# OCR Optimization Guide

This document provides detailed information on optimizing Optical Character Recognition (OCR) for invoice processing, focusing on preprocessing techniques, OCR engine configurations, and performance optimization.

## Table of Contents

1. [Introduction](#introduction)
2. [Preprocessing Techniques](#preprocessing-techniques)
3. [OCR Engine Configuration](#ocr-engine-configuration)
4. [Confidence Measurement](#confidence-measurement)
5. [Language-Specific Optimization](#language-specific-optimization)
6. [Handling Complex Layouts](#handling-complex-layouts)
7. [Performance Optimization](#performance-optimization)
8. [Troubleshooting](#troubleshooting)

## Introduction

The Invoice Processor uses a dual OCR approach:

- **Primary OCR**: Mistral OCR, specialized for Spanish language documents
- **Fallback OCR**: Tesseract OCR, providing additional coverage and comparison

Effective OCR is the foundation of reliable extraction. This guide covers techniques to optimize OCR performance for Spanish invoices.

## Preprocessing Techniques

### Image Resolution

- **Target DPI**: 300 DPI (dots per inch)
- **Upscaling**: Low-resolution images are upscaled to 300 DPI using bicubic interpolation
- **Downscaling**: Very high-resolution images may be downscaled to reduce processing time

```python
# Resize to target DPI
def resize_to_target_dpi(image, current_dpi, target_dpi=300):
    scale_factor = target_dpi / current_dpi
    new_width = int(image.shape[1] * scale_factor)
    new_height = int(image.shape[0] * scale_factor)
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
```

### Deskewing

Deskewing corrects rotation issues in scanned documents:

1. **Detection**: Identify text lines using Hough transform
2. **Angle Calculation**: Calculate the predominant angle of text lines
3. **Rotation**: Apply affine transformation to correct the skew

```python
def deskew_image(image):
    # Detect edges
    edges = cv2.Canny(image, 50, 150, apertureSize=3)
    
    # Detect lines using Hough transform
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
    
    # Calculate angles
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
        angles.append(angle)
    
    # Find the most common angle
    hist, bin_edges = np.histogram(angles, bins=np.arange(-90, 91, 1))
    skew_angle = bin_edges[np.argmax(hist)]
    
    # Apply rotation if angle is within reasonable bounds
    if abs(skew_angle) < 10:
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
        return cv2.warpAffine(image, rotation_matrix, (w, h), 
                             flags=cv2.INTER_CUBIC, 
                             borderMode=cv2.BORDER_CONSTANT, 
                             borderValue=255)
    return image
```

### Contrast Enhancement

CLAHE (Contrast Limited Adaptive Histogram Equalization) improves text visibility:

```python
def enhance_contrast(image):
    # Apply CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(image)
```

### Noise Removal

Bilateral filtering preserves edges while removing noise:

```python
def remove_noise(image):
    # Apply bilateral filter for edge-preserving denoising
    return cv2.bilateralFilter(image, 9, 75, 75)
```

### PDF Handling

For PDF documents:

1. **Conversion**: Convert PDF pages to images using pdf2image
2. **Resolution**: Convert at 300 DPI
3. **Format**: PNG format preserves quality for OCR

```python
def convert_pdf_to_images(pdf_path, dpi=300):
    images = convert_from_path(pdf_path, dpi=dpi, fmt="png")
    return images
```

## OCR Engine Configuration

### Mistral OCR

Optimal configuration for Spanish invoices:

```python
# Mistral OCR configuration
model = "mistral-ocr-base-spa"  # Spanish language model
batch_size = 8                  # Trade-off between speed and memory
greedy_decoding = True          # More stable results for structured documents
```

### Tesseract OCR

Optimal configuration for Spanish invoices:

```python
# Tesseract configuration
lang = "spa"                    # Spanish language data
oem = 1                         # LSTM neural net mode
psm = 6                         # Assume a single uniform block of text
```

Tesseract PSM (Page Segmentation Mode) options for invoices:

| PSM | Description | Use Case |
|-----|-------------|----------|
| 3 | Auto page segmentation | General purpose |
| 4 | Single column of text | Simple invoices |
| 6 | Single uniform block | Most invoice sections |
| 11 | Sparse text | Tables and line items |

## Confidence Measurement

### Confidence Scoring

Both OCR engines provide confidence scores for extracted text:

- **Mistral**: 0.0-1.0 scale per word
- **Tesseract**: 0-100 scale, converted to 0.0-1.0

### Confidence Thresholds

- **High Confidence**: > 0.85 (reliable extraction)
- **Medium Confidence**: 0.60-0.85 (review recommended)
- **Low Confidence**: < 0.60 (manual verification needed)

### Confidence Merging Strategies

The system supports multiple strategies for merging OCR results:

1. **Highest Confidence**: Choose the engine with higher overall confidence
   ```python
   if primary_conf >= fallback_conf:
       return primary_results
   else:
       return fallback_results
   ```

2. **Line-by-Line Merge**: Select the best engine for each line
   ```python
   for line_position in all_line_positions:
       primary_line = get_line(primary_results, line_position)
       fallback_line = get_line(fallback_results, line_position)
       
       if confidence(primary_line) >= confidence(fallback_line):
           merged_results.extend(primary_line)
       else:
           merged_results.extend(fallback_line)
   ```

3. **Word-by-Word Merge**: Select the best engine for each word
   ```python
   for primary_word in primary_results:
       matching_fallback_words = find_matching_words(primary_word, fallback_results)
       
       if matching_fallback_words and best_match.conf > primary_word.conf:
           merged_results.append(best_match)
       else:
           merged_results.append(primary_word)
   ```

## Language-Specific Optimization

### Spanish Language Specifics

Spanish invoices have unique characteristics:

- **Date Formats**: DD/MM/YYYY (e.g., 15/06/2023)
- **Number Formats**: Comma as decimal separator (e.g., 1.234,56 €)
- **Tax Documentation**: NIF/CIF format (e.g., B12345678)
- **Special Characters**: ñ, á, é, í, ó, ú, ü

### Language Pack Installation

For Tesseract:

```bash
# macOS
brew install tesseract-lang
brew link --force tesseract-lang

# Ubuntu/Debian
sudo apt-get install tesseract-ocr-spa

# Windows
# Download Spanish language data from
# https://github.com/tesseract-ocr/tessdata/blob/main/spa.traineddata
# and place in Tesseract tessdata directory
```

## Handling Complex Layouts

### Table Detection

For invoice line items:

1. **Line Detection**: Identify horizontal and vertical lines
2. **Grid Analysis**: Reconstruct the table structure
3. **Cell Extraction**: OCR each cell individually for better accuracy

```python
def detect_tables(image):
    # Detect horizontal and vertical lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
    
    horizontal_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, horizontal_kernel)
    vertical_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, vertical_kernel)
    
    # Combine lines to form table grid
    table_grid = cv2.add(horizontal_lines, vertical_lines)
    
    # Find contours to identify table cells
    contours, _ = cv2.findContours(table_grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    return contours
```

### Multi-Column Layout

For invoices with multiple columns:

1. **Column Detection**: Identify column boundaries
2. **Column Separation**: Process each column separately
3. **Result Merging**: Combine results in reading order

## Performance Optimization

### Batch Processing

For processing multiple invoices:

1. **Parallel Processing**: Use multiprocessing for CPU-bound tasks
2. **Batch OCR**: Process multiple images in a single API call
3. **Resource Management**: Limit concurrent processes based on available CPU and memory

```python
def batch_process_images(image_paths, num_workers=4):
    with multiprocessing.Pool(num_workers) as pool:
        results = pool.map(process_single_image, image_paths)
    return results
```

### Memory Management

For large documents:

1. **Image Scaling**: Resize very large images to reasonable dimensions
2. **Incremental Processing**: Process one page at a time
3. **Garbage Collection**: Explicitly release memory after processing

### Caching

To improve performance:

1. **OCR Result Caching**: Cache OCR results for previously seen documents
2. **Hash-Based Identification**: Use document hashes to identify duplicates
3. **LRU Cache**: Maintain a limited cache based on recent usage

```python
@lru_cache(maxsize=100)
def cached_ocr_process(image_hash):
    # Retrieve cached OCR result or process image
    pass
```

## Troubleshooting

### Common OCR Issues

#### Low Confidence Scores

**Issue**: OCR confidence scores below 0.60

**Solutions**:
1. Improve image preprocessing (enhance contrast, increase resolution)
2. Try different page segmentation modes
3. Use specialized language packs
4. Consider retraining models for specific invoice formats

#### Character Confusion

**Issue**: Similar characters consistently misinterpreted (e.g., "0" vs "O", "l" vs "1")

**Solutions**:
1. Improve image resolution
2. Apply character-specific post-processing rules
3. Use context (e.g., numeric fields should only contain digits)

#### Missed Text Detection

**Issue**: OCR fails to detect certain text regions

**Solutions**:
1. Adjust contrast enhancement parameters
2. Experiment with different PSM modes
3. Process the image at different resolutions
4. Apply region-specific preprocessing

### Diagnostic Tools

- **Visualization**: Render bounding boxes around detected text regions
- **Confidence Mapping**: Generate heatmaps of confidence scores
- **Error Analysis**: Track and categorize common OCR errors

```python
def visualize_ocr_results(image, ocr_results):
    # Create a copy of the image for drawing
    vis_image = image.copy()
    
    # Draw bounding boxes and text
    for result in ocr_results:
        x1, y1, x2, y2 = result["box"]
        text = result["text"]
        conf = result["conf"]
        
        # Color based on confidence (green for high, red for low)
        color = (0, int(255 * conf), int(255 * (1 - conf)))
        
        cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(vis_image, f"{text} ({conf:.2f})", (x1, y1 - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    return vis_image
``` 
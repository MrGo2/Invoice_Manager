"""
Logger Configuration

This module provides logging functionality for the invoice processor.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Optional

# Global dictionary to cache loggers
_loggers = {}


def setup_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Set up and configure a logger instance.
    
    Args:
        name: Name of the logger
        level: Logging level (if None, uses config or default)
        
    Returns:
        Configured logger instance
    """
    # Return cached logger if available
    if name in _loggers:
        return _loggers[name]
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Skip if logger is already configured
    if logger.handlers:
        _loggers[name] = logger
        return logger
    
    # Determine log level
    if level is None:
        # Try to read from config or environment
        config_level = os.environ.get("LOG_LEVEL", "INFO")
        level = getattr(logging, config_level, logging.INFO)
    
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    file_path = log_dir / "invoice_processor.log"
    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Add special handlers for specific loggers
    if name in ["src.ocr.confidence_merger", "src.ocr.mistral_wrapper", "src.ocr.tesseract_fallback"]:
        _add_ocr_confidence_handler(logger, log_dir)
    
    if name == "src.extraction.openai_refiner":
        _add_openai_latency_handler(logger, log_dir)
    
    # Cache and return logger
    _loggers[name] = logger
    return logger


def _add_ocr_confidence_handler(logger: logging.Logger, log_dir: Path) -> None:
    """
    Add special handler for OCR confidence metrics.
    
    Args:
        logger: Logger to add handler to
        log_dir: Directory for log files
    """
    confidence_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )
    
    confidence_handler = RotatingFileHandler(
        log_dir / "ocr_confidence.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=3
    )
    confidence_handler.setFormatter(confidence_formatter)
    
    # Only log messages containing "confidence" or "Confidence"
    class ConfidenceFilter(logging.Filter):
        def filter(self, record):
            return "confidence" in record.getMessage() or "Confidence" in record.getMessage()
    
    confidence_handler.addFilter(ConfidenceFilter())
    logger.addHandler(confidence_handler)


def _add_openai_latency_handler(logger: logging.Logger, log_dir: Path) -> None:
    """
    Add special handler for OpenAI API latency metrics.
    
    Args:
        logger: Logger to add handler to
        log_dir: Directory for log files
    """
    latency_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )
    
    latency_handler = RotatingFileHandler(
        log_dir / "openai_latency.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=3
    )
    latency_handler.setFormatter(latency_formatter)
    
    # Only log messages containing latency information
    class LatencyFilter(logging.Filter):
        def filter(self, record):
            return "latency" in record.getMessage() or "time" in record.getMessage().lower()
    
    latency_handler.addFilter(LatencyFilter())
    logger.addHandler(latency_handler) 
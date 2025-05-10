"""
Configuration Loader

This module loads and manages configuration settings for the invoice processor.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
from dotenv import load_dotenv

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ConfigLoader:
    """Loads and validates configuration from YAML file and environment variables."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_path: Optional path to a custom config file
        """
        # Load environment variables from .env file if present
        load_dotenv()
        
        # Use provided config path or default
        if config_path is None:
            config_path = os.environ.get("CONFIG_PATH", "config.yaml")
        
        self.config_path = Path(config_path)
        
        # Load configuration
        self.config = self._load_config()
        
        # Apply environment variable overrides
        self._apply_env_overrides()
        
        logger.info(f"Configuration loaded from {self.config_path}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Returns:
            Configuration dictionary
        """
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            logger.warning("Using default configuration")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            return config
        except Exception as e:
            logger.error(f"Error loading config file: {str(e)}")
            logger.warning("Using default configuration")
            return self._get_default_config()
    
    def _apply_env_overrides(self) -> None:
        """
        Apply environment variable overrides to configuration.
        
        Environment variables override YAML configuration when they have
        the format 'INVOICE_CONFIG_section_subsection_key'.
        """
        # Process environment variables that start with INVOICE_CONFIG_
        prefix = "INVOICE_CONFIG_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and split by underscore
                config_path = key[len(prefix):].lower().split('_')
                
                # Update nested config value
                self._update_nested_dict(self.config, config_path, value)
    
    def _update_nested_dict(self, d: Dict, path: list, value: Any) -> None:
        """
        Update a nested dictionary using a path of keys.
        
        Args:
            d: Dictionary to update
            path: List of keys representing the path in the nested dictionary
            value: Value to set
        """
        key = path[0]
        if len(path) == 1:
            # Convert value to appropriate type based on existing value
            if key in d:
                if isinstance(d[key], bool):
                    d[key] = value.lower() in ('true', 'yes', '1', 'y')
                elif isinstance(d[key], int):
                    d[key] = int(value)
                elif isinstance(d[key], float):
                    d[key] = float(value)
                else:
                    d[key] = value
            else:
                d[key] = value
            return
            
        # Create nested dict if it doesn't exist
        if key not in d:
            d[key] = {}
        
        # Recurse into nested dict
        self._update_nested_dict(d[key], path[1:], value)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration when config file is not available.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "language": "spa",
            "ocr_engine": "mistral",
            "tesseract_fallback": True,
            "input": {
                "allowed_formats": ["pdf", "jpg", "jpeg", "png", "tiff"],
                "max_file_size_mb": 10
            },
            "ocr": {
                "preprocessing": {
                    "dpi": 300,
                    "deskew": True,
                    "denoise": True,
                    "contrast_enhancement": True
                },
                "mistral": {
                    "model": "mistral-ocr-base-spa",
                    "batch_size": 8,
                    "greedy_decoding": True
                },
                "tesseract": {
                    "options": "--oem 1 --psm 6",
                    "lang": "spa"
                },
                "confidence": {
                    "threshold": 0.85,
                    "merge_strategy": "highest_confidence"
                }
            },
            "openai": {
                "model": "gpt-4o",
                "temperature": 0,
                "max_tokens": 2000,
                "few_shot_examples": 3,
                "log_prompts": True
            },
            "validation": {
                "schema": "schemas/invoice.json",
                "strict_mode": False
            },
            "export": {
                "default_format": "json",
                "available_formats": ["json", "csv"],
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "headers": {}
                }
            },
            "logging": {
                "level": "INFO",
                "file": "logs/invoice_processor.log",
                "max_size_mb": 10,
                "backup_count": 5
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key (can be nested with dots, e.g., 'openai.model')
            default: Default value to return if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        current = self.config
        
        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return default
            current = current[k]
        
        return current 
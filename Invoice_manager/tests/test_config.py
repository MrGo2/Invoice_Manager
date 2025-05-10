"""
Test configuration loader functionality.
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.utils.cfg import ConfigLoader


def test_default_config():
    """Test that default configuration is loaded correctly."""
    config = ConfigLoader()._get_default_config()
    
    # Check for required sections
    assert "language" in config
    assert "ocr" in config
    assert "validation" in config
    assert "export" in config
    assert "logging" in config
    
    # Check for specific values
    assert config["language"] == "spa"
    assert config["ocr"]["preprocessing"]["dpi"] == 300


def test_load_from_file():
    """Test loading configuration from a YAML file."""
    # Create a temporary config file
    config_data = {
        "language": "eng",
        "ocr": {
            "preprocessing": {
                "dpi": 400
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
        yaml.dump(config_data, temp_file)
        temp_path = temp_file.name
    
    try:
        # Load configuration from the temp file
        config_loader = ConfigLoader(temp_path)
        
        # Check that values were loaded correctly
        assert config_loader.config["language"] == "eng"
        assert config_loader.config["ocr"]["preprocessing"]["dpi"] == 400
        
        # Check that default values are still present for unspecified options
        assert "validation" in config_loader.config
        
    finally:
        # Clean up temp file
        os.unlink(temp_path)


def test_env_var_override():
    """Test that environment variables override configuration values."""
    # Set environment variables
    os.environ["INVOICE_CONFIG_LANGUAGE"] = "cat"
    os.environ["INVOICE_CONFIG_OCR_PREPROCESSING_DPI"] = "600"
    
    try:
        # Load configuration
        config_loader = ConfigLoader()
        
        # Check that environment variables override defaults
        assert config_loader.config["language"] == "cat"
        assert config_loader.config["ocr"]["preprocessing"]["dpi"] == 600
        
    finally:
        # Clean up environment variables
        del os.environ["INVOICE_CONFIG_LANGUAGE"]
        del os.environ["INVOICE_CONFIG_OCR_PREPROCESSING_DPI"]


def test_get_method():
    """Test the get method for accessing configuration values."""
    config_loader = ConfigLoader()
    
    # Test getting values at different nesting levels
    assert config_loader.get("language") == "spa"
    assert config_loader.get("ocr.preprocessing.dpi") == 300
    
    # Test getting a non-existent value with default
    assert config_loader.get("non_existent", "default") == "default"
    
    # Test getting a nested non-existent value with default
    assert config_loader.get("ocr.non_existent", 123) == 123 
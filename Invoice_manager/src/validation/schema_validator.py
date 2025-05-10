"""
Schema Validator

This module validates extracted invoice data against the JSON schema.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import jsonschema
from jsonschema import validate, ValidationError

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SchemaValidator:
    """Validates extracted invoice data against a JSON schema."""
    
    def __init__(self, config: Dict):
        """
        Initialize the schema validator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.strict_mode = config["validation"]["strict_mode"]
        self.schema_path = Path(config["validation"]["schema"])
        
        # Load schema
        with open(self.schema_path, 'r') as f:
            self.schema = json.load(f)
        
        logger.info(f"Initialized schema validator with schema: {self.schema_path}")
    
    def validate(self, data: Dict) -> Dict:
        """
        Validate invoice data against the schema.
        
        Args:
            data: Invoice data to validate
            
        Returns:
            Validated data with any corrections or errors added to metadata
        """
        logger.info("Validating extracted invoice data against schema")
        
        # Copy data to avoid modifying original
        validated_data = data.copy()
        
        # Create or access metadata
        if "metadata" not in validated_data:
            validated_data["metadata"] = {}
        
        # Add validation metadata
        validated_data["metadata"]["validation_errors"] = []
        validated_data["metadata"]["validation_warnings"] = []
        
        # Check required fields
        self._check_required_fields(validated_data)
        
        # Format fields according to schema patterns
        self._format_fields(validated_data)
        
        # Perform schema validation
        try:
            # Remove metadata before validation (will add back later)
            temp_data = validated_data.copy()
            metadata = temp_data.pop("metadata", {})
            
            # Validate against schema
            validate(instance=temp_data, schema=self.schema)
            validated_data["metadata"]["validation_passed"] = True
            
            logger.info("Schema validation passed")
        
        except ValidationError as e:
            # Log validation error
            error_path = ".".join(str(p) for p in e.path)
            error_message = e.message
            
            logger.error(f"Schema validation failed: {error_path} - {error_message}")
            
            validated_data["metadata"]["validation_passed"] = False
            validated_data["metadata"]["validation_errors"].append({
                "path": error_path or "root",
                "message": error_message
            })
            
            # In strict mode, raise the error
            if self.strict_mode:
                raise ValidationError(f"Validation failed: {error_message}")
        
        return validated_data
    
    def _check_required_fields(self, data: Dict) -> None:
        """
        Check that all required fields are present.
        
        Args:
            data: Invoice data to check
        """
        if "required" not in self.schema:
            return
            
        for field in self.schema["required"]:
            if field not in data:
                error = f"Required field '{field}' is missing"
                logger.warning(error)
                
                data["metadata"]["validation_errors"].append({
                    "path": field,
                    "message": error
                })
                
                # Add placeholder for missing required field
                data[field] = self._get_default_value(field)
    
    def _format_fields(self, data: Dict) -> None:
        """
        Format fields according to schema patterns.
        
        Args:
            data: Invoice data to format
        """
        properties = self.schema.get("properties", {})
        
        for field, value in data.items():
            # Skip metadata and non-string fields
            if field == "metadata" or not isinstance(value, str) or field not in properties:
                continue
                
            # Get field schema
            field_schema = properties[field]
            
            # Apply formatting based on field type and pattern
            if field == "issue_date" and "pattern" in field_schema:
                data[field] = self._format_date(value)
            
            elif "total" in field.lower() or field == "vat_amount" or "price" in field.lower():
                data[field] = self._format_currency(value)
    
    def _format_date(self, date_str: str) -> str:
        """
        Format date string to DD/MM/YYYY.
        
        Args:
            date_str: Date string to format
            
        Returns:
            Formatted date string
        """
        # Clean up date string
        date_str = date_str.strip()
        
        # Replace hyphens with slashes
        date_str = date_str.replace("-", "/")
        
        # Ensure 2-digit day and month
        parts = date_str.split("/")
        if len(parts) == 3:
            day, month, year = parts
            
            # Ensure 2-digit day
            if len(day) == 1:
                day = f"0{day}"
                
            # Ensure 2-digit month
            if len(month) == 1:
                month = f"0{month}"
                
            # Convert 2-digit year to 4-digit if needed
            if len(year) == 2:
                year = f"20{year}"
                
            date_str = f"{day}/{month}/{year}"
        
        return date_str
    
    def _format_currency(self, currency_str: str) -> str:
        """
        Format currency string.
        
        Args:
            currency_str: Currency string to format
            
        Returns:
            Formatted currency string
        """
        # Clean up currency string
        currency_str = currency_str.strip()
        
        # Ensure decimal comma
        if "." in currency_str and "," not in currency_str:
            parts = currency_str.split(".")
            if len(parts) == 2 and len(parts[1]) <= 2:
                currency_str = currency_str.replace(".", ",")
        
        # Add € symbol if not present
        if "€" not in currency_str and "EUR" not in currency_str:
            currency_str = f"{currency_str} €"
        
        return currency_str
    
    def _get_default_value(self, field: str) -> Any:
        """
        Get default value for a field based on its type.
        
        Args:
            field: Field name
            
        Returns:
            Default value for the field
        """
        field_schema = self.schema.get("properties", {}).get(field, {})
        field_type = field_schema.get("type", "string")
        
        if field_type == "string":
            return "N/A"
        elif field_type == "number":
            return 0
        elif field_type == "integer":
            return 0
        elif field_type == "boolean":
            return False
        elif field_type == "array":
            return []
        elif field_type == "object":
            return {}
        else:
            return None 
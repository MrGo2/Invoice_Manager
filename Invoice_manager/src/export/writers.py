"""
Export Writers

This module provides exporters for saving extracted invoice data in different formats.
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import requests

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseWriter:
    """Base class for invoice data writers."""
    
    def write(self, data: Union[Dict, List[Dict]], output_path: Optional[str] = None) -> str:
        """
        Write invoice data to output.
        
        Args:
            data: Invoice data (single invoice or list)
            output_path: Path to write output (optional)
            
        Returns:
            Path or confirmation message for the output
        """
        raise NotImplementedError("Subclasses must implement write method")


class JSONWriter(BaseWriter):
    """Writer for JSON format output."""
    
    def write(self, data: Union[Dict, List[Dict]], output_path: Optional[str] = None) -> str:
        """
        Write invoice data to JSON file.
        
        Args:
            data: Invoice data (single invoice or list)
            output_path: Path to write JSON file (optional)
            
        Returns:
            Path to the written JSON file
        """
        # If output path not provided, generate one in the current directory
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"invoice_data_{timestamp}.json"
        
        # Ensure the directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write data to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported invoice data to JSON: {output_path}")
        return str(output_path)


class CSVWriter(BaseWriter):
    """Writer for CSV format output."""
    
    def write(self, data: Union[Dict, List[Dict]], output_path: Optional[str] = None) -> str:
        """
        Write invoice data to CSV file.
        
        Args:
            data: Invoice data (single invoice or list)
            output_path: Path to write CSV file (optional)
            
        Returns:
            Path to the written CSV file
        """
        # If output path not provided, generate one in the current directory
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"invoice_data_{timestamp}.csv"
        
        # Ensure the directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to list if single invoice
        if isinstance(data, dict):
            data_list = [data]
        else:
            data_list = data
        
        # Flatten the first invoice to get all field names
        flattened_fields = self._get_flattened_fields(data_list[0])
        
        # Write data to CSV file
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=flattened_fields)
            writer.writeheader()
            
            for invoice in data_list:
                # Flatten each invoice record
                flat_invoice = self._flatten_invoice(invoice)
                writer.writerow(flat_invoice)
        
        logger.info(f"Exported invoice data to CSV: {output_path}")
        return str(output_path)
    
    def _get_flattened_fields(self, invoice: Dict) -> List[str]:
        """
        Get flattened field names from invoice data.
        
        Args:
            invoice: Invoice data
            
        Returns:
            List of flattened field names
        """
        fields = []
        
        # Add all top-level fields except line_items and metadata
        for field in invoice:
            if field not in ["line_items", "metadata"]:
                fields.append(field)
        
        # Add line_item field prefixes if present
        if "line_items" in invoice and invoice["line_items"]:
            item = invoice["line_items"][0]
            for item_field in item:
                fields.append(f"line_item_1_{item_field}")
        
        return fields
    
    def _flatten_invoice(self, invoice: Dict) -> Dict:
        """
        Flatten invoice data for CSV output.
        
        Args:
            invoice: Invoice data
            
        Returns:
            Flattened invoice data
        """
        flattened = {}
        
        # Copy all top-level fields except line_items and metadata
        for field, value in invoice.items():
            if field not in ["line_items", "metadata"]:
                flattened[field] = value
        
        # Add line_items as flattened fields
        if "line_items" in invoice and invoice["line_items"]:
            for i, item in enumerate(invoice["line_items"], start=1):
                for item_field, item_value in item.items():
                    flattened[f"line_item_{i}_{item_field}"] = item_value
        
        return flattened


class WebhookWriter(BaseWriter):
    """Writer for webhook output."""
    
    def __init__(self, config: Dict):
        """
        Initialize the webhook writer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.webhook_config = config["export"]["webhook"]
        self.enabled = self.webhook_config["enabled"]
        self.url = self.webhook_config["url"]
        self.headers = self.webhook_config["headers"]
    
    def write(self, data: Union[Dict, List[Dict]], output_path: Optional[str] = None) -> str:
        """
        Send invoice data to webhook.
        
        Args:
            data: Invoice data (single invoice or list)
            output_path: Ignored for webhook
            
        Returns:
            Confirmation message for the webhook request
        """
        # Check if webhook is enabled
        if not self.enabled:
            logger.warning("Webhook is disabled in configuration")
            return "Webhook disabled"
        
        # Check if URL is configured
        if not self.url:
            logger.error("Webhook URL not configured")
            return "Webhook URL not configured"
        
        try:
            # Send data to webhook
            response = requests.post(
                self.url,
                json=data,
                headers=self.headers
            )
            
            # Log response
            if response.ok:
                logger.info(f"Webhook request successful: {response.status_code}")
                return f"Webhook request successful: {response.status_code}"
            else:
                logger.error(f"Webhook request failed: {response.status_code} - {response.text}")
                return f"Webhook request failed: {response.status_code}"
                
        except Exception as e:
            logger.error(f"Webhook request error: {str(e)}")
            return f"Webhook request error: {str(e)}" 
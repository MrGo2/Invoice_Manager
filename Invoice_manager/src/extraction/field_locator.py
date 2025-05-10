"""
Field Locator

This module extracts invoice fields from OCR text using regex patterns and heuristics.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class FieldLocator:
    """Extracts invoice field data using regex patterns and heuristics."""
    
    def __init__(self, config: Dict):
        """
        Initialize the field locator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Regex patterns for Spanish invoices
        self._patterns = {
            # Invoice number - common patterns like "Factura Nº: 12345" or "Nº de factura: 12345"
            "invoice_number": [
                r"(?:factura|fact|fra)(?:\s+)(?:n[º|°|o]?\.?:?\s*)([A-Za-z0-9\-\/]+)",
                r"(?:n[º|°|o]\.?:?\s*)(?:factura|fact|fra)(?:\s+)([A-Za-z0-9\-\/]+)",
                r"(?:n[º|°|o]\.?:?)(?:\s+)(?:de factura|del documento):?\s*([A-Za-z0-9\-\/]+)",
                r"(?:número de factura|núm. factura):?\s*([A-Za-z0-9\-\/]+)",
                r"(?:invoice number|invoice no):?\s*([A-Za-z0-9\-\/]+)",
                r"(?:factura|fact|fra)(?:[^\n\r]*):?\s*([A-Za-z0-9\-\/]+)"
            ],
            
            # Date - Spanish format DD/MM/YYYY or DD-MM-YYYY
            "issue_date": [
                r"(?:fecha(?:\s+)(?:de(?:\s+))?(?:factura|emisión|expedición)|fecha):?\s*(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4})",
                r"(?:date|emission date|invoice date):?\s*(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4})",
                r"(?:emitido el|fecha):?\s*(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4})",
                r"(?:factura|fact|fra)(?:[^\n\r]*):?(?:[^\n\r]*):?\s*(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4})"
            ],
            
            # Total amount - looking for currency symbols or words
            "total_eur": [
                r"(?:total factura|importe total|total a pagar|total):?\s*(\d{1,3}(?:[\s\.]?\d{3})*(?:,\d{1,2})?)(?:\s*€|\s*EUR)?",
                r"(?:total|importe)(?:[^\n\r]*):?\s*(\d{1,3}(?:[\s\.]?\d{3})*(?:,\d{1,2})?)(?:\s*€|\s*EUR)",
                r"(?:a pagar|total a pagar)(?:[^\n\r]*):?\s*(\d{1,3}(?:[\s\.]?\d{3})*(?:,\d{1,2})?)(?:\s*€|\s*EUR)?",
                r"(\d{1,3}(?:[\s\.]?\d{3})*(?:,\d{1,2})?)(?:\s*€|\s*EUR)(?:\s*total|\s*a pagar)"
            ],
            
            # VAT rate - common Spanish rates are 21%, 10%, 4%
            "vat_rate": [
                r"(?:iva|i\.v\.a\.|impuesto)(?:[^\n\r]*)(?:\s+)(\d{1,2}(?:,\d{1,2})?\s*%)",
                r"(\d{1,2}(?:,\d{1,2})?\s*%)(?:\s+)(?:iva|i\.v\.a\.|impuesto)",
                r"(?:tipo(?:\s+)(?:de(?:\s+))?(?:iva|impuesto)):?\s*(\d{1,2}(?:,\d{1,2})?\s*%)",
                r"(?:vat rate|tax rate):?\s*(\d{1,2}(?:,\d{1,2})?\s*%)"
            ],
            
            # VAT amount
            "vat_amount": [
                r"(?:iva|i\.v\.a\.|impuesto)(?:[^\n\r]*):?\s*(\d{1,3}(?:[\s\.]?\d{3})*(?:,\d{1,2})?)(?:\s*€|\s*EUR)?",
                r"(?:cuota(?:\s+)(?:de(?:\s+))?(?:iva|impuesto))(?:[^\n\r]*):?\s*(\d{1,3}(?:[\s\.]?\d{3})*(?:,\d{1,2})?)(?:\s*€|\s*EUR)?",
                r"(?:vat amount|tax amount):?\s*(\d{1,3}(?:[\s\.]?\d{3})*(?:,\d{1,2})?)(?:\s*€|\s*EUR)?"
            ],
            
            # Vendor name - typically at the top of the invoice
            "vendor_name": [
                r"(?:^|\n)([A-Z][A-Za-z0-9\s\.,]+)(?:\n|$)",
                r"(?:emisor|proveedor|vendedor|expedidor):?\s*([A-Z][A-Za-z0-9\s\.,]+)"
            ],
            
            # Tax ID (NIF/CIF) - Spanish format
            "vendor_tax_id": [
                r"(?:nif|cif|n\.i\.f\.|c\.i\.f\.|dni)(?:[^\n\r]*):?\s*([A-Z0-9]\d{7}[A-Z0-9])",
                r"(?:tax id|fiscal id|id fiscal)(?:[^\n\r]*):?\s*([A-Z0-9]\d{7}[A-Z0-9])"
            ],
            
            # Buyer name
            "buyer_name": [
                r"(?:cliente|destinatario|comprador|receptor):?\s*([A-Za-z0-9\s\.,]+)(?:\n|$)",
                r"(?:customer|client|buyer|recipient):?\s*([A-Za-z0-9\s\.,]+)(?:\n|$)"
            ],
            
            # Payment terms
            "payment_terms": [
                r"(?:forma(?:\s+)(?:de(?:\s+))?pago|condiciones(?:\s+)(?:de(?:\s+))?pago|pago):?\s*([^\n\r]+)(?:\n|$)",
                r"(?:payment terms|payment method|payment):?\s*([^\n\r]+)(?:\n|$)"
            ]
        }
        
        logger.info("Initialized field locator with heuristic patterns")
    
    def extract_fields(self, text: str) -> Dict:
        """
        Extract invoice fields from OCR text using regex patterns.
        
        Args:
            text: OCR extracted text
            
        Returns:
            Dictionary of extracted field values
        """
        logger.debug("Extracting fields from OCR text")
        
        # Normalize text: trim spaces, normalize line endings
        normalized_text = self._normalize_text(text)
        
        results = {}
        
        # Extract fields using regex patterns
        for field, patterns in self._patterns.items():
            value = self._extract_with_patterns(normalized_text, patterns)
            if value:
                results[field] = value
                logger.debug(f"Extracted {field}: {value}")
                
        # Try to extract line items if available
        line_items = self._extract_line_items(normalized_text)
        if line_items:
            results["line_items"] = line_items
            logger.debug(f"Extracted {len(line_items)} line items")
        
        # Add extraction metadata
        results["metadata"] = {
            "extraction_method": "regex_heuristics",
            "extraction_timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Extracted {len(results) - 1} invoice fields")  # -1 for metadata
        return results
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize OCR text for better pattern matching.
        
        Args:
            text: Raw OCR text
            
        Returns:
            Normalized text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Normalize spaces around common separators
        text = re.sub(r'\s*([:\-])\s*', r' \1 ', text)
        
        return text.strip()
    
    def _extract_with_patterns(self, text: str, patterns: List[str]) -> Optional[str]:
        """
        Extract field using a list of regex patterns.
        
        Args:
            text: OCR text to search
            patterns: List of regex patterns to try
            
        Returns:
            Extracted value or None if not found
        """
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and match.group(1):
                return match.group(1).strip()
        return None
    
    def _extract_line_items(self, text: str) -> Optional[List[Dict]]:
        """
        Extract line items from invoice text.
        
        Args:
            text: OCR text
            
        Returns:
            List of line item dictionaries if found, or None
        """
        # This is a simplified approach - actual implementation would be more complex
        # and would need to handle different invoice table formats
        
        # Look for potential table sections in the invoice
        table_pattern = r'(?:descripción|concepto|artículo|producto|servicio)(?:[^\n]+)(?:cantidad|cant|qty|ud)(?:[^\n]+)(?:precio|importe|p\.u\.)(?:[^\n]+)(?:total)(?:[^\n]+\n)((?:.*\n)+)'
        table_match = re.search(table_pattern, text, re.IGNORECASE)
        
        if not table_match:
            return None
            
        table_text = table_match.group(1)
        
        # Simple pattern for line items - this is a basic approach
        # More sophisticated parsing would be needed for real invoices
        item_pattern = r'([^\n]+?)(?:\s+)(\d+(?:,\d+)?)(?:\s+)(\d{1,3}(?:[\s\.]?\d{3})*(?:,\d{1,2})?)(?:\s*€)?(?:\s+)(\d{1,3}(?:[\s\.]?\d{3})*(?:,\d{1,2})?)(?:\s*€)?'
        items = []
        
        for match in re.finditer(item_pattern, table_text):
            if match and len(match.groups()) >= 4:
                items.append({
                    'description': match.group(1).strip(),
                    'qty': match.group(2).strip(),
                    'unit_price': match.group(3).strip(),
                    'line_total': match.group(4).strip()
                })
        
        return items if items else None 
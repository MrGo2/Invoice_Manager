#!/usr/bin/env python3
"""
Test error handling in process_single_invoice
"""

import sys
import json
from pathlib import Path

# Add the project root to path
sys.path.insert(0, '.')

from process_invoice import process_single_invoice

def test_error_handling():
    """Test error handling in process_single_invoice"""
    
    print("=== Testing Error Handling in process_single_invoice ===\n")
    
    # Test with empty PDF file
    print("Testing with empty PDF file...")
    result = process_single_invoice('test_error.pdf')
    
    # Analyze result
    print(f"Type of result: {type(result)}")
    print(f"Result is dict: {isinstance(result, dict)}")
    
    if isinstance(result, dict) and "metadata" in result:
        print(f"Contains error info: {result['metadata'].get('error') is not None}")
        print(f"Error type: {result['metadata'].get('error_type')}")
    
    # Print full result with pretty formatting
    print("\nFull result content:")
    print(json.dumps(result, indent=2, default=str))
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_error_handling() 
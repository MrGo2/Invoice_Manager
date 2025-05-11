import json
import os
import sys
from datetime import datetime

# Add the src directory to path for importing
# This might need adjustment based on your project's root and where manage.py is
# Assuming processors.py is in Invoice_manager/invoice_app/ and src is in Invoice_manager/src/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

# Import your existing processing code
# This may need to be adjusted based on your actual code structure
# from src.main import process_invoice as process_invoice_function
# Attempting a more specific import if main.py contains InvoiceProcessor class as seen in other files
try:
    from main import process_invoice as process_invoice_function # If process_invoice is a function in src/main.py
    # from main import InvoiceProcessor # If you use the InvoiceProcessor class directly
except ImportError as e:
    print(f"Error importing processing function/class from src.main: {e}")
    process_invoice_function = None
    # InvoiceProcessor = None

def process_invoice(invoice_id):
    """
    Process an uploaded invoice using the existing code.
    Updates the invoice status and extracted data in the database.
    """
    from .models import Invoice # Import here to avoid circular dependency if models import processors
    
    # Get the invoice object
    try:
        invoice = Invoice.objects.get(id=invoice_id)
    except Invoice.DoesNotExist:
        # Consider logging this event
        return False
    
    # Update status to processing
    invoice.status = 'processing'
    invoice.save()
    
    if not process_invoice_function:
        invoice.status = 'failed'
        invoice.error_message = "Processing function not available."
        invoice.save()
        return False
        
    try:
        # Get the file path
        file_path = invoice.file.path
        
        # Process the invoice using the existing code
        # Adjust this call based on your actual function signature
        result = process_invoice_function(file_path)
        
        # Store the result
        # Ensure result is serializable to JSON
        invoice.extracted_data = result # Assuming result is already a dict/JSON serializable
        invoice.status = 'completed'
        invoice.processed_date = datetime.now()
        invoice.save()
        
        return True
    except Exception as e:
        # Handle errors
        invoice.status = 'failed'
        invoice.error_message = str(e)
        invoice.save()
        # Consider logging the full traceback here
        return False 
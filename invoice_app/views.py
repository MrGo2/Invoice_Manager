from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Invoice
from .forms import InvoiceUploadForm
import os
import sys
import json

# Add the path to your invoice processor code
invoice_manager_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if invoice_manager_path not in sys.path:
    sys.path.append(invoice_manager_path)

# Import your invoice processing code
# Adjust the import path according to your project structure
try:
    from Invoice_manager.src.main import InvoiceProcessor
except ImportError:
    # Fallback message if the import fails
    print("Could not import InvoiceProcessor. Please check the path.")
    InvoiceProcessor = None # Define it as None so the app can still run

def home(request):
    # Get the 5 most recent invoices
    recent_invoices = Invoice.objects.order_by('-upload_date')[:5]
    return render(request, 'invoice_app/home.html', {'recent_invoices': recent_invoices})

def upload_invoice(request):
    if request.method == 'POST':
        form = InvoiceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            invoice = form.save()
            
            # Process the invoice in the same request (for simplicity)
            # In production, this should be done asynchronously
            if InvoiceProcessor: # Check if InvoiceProcessor was imported
                try:
                    process_invoice(invoice.id)
                    messages.success(request, 'Invoice uploaded and processed successfully!')
                except Exception as e:
                    messages.error(request, f'Error processing invoice: {str(e)}')
            else:
                messages.warning(request, 'Invoice uploaded but InvoiceProcessor is not available to process it.')
            
            return redirect('invoice_detail', invoice_id=invoice.id)
    else:
        form = InvoiceUploadForm()
    
    return render(request, 'invoice_app/upload.html', {'form': form})

def invoice_list(request):
    invoices = Invoice.objects.all().order_by('-upload_date')
    return render(request, 'invoice_app/list.html', {'invoices': invoices})

def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    return render(request, 'invoice_app/detail.html', {'invoice': invoice})

def process_invoice(invoice_id):
    """Process an invoice using your existing code"""
    invoice = Invoice.objects.get(id=invoice_id)
    invoice.status = 'processing'
    invoice.save()
    
    if not InvoiceProcessor:
        invoice.status = 'failed'
        invoice.save()
        print(f"InvoiceProcessor not available, cannot process invoice {invoice_id}")
        raise ImportError("InvoiceProcessor is not available.")

    try:
        # Initialize InvoiceProcessor
        processor = InvoiceProcessor()
        
        # Get the full path to the uploaded file
        file_path = invoice.file.path
        
        # Process the invoice
        result = processor.process(file_path)
        
        # Update the invoice with extracted data
        invoice.extracted_data = result
        invoice.status = 'completed'
        invoice.processed_date = timezone.now()
        
    except Exception as e:
        invoice.status = 'failed'
        print(f"Error processing invoice {invoice_id}: {str(e)}")
        raise
    
    invoice.save() 
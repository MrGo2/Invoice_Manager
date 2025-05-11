from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Invoice
from .forms import InvoiceUploadForm
import json
from .processors import process_invoice

def dashboard_view(request):
    # Count statistics
    total_invoices = Invoice.objects.count()
    completed = Invoice.objects.filter(status='completed').count()
    pending = Invoice.objects.filter(status='pending').count()
    failed = Invoice.objects.filter(status='failed').count()
    
    context = {
        'total_invoices': total_invoices,
        'completed': completed,
        'pending': pending,
        'failed': failed
    }
    return render(request, 'invoice_app/dashboard.html', context) # Changed template path

def invoice_list_view(request):
    invoices = Invoice.objects.all().order_by('-upload_date')
    return render(request, 'invoice_app/invoice_list.html', {'invoices': invoices}) # Changed template path

def invoice_detail_view(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    # Parse JSON data if available
    extracted_data = None
    if invoice.extracted_data:
        try:
            # If extracted_data is already a dict (from JSONField), no need to loads
            if isinstance(invoice.extracted_data, str):
                extracted_data = json.loads(invoice.extracted_data)
            else:
                extracted_data = invoice.extracted_data 
        except json.JSONDecodeError:
            extracted_data = None
    
    return render(request, 'invoice_app/invoice_detail.html', { # Changed template path
        'invoice': invoice,
        'extracted_data': extracted_data
    })

def upload_invoice_view(request):
    if request.method == 'POST':
        form = InvoiceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            invoice = form.save(commit=False)
            # file_name is handled by model's save method
            invoice.status = 'pending' # Initial status
            invoice.save()
            
            # Process the invoice
            # For now, process it directly - in production, use a task queue
            process_invoice(invoice.id) # Call the processing function
            
            return redirect(reverse('invoice_app:invoice_list')) # Corrected redirect
    else:
        form = InvoiceUploadForm()
    return render(request, 'invoice_app/upload.html', {'form': form}) # Changed template path 
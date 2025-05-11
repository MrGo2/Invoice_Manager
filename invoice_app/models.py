from django.db import models
import os
import uuid
from django.utils import timezone

def invoice_file_path(instance, filename):
    """Generate a unique file path for uploaded invoices."""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('invoices', filename)

class Invoice(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    file = models.FileField(upload_to=invoice_file_path)
    file_name = models.CharField(max_length=255, blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processed_date = models.DateTimeField(null=True, blank=True)
    extracted_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Invoice {self.id} - {self.file_name} ({self.status})"
    
    def save(self, *args, **kwargs):
        if not self.file_name and self.file:
            self.file_name = os.path.basename(self.file.name)
        super().save(*args, **kwargs)
    
    def mark_as_processing(self):
        self.status = 'processing'
        self.save(update_fields=['status'])
    
    def mark_as_completed(self, data):
        self.status = 'completed'
        self.extracted_data = data
        self.processed_date = timezone.now()
        self.save(update_fields=['status', 'extracted_data', 'processed_date'])
    
    def mark_as_failed(self, error_message):
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])

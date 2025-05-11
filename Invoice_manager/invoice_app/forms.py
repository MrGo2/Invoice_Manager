from django import forms
from .models import Invoice

class InvoiceUploadForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'hidden',
                'id': 'invoice_file',
                'accept': '.pdf,.jpg,.jpeg,.png'
            })
        } 
from django.urls import path
from . import views

app_name = 'invoice_app'  # Set the application namespace

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_invoice, name='upload_invoice'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
] 
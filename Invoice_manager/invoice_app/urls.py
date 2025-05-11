from django.urls import path
from . import views

app_name = 'invoice_app'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('invoices/', views.invoice_list_view, name='invoice_list'),
    path('invoices/<int:invoice_id>/', views.invoice_detail_view, name='invoice_detail'),
    path('upload/', views.upload_invoice_view, name='upload_invoice'),
] 
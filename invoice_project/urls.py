from django.contrib import admin
from django.urls import path, include # Make sure to import include
from django.conf import settings
from django.conf.urls.static import static
# Remove direct import of views from invoice_app if you are using include
# from invoice_app import views # This line might be removed or changed

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('invoice_app.urls')), # Include app URLs
    # path('', views.home, name='home'), # Old direct path
    # path('upload/', views.upload_invoice, name='upload_invoice'), # Old direct path
    # path('invoices/', views.invoice_list, name='invoice_list'), # Old direct path
    # path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'), # Old direct path
]

# Add this to serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
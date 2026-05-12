"""
==============================================================================
ARCHIVO: urls.py
==============================================================================
Propósito:
    Enrutador principal. El branding del admin se define SOLO en admin.py,
    no aquí, para evitar sobreescrituras.
==============================================================================
"""

from django.contrib import admin
from django.urls import path
from app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/app/dashboard/', views.dashboard_kpi, name='dashboard_kpi'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

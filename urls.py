"""
URL configuration for nexus project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from app import views
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "Panel KPI Nexus"  # El título principal en la barra azul
admin.site.site_title = "Admin Nexus"       # El texto que sale en la pestaña del navegador
admin.site.index_title = "Módulo de Administración" # El subtítulo principal

urlpatterns = [
    path('admin/app/dashboard/', views.dashboard_kpi, name='dashboard_kpi'),

    # 2. La ruta original del admin (debe ir debajo de la tuya)
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
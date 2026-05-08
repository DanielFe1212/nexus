"""
==============================================================================
ARCHIVO: admin.py
==============================================================================
Propósito:
    Configura y personaliza el panel de administración de Django.
    Define qué campos se ven en las listas, los filtros laterales y conecta
    scripts (JavaScript) y hojas de estilo (CSS) externos para mejorar la UI.
==============================================================================
"""

from django.contrib import admin
from django.shortcuts import redirect
from rangefilter.filters import DateRangeFilter
from django.urls import reverse


from .models import (
    Empresa, Sede, Proveedor,
    TipoFalla, Evento, ConfiguracionGlobal,
    EnlaceDashboard
)

# Branding global
admin.site.site_header = "Administración Grupo Carval"
admin.site.site_title = "Admin Carval"
admin.site.index_title = "Panel de Control - Eventos"


class BaseNexusAdmin(admin.ModelAdmin):
    """
    Base DRY para todos los modelos del admin:
    - Carga CSS y JS global
    - Permite extender sin romper layout
    """

    def has_add_permission(self, request, obj=None):
        return True  # Cambiar a False si quieres quitar el botón de añadir general

    class Media:
        css = {
            'all': (
                'css/base_admin.css',
                'css/layout_admin.css',
                'css/navigation_admin.css',
                'css/components_admin.css',
                'css/overrides_admin.css',
            )
        }
        js = (
            'js/custom_admin.js',
            'js/modulos/boton_eliminar.js',
        )


@admin.register(EnlaceDashboard)
class EnlaceDashboardAdmin(BaseNexusAdmin):
    def changelist_view(self, request, extra_context=None):
        return redirect('/admin/app/dashboard/')


@admin.register(Empresa, Sede, Proveedor, TipoFalla, ConfiguracionGlobal)
class GeneralAdmin(BaseNexusAdmin):
    pass


@admin.register(Evento)
class EventoAdmin(BaseNexusAdmin):

    list_display = (
        'get_empresa',
        'idsede',
        'idproveedor',
        'rol',
        'fecha_inicio',
        'fecha_fin',
        'duracion_horas',
        'duracion_minutos',
        'idtipo_falla'
    )

    class Media:
        js = (
            'js/reloj.js',
        )

    def get_empresa(self, obj):
        return obj.idsede.idempresa.nombre if obj.idsede and obj.idsede.idempresa else "-"

    get_empresa.short_description = "Empresa"
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
from .models import Empresa, Sede, Proveedor, TipoFalla, Evento, ConfiguracionGlobal
from django.shortcuts import redirect
from .models import EnlaceDashboard
from rangefilter.filters import DateRangeFilter

admin.site.site_header = "Administración Grupo Carval"
admin.site.site_title = "Admin Carval"
admin.site.index_title = "Panel de Control - Eventos"

@admin.register(EnlaceDashboard)
class EnlaceDashboardAdmin(admin.ModelAdmin):
    """ Botón de redirección hacia el Dashboard. """
    def changelist_view(self, request, extra_context=None):
        return redirect('/admin/app/dashboard/')

    def has_module_permission(self, request):
        return False

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(TipoFalla)
class TipoFallaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(ConfiguracionGlobal)
class ConfiguracionAdmin(admin.ModelAdmin):
    list_display = ('meta_disponibilidad', 'minutos_dia')

@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'idempresa', 'canal_primario', 'canal_secundario')
    list_filter = ('idempresa',)

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    """
    Controla la interfaz de registro de caídas y la inyección
    de calendarios Flatpickr en los campos de fecha.
    """
    list_display = (
        'get_empresa', 'idsede', 'idproveedor', 'rol',
        'fecha_inicio', 'fecha_fin', 'duracion_horas',
        'duracion_minutos', 'idtipo_falla'
    )
    list_filter = (
        'idsede__idempresa',
        'rol',
        ('fecha_inicio', DateRangeFilter),
    )
    search_fields = ('idsede__nombre',)

    exclude = ('duracion_horas', 'duracion_minutos')

    def get_empresa(self, obj):
        return obj.idsede.idempresa.nombre
    get_empresa.short_description = 'Empresa'

    class Media:
        css = {
            'all': (
                'https://cdnjs.cloudflare.com/ajax/libs/clockpicker/0.0.7/jquery-clockpicker.min.css',
                'https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css',
                'css/custom_admin.css',
            )
        }
        js = (
            'https://code.jquery.com/jquery-3.6.0.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/clockpicker/0.0.7/jquery-clockpicker.min.js',
            'https://cdn.jsdelivr.net/npm/flatpickr',
            'https://npmcdn.com/flatpickr/dist/l10n/es.js',
            'js/reloj.js',
            'js/custom_admin.js',
        )
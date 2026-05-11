"""
==============================================================================
ARCHIVO: admin.py
==============================================================================
Propósito:
    Configura y personaliza el panel de administración de Django.
    Define columnas visibles, filtros laterales, acciones y conecta
    los scripts (JS/CSS) externos definidos en BaseNexusAdmin (DRY).
==============================================================================
"""

from django.contrib import admin
from django.shortcuts import redirect
from rangefilter.filters import DateRangeFilterBuilder

from .models import (
    Empresa, Sede, Proveedor,
    TipoFalla, Evento, ConfiguracionGlobal,
    EnlaceDashboard
)

# --- Branding global ---
admin.site.site_header = "Administración Grupo Carval"
admin.site.site_title  = "Admin Carval"
admin.site.index_title = "Panel de Control - Eventos"


# ==============================================================================
# BASE DRY — Carga de CSS/JS compartido en todos los modelos
# ==============================================================================

class BaseNexusAdmin(admin.ModelAdmin):
    """
    Clase base para todos los ModelAdmin del proyecto.
    Centraliza la carga de CSS y JS para mantener DRY.
    """

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
            'js/modulos/filtros_toggle.js',
        )


# ==============================================================================
# ENLACE DASHBOARD — Redirección rápida desde el menú
# ==============================================================================

@admin.register(EnlaceDashboard)
class EnlaceDashboardAdmin(BaseNexusAdmin):
    def changelist_view(self, request, extra_context=None):
        return redirect('/admin/app/dashboard/')


# ==============================================================================
# EMPRESA
# ==============================================================================

@admin.register(Empresa)
class EmpresaAdmin(BaseNexusAdmin):
    list_display  = ('nombre',)
    search_fields = ('nombre',)
    list_filter   = ('nombre',)
    ordering      = ('nombre',)


# ==============================================================================
# PROVEEDOR
# ==============================================================================

@admin.register(Proveedor)
class ProveedorAdmin(BaseNexusAdmin):
    list_display  = ('nombre',)
    search_fields = ('nombre',)
    list_filter   = ('nombre',)
    ordering      = ('nombre',)


# ==============================================================================
# TIPO DE FALLA
# ==============================================================================

@admin.register(TipoFalla)
class TipoFallaAdmin(BaseNexusAdmin):
    list_display  = ('nombre',)
    search_fields = ('nombre',)
    ordering      = ('nombre',)


# ==============================================================================
# CONFIGURACIÓN GLOBAL
# ==============================================================================

@admin.register(ConfiguracionGlobal)
class ConfiguracionGlobalAdmin(BaseNexusAdmin):
    list_display = ('meta_disponibilidad', 'minutos_dia')


# ==============================================================================
# SEDE
# ==============================================================================

@admin.register(Sede)
class SedeAdmin(BaseNexusAdmin):
    list_display  = ('nombre', 'idempresa', 'pais', 'canal_primario', 'canal_secundario', 'canal_mpls')
    search_fields = ('nombre', 'idempresa__nombre', 'pais')
    list_filter   = ('idempresa', 'pais', 'canal_primario', 'canal_secundario', 'canal_mpls')
    ordering      = ('idempresa', 'nombre')


# ==============================================================================
# EVENTO — Con filtro de rango de fechas (rangefilter)
# ==============================================================================

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
        'idtipo_falla',
    )

    search_fields = ('idsede__nombre', 'idsede__idempresa__nombre', 'idproveedor__nombre')

    list_filter = (
        'idsede__idempresa',
        'rol',
        'idproveedor',
        'idtipo_falla',
        ('fecha_inicio', DateRangeFilterBuilder(title='Rango de Fecha Inicio')),
        ('fecha_fin',    DateRangeFilterBuilder(title='Rango de Fecha Fin')),
    )

    ordering = ('-fecha_inicio',)

    # Agrega JS del reloj/calendario ADEMÁS del de la clase base
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
            'js/modulos/filtros_toggle.js',
            'js/modulos/reloj.js',
        )

    def get_empresa(self, obj):
        return obj.idsede.idempresa.nombre if obj.idsede and obj.idsede.idempresa else '-'

    get_empresa.short_description = 'Empresa'
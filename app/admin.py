"""
==============================================================================
ARCHIVO: admin.py
==============================================================================
Propósito:
    - Configura el panel de administración.
    - PUNTO 5: EventoAdmin aplica permisos por propietario (solo admins
      pueden editar/eliminar eventos de otros usuarios).
    - PUNTO 6: Registra acciones de crear/editar/eliminar en LogAccion.
==============================================================================
"""

from django.contrib import admin
from django.shortcuts import redirect
from django import forms
from rangefilter.filters import DateRangeFilterBuilder

from .models import (
    Empresa, Sede, Proveedor, TipoFalla,
    Evento, ConfiguracionGlobal, EnlaceDashboard, LogAccion
)

# Branding — definido solo aquí (urls.py lo sobreescribía antes)
admin.site.site_header = "Administración Grupo Carval"
admin.site.site_title  = "Admin Carval"
admin.site.index_title = "Panel de Control"


# ==============================================================================
# UTILIDAD — Registrar acción en LogAccion
# ==============================================================================

def _log(request, accion, obj):
    """Crea un registro de auditoría para acciones CRUD."""
    from .models import LogAccion
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x_forwarded.split(',')[0].strip() if x_forwarded else request.META.get('REMOTE_ADDR')
    LogAccion.objects.create(
        usuario     = request.user,
        accion      = accion,
        modelo      = obj.__class__.__name__,
        objeto_id   = str(obj.pk),
        descripcion = str(obj),
        ip          = ip,
    )


# ==============================================================================
# BASE DRY — CSS/JS compartido
# ==============================================================================

class BaseNexusAdmin(admin.ModelAdmin):
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
            'js/modulos/boton_eliminar.js',
            'js/modulos/filtros_toggle.js',
        )

    # ── PUNTO 6: Hooks de auditoría CRUD ──────────────────────────
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        _log(request, 'EDITAR' if change else 'CREAR', obj)

    def delete_model(self, request, obj):
        _log(request, 'ELIMINAR', obj)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            _log(request, 'ELIMINAR', obj)
        super().delete_queryset(request, queryset)


# ==============================================================================
# ENLACE DASHBOARD — sin aparecer en el menú
# ==============================================================================

@admin.register(EnlaceDashboard)
class EnlaceDashboardAdmin(BaseNexusAdmin):
    def changelist_view(self, request, extra_context=None):
        return redirect('/admin/app/dashboard/')

    def has_add_permission(self, request):
        return False

    def has_module_perms(self, request):
        return False


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
# EVENTO
# PUNTO 1: Widgets nativos del navegador para fecha y hora
# PUNTO 2: Filtrado dinámico de Idproveedor según Idsede seleccionada
# PUNTO 5: Permisos por propietario
# PUNTO 6: Auditoría heredada de BaseNexusAdmin + auto-asignar creado_por
# ==============================================================================

class EventoForm(forms.ModelForm):
    """
    Form personalizado para el Evento.
    Usa los widgets HTML5 nativos del navegador para fecha y hora:
        - <input type="date">  → calendario nativo del navegador
        - <input type="time">  → reloj nativo del navegador
    Ventajas:
      - UX consistente con el navegador del operador (Chrome/Edge/Firefox).
      - No depende del jQuery del admin antiguo de Django.
      - Mejor accesibilidad y soporte móvil.
    """
    class Meta:
        model  = Evento
        fields = '__all__'
        widgets = {
            'fecha_inicio': forms.SplitDateTimeWidget(
                date_attrs={'type': 'date', 'class': 'input-fecha-nativo'},
                time_attrs={'type': 'time', 'class': 'input-hora-nativo', 'step': 60},
            ),
            'fecha_fin': forms.SplitDateTimeWidget(
                date_attrs={'type': 'date', 'class': 'input-fecha-nativo'},
                time_attrs={'type': 'time', 'class': 'input-hora-nativo', 'step': 60},
            ),
        }


@admin.register(Evento)
class EventoAdmin(BaseNexusAdmin):

    form = EventoForm                                       # Punto 1 — widgets nativos

    list_display = (
        'get_empresa', 'idsede', 'idproveedor', 'rol',
        'fecha_inicio', 'fecha_fin',
        'duracion_horas', 'duracion_minutos',
        'idtipo_falla', 'creado_por',
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

    ordering        = ('-fecha_inicio',)
    readonly_fields = ('creado_por',)

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
            'js/modulos/boton_eliminar.js',
            'js/modulos/filtros_toggle.js',
            'js/modulos/reloj.js',
            'js/modulos/evento_proveedores.js',             # Punto 2 — filtro dinámico
        )

    # ── Empresa en columna ──────────────────────────────────────────
    def get_empresa(self, obj):
        return obj.idsede.idempresa.nombre if obj.idsede and obj.idsede.idempresa else '-'
    get_empresa.short_description = 'Empresa'

    # ── PUNTO 2: Filtrar idproveedor según la sede al EDITAR ────────
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Al cargar el form:
        - Si estamos editando un Evento, idsede tiene un valor y filtramos
          idproveedor a los 3 canales de esa sede.
        - Si es un Evento nuevo, mostramos todos los proveedores; el JS
          evento_proveedores.js se encarga de filtrarlos dinámicamente
          al elegir sede.
        """
        if db_field.name == 'idproveedor':
            sede_id = None
            if request.resolver_match and 'object_id' in request.resolver_match.kwargs:
                try:
                    evento_id = request.resolver_match.kwargs['object_id']
                    ev = Evento.objects.select_related(
                        'idsede__canal_primario',
                        'idsede__canal_secundario',
                        'idsede__canal_mpls'
                    ).get(pk=evento_id)
                    sede_id = ev.idsede_id
                except Evento.DoesNotExist:
                    pass

            if sede_id:
                try:
                    sede = Sede.objects.select_related(
                        'canal_primario', 'canal_secundario', 'canal_mpls'
                    ).get(pk=sede_id)
                    ids = [
                        c.pk for c in (sede.canal_primario, sede.canal_secundario, sede.canal_mpls)
                        if c is not None
                    ]
                    kwargs['queryset'] = Proveedor.objects.filter(pk__in=ids)
                except Sede.DoesNotExist:
                    pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # ── PUNTO 5: Solo ver sus propios eventos (no admins) ──────────
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(creado_por=request.user)

    # ── PUNTO 5: Solo puede editar/eliminar sus propios eventos ────
    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user.is_superuser:
            return True
        return obj.creado_por == request.user

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user.is_superuser:
            return True
        return obj.creado_por == request.user

    # ── PUNTO 5 + 6: Auto-asignar creado_por al guardar ────────────
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
        from .models import LogAccion
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded.split(',')[0].strip() if x_forwarded else request.META.get('REMOTE_ADDR')
        LogAccion.objects.create(
            usuario     = request.user,
            accion      = 'EDITAR' if change else 'CREAR',
            modelo      = 'Evento',
            objeto_id   = str(obj.pk),
            descripcion = str(obj),
            ip          = ip,
        )


# ==============================================================================
# PUNTO 6 — LOG DE ACCIONES (solo lectura para admins)
# ==============================================================================

@admin.register(LogAccion)
class LogAccionAdmin(admin.ModelAdmin):
    """
    Tabla de auditoría. Solo superusuarios pueden verla.
    Nadie puede editar ni eliminar registros de auditoría.
    """
    list_display  = ('fecha', 'usuario', 'accion', 'modelo', 'objeto_id', 'descripcion', 'ip')
    list_filter   = ('accion', 'modelo', 'usuario')
    search_fields = ('usuario__username', 'descripcion', 'ip')
    ordering      = ('-fecha',)
    readonly_fields = ('fecha', 'usuario', 'accion', 'modelo', 'objeto_id', 'descripcion', 'ip')

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
            'js/modulos/filtros_toggle.js',
        )

    def has_add_permission(self, request):
        return False  # Nadie puede crear logs manualmente

    def has_delete_permission(self, request, obj=None):
        return False  # Nadie puede borrar logs

    def has_change_permission(self, request, obj=None):
        return False  # Nadie puede editar logs

    def has_module_perms(self, request):
        return request.user.is_superuser  # Solo superusuarios ven el módulo

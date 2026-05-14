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
# UTILIDAD — Detectar si el usuario es Administrador
# ==============================================================================

def es_administrador(user):
    """
    True si el usuario:
      - Es superuser de Django (heredado), o
      - Pertenece al grupo 'Administrador'.
    Mantenemos esta función centralizada por si mañana cambia la lógica.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name='Administrador').exists()


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
# BASE DRY — CSS/JS compartido + lógica de permisos por rol
# ==============================================================================

class BaseNexusAdmin(admin.ModelAdmin):
    """
    Base para todos los ModelAdmin del proyecto.
    Por defecto un Operador (no-Administrador) solo puede VER los registros
    de los modelos que heredan de esta base.
    EventoAdmin sobreescribe estos métodos porque sí permite crear/editar
    sus propios eventos.
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
            'js/modulos/boton_eliminar.js',
            'js/modulos/filtros_toggle.js',
        )

    # ── Lógica de roles: Operador solo ve, no crea/edita/borra ───
    # (EventoAdmin sobreescribirá estos métodos)
    def has_add_permission(self, request):
        return es_administrador(request.user)

    def has_change_permission(self, request, obj=None):
        # Permitir abrir la página de detalle en modo lectura.
        # Django muestra el form pero todos los inputs salen disabled si
        # readonly_fields cubre todo. Mejor sobreescribir get_readonly_fields.
        return True if es_administrador(request.user) else False

    def has_delete_permission(self, request, obj=None):
        return es_administrador(request.user)

    def get_readonly_fields(self, request, obj=None):
        """
        Para no-Administradores, TODOS los campos son de solo lectura.
        Así pueden entrar al registro y ver detalles sin editar nada.
        """
        if es_administrador(request.user):
            return super().get_readonly_fields(request, obj)
        # Devolver todos los campos del modelo como readonly
        if obj is not None:
            return [f.name for f in obj._meta.fields]
        return super().get_readonly_fields(request, obj)

    # ── Hooks de auditoría CRUD ──────────────────────────────────
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
# PUNTO 1: Calendario Flatpickr y reloj custom (vía reloj.js + flatpickr.js)
# PUNTO 2: Filtrado dinámico de Idproveedor según Idsede seleccionada
# PUNTO 5: Permisos por propietario
# PUNTO 6: Auditoría heredada de BaseNexusAdmin + auto-asignar creado_por
# ==============================================================================

@admin.register(Evento)
class EventoAdmin(BaseNexusAdmin):

    # Nota: usamos los widgets clásicos del admin (AdminSplitDateTime)
    # porque Flatpickr/ClockPicker se enganchan sobre las clases CSS
    # .vDateField y .vTimeField que esos widgets le ponen al input.
    # No definimos `form` personalizado para no perder esas clases.

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
                'css/vendor/flatpickr.min.css',             # Flatpickr CSS
                'css/overrides_admin.css',                  # último — para que ganen nuestros estilos
            )
        }
        js = (
            'js/vendor/flatpickr.min.js',                   # Flatpickr core
            'js/vendor/flatpickr.es.min.js',                # Locale español
            'js/modulos/boton_eliminar.js',
            'js/modulos/filtros_toggle.js',
            'js/modulos/reloj.js',                          # debe ir DESPUÉS de flatpickr
            'js/modulos/evento_proveedores.js',
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

    # ── Solo ver sus propios eventos (no Administradores) ─────────
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if es_administrador(request.user):
            return qs
        return qs

    # ── EventoAdmin SOBREESCRIBE las restricciones de BaseNexusAdmin ──
    # Aquí los Operadores SÍ pueden crear y editar/borrar sus propios.

    def has_add_permission(self, request):
        # Cualquier usuario autenticado del staff puede CREAR eventos
        return request.user.is_authenticated

    def has_change_permission(self, request, obj=None):
        # Listado siempre se puede ver
        if obj is None:
            return True
        if es_administrador(request.user):
            return True
        # Operador: solo edita los SUYOS
        return obj.creado_por == request.user

    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        if es_administrador(request.user):
            return True
        return obj.creado_por == request.user

    def get_readonly_fields(self, request, obj=None):
        """
        - Administrador: campos normales (solo creado_por es readonly).
        - Operador editando un evento ajeno: TODOS los campos readonly.
        - Operador editando un evento propio: campos normales.
        """
        if es_administrador(request.user):
            return ('creado_por',)
        if obj is not None and obj.creado_por != request.user:
            return [f.name for f in obj._meta.fields]
        return ('creado_por',)

    # ── Auto-asignar creado_por al guardar ─────────────────────────
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
        return es_administrador(request.user)  # Solo Administradores ven el módulo

    def has_view_permission(self, request, obj=None):
        return es_administrador(request.user)

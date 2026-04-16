from django.contrib import admin
from .models import Empresa, Sede, Proveedor, TipoFalla, Evento, ConfiguracionGlobal

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    # Si te da error aquí, cambia 'idempresa' por 'pk'
    list_display = ('nombre',)

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(TipoFalla)
class TipoFallaAdmin(admin.ModelAdmin):
    # Quitamos 'idtipo_falla' y dejamos 'nombre' para ir a lo seguro
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
    list_display = (
        'get_empresa',
        'idsede',
        'idproveedor', # CORREGIDO: antes decía idprovider
        'rol',
        'fecha_inicio',
        'fecha_fin',
        'duracion_horas',
        'duracion_minutos',
        'idtipo_falla'
    )
    list_filter = ('idsede__idempresa', 'rol', 'fecha_inicio')
    search_fields = ('idsede__nombre',)

    def get_empresa(self, obj):
        return obj.idsede.idempresa.nombre
    get_empresa.short_description = 'Empresa'
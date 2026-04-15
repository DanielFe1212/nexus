from django.contrib import admin
from .models import Empresa, Sede, Proveedor, Evento, TipoFalla, ConfiguracionGlobal

admin.site.register(Empresa)
admin.site.register(Sede)
admin.site.register(Proveedor)
admin.site.register(TipoFalla)
admin.site.register(ConfiguracionGlobal)

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('idsede', 'idproveedor', 'idtipo_falla', 'fecha_inicio', 'duracion_horas', 'periodo')
    readonly_fields = ('duracion_minutos', 'duracion_horas')
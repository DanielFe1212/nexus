from django.contrib import admin
from .models import Empresa, Sede, Proveedor, Inventario, Evento

# Registro sencillo de los modelos
admin.site.register(Empresa)
admin.site.register(Sede)
admin.site.register(Proveedor)
admin.site.register(Inventario)

# Opcional: Registro avanzado para Evento (para ver las columnas calculadas)
@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    # Definimos qué columnas se verán en la lista principal
    list_display = ('idsede', 'idproveedor', 'fecha_inicio', 'periodo', 'duracion_horas')
    # Filtros laterales
    list_filter = ('idsede', 'idproveedor')
"""
Migración: crear los grupos Administrador y Operador con sus permisos.

Se ejecuta una sola vez con: python manage.py migrate

Grupos creados:
  - Administrador: todos los permisos sobre todos los modelos (equivalente a is_superuser
    en cuanto a permisos de modelo, pero respeta el flag is_superuser para acceso
    al módulo LogAccion).
  - Operador: permisos limitados según los requisitos:
      * Evento → add, change, delete, view (pero la lógica del admin limita
        change/delete a SUS PROPIOS eventos vía permisos por objeto).
      * Empresa, Sede, Proveedor, TipoFalla, ConfiguracionGlobal → solo `view`.
      * LogAccion → ningún permiso (módulo invisible).
      * User, Group → ningún permiso.
"""

from django.db import migrations


# ── Mapa de permisos por grupo ───────────────────────────────────────────────
# Formato: {grupo: {modelo_lower: ['add', 'change', 'delete', 'view']}}
PERMISOS = {
    'Administrador': {
        # Todos los permisos sobre todos los modelos de la app
        'empresa':              ['add', 'change', 'delete', 'view'],
        'sede':                 ['add', 'change', 'delete', 'view'],
        'proveedor':            ['add', 'change', 'delete', 'view'],
        'tipofalla':            ['add', 'change', 'delete', 'view'],
        'evento':               ['add', 'change', 'delete', 'view'],
        'configuracionglobal':  ['add', 'change', 'delete', 'view'],
        'logaccion':            ['view'],  # Solo lectura — la tabla es append-only
    },
    'Operador': {
        # Solo en Evento puede CRUD; en el resto solo VER.
        # La restricción "solo SUS propios eventos para editar/borrar" se aplica
        # en EventoAdmin con has_change_permission / has_delete_permission.
        'evento':               ['add', 'change', 'delete', 'view'],
        'empresa':              ['view'],
        'sede':                 ['view'],
        'proveedor':            ['view'],
        'tipofalla':            ['view'],
        'configuracionglobal':  ['view'],
        # logaccion: deliberadamente NO listado — el grupo no tiene ningún permiso
        # sobre él, por lo que el módulo no aparece en el sidebar.
    },
}


def crear_grupos(apps, schema_editor):
    Group       = apps.get_model('auth', 'Group')
    Permission  = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    for nombre_grupo, modelos in PERMISOS.items():
        grupo, _ = Group.objects.get_or_create(name=nombre_grupo)
        grupo.permissions.clear()  # idempotente: limpiar y volver a asignar

        for modelo, acciones in modelos.items():
            try:
                ct = ContentType.objects.get(app_label='app', model=modelo)
            except ContentType.DoesNotExist:
                continue

            for accion in acciones:
                codename = f"{accion}_{modelo}"
                try:
                    p = Permission.objects.get(content_type=ct, codename=codename)
                    grupo.permissions.add(p)
                except Permission.DoesNotExist:
                    # Puede ocurrir si la migración corre antes de que Django
                    # cree los permisos del modelo. Es seguro ignorar.
                    pass


def revertir_grupos(apps, schema_editor):
    """
    Si se reverte la migración, eliminamos los grupos.
    Los usuarios asignados quedan sin grupo pero no se eliminan.
    """
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['Administrador', 'Operador']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('app',  '0010_logaccion_evento_creado_por'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(crear_grupos, reverse_code=revertir_grupos),
    ]

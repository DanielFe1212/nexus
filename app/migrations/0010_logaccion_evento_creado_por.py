"""
Migración 0010
- Agrega campo creado_por a Evento (FK a auth.User)
- Crea modelo LogAccion para auditoría
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_sede_nodo_central_mpls'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Nuevo campo en Evento
        migrations.AddField(
            model_name='evento',
            name='creado_por',
            field=models.ForeignKey(
                blank=True, editable=False, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='eventos_creados',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Creado por',
            ),
        ),
        # Modelo de auditoría
        migrations.CreateModel(
            name='LogAccion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accion', models.CharField(
                    choices=[
                        ('LOGIN', 'Inicio de sesión'),
                        ('LOGOUT', 'Cierre de sesión'),
                        ('LOGIN_FAIL', 'Intento fallido de login'),
                        ('CREAR', 'Creación'),
                        ('EDITAR', 'Edición'),
                        ('ELIMINAR', 'Eliminación'),
                    ],
                    max_length=20,
                )),
                ('modelo',      models.CharField(blank=True, help_text='Nombre del modelo afectado', max_length=50, null=True)),
                ('objeto_id',   models.CharField(blank=True, help_text='ID del objeto afectado', max_length=50, null=True)),
                ('descripcion', models.TextField(blank=True, help_text='Detalle legible de la acción', null=True)),
                ('ip',          models.GenericIPAddressField(blank=True, null=True)),
                ('fecha',       models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='log_acciones',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Log de Acción',
                'verbose_name_plural': 'Logs de Acciones',
                'ordering': ['-fecha'],
            },
        ),
    ]

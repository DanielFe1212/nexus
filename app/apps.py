"""
==============================================================================
ARCHIVO: apps.py
==============================================================================
Propósito:
    Configuración de la app. Conecta los signals al iniciar Django.
==============================================================================
"""

from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'app'

    def ready(self):
        import app.signals  # noqa: F401 — conecta los receivers al arrancar

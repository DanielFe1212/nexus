"""
==============================================================================
ARCHIVO: signals.py
==============================================================================
Propósito:
    Escucha eventos del sistema (login, logout, login fallido) y los registra
    automáticamente en la tabla LogAccion.
    Los cambios sobre modelos (crear/editar/eliminar) se registran desde admin.py.
==============================================================================
"""

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

from .models import LogAccion


def _get_ip(request):
    """Extrae la IP real del cliente, considerando proxies."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    LogAccion.objects.create(
        usuario     = user,
        accion      = 'LOGIN',
        descripcion = f"Inicio de sesión: {user.username}",
        ip          = _get_ip(request),
    )


@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    LogAccion.objects.create(
        usuario     = user,
        accion      = 'LOGOUT',
        descripcion = f"Cierre de sesión: {user.username if user else 'desconocido'}",
        ip          = _get_ip(request),
    )


@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    LogAccion.objects.create(
        usuario     = None,
        accion      = 'LOGIN_FAIL',
        descripcion = f"Intento fallido con usuario: {credentials.get('username', '?')}",
        ip          = _get_ip(request),
    )

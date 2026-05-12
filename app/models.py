"""
==============================================================================
ARCHIVO: models.py
==============================================================================
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Empresa(models.Model):
    idempresa = models.AutoField(primary_key=True)
    nombre    = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name        = "Empresa"
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    idproveedor = models.AutoField(primary_key=True)
    nombre      = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name        = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.nombre


class Sede(models.Model):
    idsede    = models.AutoField(primary_key=True)
    idempresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='sedes')
    nombre    = models.CharField(max_length=50)
    ciudad    = models.CharField(max_length=30, blank=True, null=True)
    pais      = models.CharField(max_length=30, blank=True, null=True)

    canal_primario   = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='sedes_primario',   null=True, blank=True, verbose_name="Canal Primario")
    canal_secundario = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='sedes_secundario', null=True, blank=True, verbose_name="Canal Secundario")
    canal_mpls       = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='sedes_mpls',       null=True, blank=True, verbose_name="Canal MPLS")

    nodo_central_mpls = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sedes_hijas_mpls', verbose_name="Nodo Padre MPLS (Topología Estrella)",
        help_text="Si esta sede pierde MPLS cuando otra sede principal se cae, selecciona aquí la sede principal."
    )

    class Meta:
        verbose_name        = "Sede"
        verbose_name_plural = "Sedes"

    def __str__(self):
        return f"{self.nombre} ({self.idempresa.nombre})"


class TipoFalla(models.Model):
    nombre      = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name        = "Tipo de Falla"
        verbose_name_plural = "Tipos de Fallas"

    def __str__(self):
        return self.nombre


class Evento(models.Model):
    """
    Registra caídas de canal.
    creado_por: usuario que registró el evento (para control de permisos).
    """
    idevento    = models.AutoField(primary_key=True)
    idsede      = models.ForeignKey(Sede,      on_delete=models.CASCADE)
    idproveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)

    ROL_CHOICES = [('Principal', 'Principal'), ('Respaldo', 'Respaldo'), ('MPLS', 'MPLS')]
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, blank=True, null=True)

    fecha_inicio     = models.DateTimeField()
    fecha_fin        = models.DateTimeField(blank=True, null=True)
    duracion_horas   = models.FloatField(blank=True, null=True)
    duracion_minutos = models.IntegerField(blank=True, null=True)
    idtipo_falla     = models.ForeignKey(TipoFalla, on_delete=models.SET_NULL, null=True, blank=True)
    ticket_proveedor = models.CharField(max_length=50, blank=True, null=True)
    observaciones    = models.TextField(blank=True, null=True)

    # ── PUNTO 5: control de propiedad ──────────────────────────────
    creado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='eventos_creados', verbose_name="Creado por",
        editable=False  # No aparece en el formulario del admin
    )

    class Meta:
        verbose_name        = "Evento"
        verbose_name_plural = "Eventos"

    def save(self, *args, **kwargs):
        # Auto-detectar rol si no está definido
        if not self.rol:
            if self.idsede.canal_mpls       and self.idproveedor == self.idsede.canal_mpls:
                self.rol = "MPLS"
            elif self.idsede.canal_primario  and self.idproveedor == self.idsede.canal_primario:
                self.rol = "Principal"
            elif self.idsede.canal_secundario and self.idproveedor == self.idsede.canal_secundario:
                self.rol = "Respaldo"

        # Calcular duración automáticamente
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_fin < self.fecha_inicio:
                raise ValidationError("La fecha de fin no puede ser anterior a la de inicio.")
            delta            = self.fecha_fin - self.fecha_inicio
            minutos          = int(delta.total_seconds() / 60)
            self.duracion_minutos = minutos
            self.duracion_horas   = round(minutos / 60.0, 2)
        else:
            self.duracion_minutos = None
            self.duracion_horas   = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Evento {self.idevento} - {self.idsede}"


class ConfiguracionGlobal(models.Model):
    meta_disponibilidad = models.FloatField(default=0.99, help_text="Ejemplo: 0.99 para 99%")
    minutos_dia         = models.IntegerField(default=1440, help_text="Minutos en un día (24h = 1440)")

    class Meta:
        verbose_name        = "Configuración Global"
        verbose_name_plural = "Configuración Global"


class EnlaceDashboard(models.Model):
    class Meta:
        verbose_name        = " Ver Dashboard Completo"
        verbose_name_plural = " Ver Dashboard Completo"
        managed             = False


# ==============================================================================
# PUNTO 6 — AUDITORÍA DE ACCIONES
# Registra: login, logout, crear/editar/eliminar evento y cualquier modelo.
# ==============================================================================

class LogAccion(models.Model):
    """
    Tabla de auditoría centralizada.
    Registrada automáticamente vía signals (signals.py) y middleware.
    No se edita manualmente.
    """

    ACCION_CHOICES = [
        ('LOGIN',    'Inicio de sesión'),
        ('LOGOUT',   'Cierre de sesión'),
        ('LOGIN_FAIL', 'Intento fallido de login'),
        ('CREAR',    'Creación'),
        ('EDITAR',   'Edición'),
        ('ELIMINAR', 'Eliminación'),
    ]

    usuario     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='log_acciones')
    accion      = models.CharField(max_length=20, choices=ACCION_CHOICES)
    modelo      = models.CharField(max_length=50, blank=True, null=True, help_text="Nombre del modelo afectado")
    objeto_id   = models.CharField(max_length=50, blank=True, null=True, help_text="ID del objeto afectado")
    descripcion = models.TextField(blank=True, null=True, help_text="Detalle legible de la acción")
    ip          = models.GenericIPAddressField(null=True, blank=True)
    fecha       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Log de Acción"
        verbose_name_plural = "Logs de Acciones"
        ordering            = ['-fecha']

    def __str__(self):
        usuario = self.usuario.username if self.usuario else "Anónimo"
        return f"[{self.fecha:%Y-%m-%d %H:%M}] {usuario} — {self.get_accion_display()}"

"""
==============================================================================
ARCHIVO: models.py
==============================================================================
Propósito:
    Define la estructura de la base de datos (Modelos/Tablas) usando el ORM de Django.
    Cada clase representa una tabla en la base de datos y cada atributo una columna.
==============================================================================
"""

from django.db import models
from django.core.exceptions import ValidationError

class Empresa(models.Model):
    """
    MODELO: Empresa
    Almacena las diferentes compañías u organizaciones que gestiona el sistema.
    """
    idempresa = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    """
    MODELO: Proveedor
    Almacena los ISP o proveedores de servicios de telecomunicaciones.
    """
    idproveedor = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.nombre


class Sede(models.Model):
    """
    MODELO: Sede
    Representa una ubicación física de una Empresa.
    """
    idsede = models.AutoField(primary_key=True)
    idempresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='sedes')
    nombre = models.CharField(max_length=50)
    ciudad = models.CharField(max_length=30, blank=True, null=True)
    pais = models.CharField(max_length=30, blank=True, null=True)

    canal_primario = models.ForeignKey(
        Proveedor, on_delete=models.PROTECT, related_name='sedes_primario',
        null=True, blank=True, verbose_name="Canal Primario"
    )
    canal_secundario = models.ForeignKey(
        Proveedor, on_delete=models.PROTECT, related_name='sedes_secundario',
        null=True, blank=True, verbose_name="Canal Secundario"
    )
    canal_mpls = models.ForeignKey(
        Proveedor, on_delete=models.PROTECT, related_name='sedes_mpls',
        null=True, blank=True, verbose_name="Canal MPLS"
    )

    # 🔥 LA SOLUCIÓN MÁGICA:
    nodo_central_mpls = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sedes_hijas_mpls', verbose_name="Nodo Padre MPLS (Topología Estrella)",
        help_text="Si esta sede pierde MPLS cuando otra sede principal se cae, selecciona aquí la sede principal."
    )

    class Meta:
        verbose_name = "Sede"
        verbose_name_plural = "Sedes"

    def __str__(self):
        return f"{self.nombre} ({self.idempresa.nombre})"


class TipoFalla(models.Model):
    """
    MODELO: TipoFalla
    Catálogo de las posibles razones por las que ocurre un evento de indisponibilidad.
    """
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Tipo de Falla"
        verbose_name_plural = "Tipos de Fallas"

    def __str__(self):
        return self.nombre


class Evento(models.Model):
    """
    MODELO: Evento
    Registra las caídas o indisponibilidades de un canal específico en una sede.
    """
    idevento = models.AutoField(primary_key=True)
    idsede = models.ForeignKey(Sede, on_delete=models.CASCADE)
    idproveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)

    ROL_CHOICES = [('Principal', 'Principal'), ('Respaldo', 'Respaldo'), ('MPLS', 'MPLS')]
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, blank=True, null=True)

    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(blank=True, null=True)
    duracion_horas = models.FloatField(blank=True, null=True)
    duracion_minutos = models.IntegerField(blank=True, null=True)
    idtipo_falla = models.ForeignKey(TipoFalla, on_delete=models.SET_NULL, null=True, blank=True)
    ticket_proveedor = models.CharField(max_length=50, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"

    def save(self, *args, **kwargs):
        """
        SOBREESCRITURA DE SAVE:
        Asigna el rol automáticamente y calcula los minutos de duración.
        """
        if not self.rol:
            if self.idsede.canal_mpls and self.idproveedor == self.idsede.canal_mpls:
                self.rol = "MPLS"
            elif self.idsede.canal_primario and self.idproveedor == self.idsede.canal_primario:
                self.rol = "Principal"
            elif self.idsede.canal_secundario and self.idproveedor == self.idsede.canal_secundario:
                self.rol = "Respaldo"

        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_fin < self.fecha_inicio:
                raise ValidationError("La fecha de fin no puede ser anterior a la de inicio.")
            delta = self.fecha_fin - self.fecha_inicio
            minutos = int(delta.total_seconds() / 60)
            self.duracion_minutos = minutos
            self.duracion_horas = round(minutos / 60.0, 2)
        else:
            self.duracion_minutos = None
            self.duracion_horas = None

        super().save(*args, **kwargs)


class ConfiguracionGlobal(models.Model):
    """
    MODELO: ConfiguracionGlobal
    Parámetros base del sistema (SLA Meta).
    """
    meta_disponibilidad = models.FloatField(default=0.99, help_text="Ejemplo: 0.99 para 99%")
    minutos_dia = models.IntegerField(default=1440, help_text="Minutos en un día (24h = 1440)")

    class Meta:
        verbose_name = "Configuración Global"
        verbose_name_plural = "Configuración Global"

class EnlaceDashboard(models.Model):
    """
    MODELO FANTASMA: EnlaceDashboard
    Crea el botón de acceso directo en el panel administrador.
    """
    class Meta:
        verbose_name = " Ver Dashboard Completo"
        verbose_name_plural = " Ver Dashboard Completo"
        managed = False
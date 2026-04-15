from django.db import models
from django.core.exceptions import ValidationError


class Empresa(models.Model):
    idempresa = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    idproveedor = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.nombre


class Sede(models.Model):
    idsede = models.AutoField(primary_key=True)
    idempresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='sedes')
    nombre = models.CharField(max_length=50)
    ciudad = models.CharField(max_length=30, blank=True, null=True)
    pais = models.CharField(max_length=30, blank=True, null=True)

    # Mapa de Sedes (Punto A): Definimos la función de los proveedores en esta sede
    canal_primario = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name='sedes_primario',
        null=True, blank=True,
        verbose_name="Canal Primario"
    )
    canal_secundario = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name='sedes_secundario',
        null=True, blank=True,
        verbose_name="Canal Secundario"
    )

    class Meta:
        verbose_name = "Sede"
        verbose_name_plural = "Sedes"

    def __str__(self):
        return f"{self.nombre} ({self.idempresa.nombre})"


class TipoFalla(models.Model):
    # Punto B: Tabla gestionable para las causas de los eventos
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Tipo de Falla"
        verbose_name_plural = "Tipos de Fallas"

    def __str__(self):
        return self.nombre


class Evento(models.Model):
    idevento = models.AutoField(primary_key=True)
    idsede = models.ForeignKey(Sede, on_delete=models.CASCADE)
    idproveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    idtipo_falla = models.ForeignKey(TipoFalla, on_delete=models.SET_NULL, null=True, verbose_name="Causa de Falla")

    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True, blank=True)
    comentarios = models.TextField(blank=True, null=True)

    # Columnas físicas para cálculos rápidos (Dashboard)
    duracion_minutos = models.IntegerField(null=True, blank=True, editable=False)
    duracion_horas = models.FloatField(null=True, blank=True, editable=False)

    @property
    def periodo(self):
        if self.fecha_inicio:
            return self.fecha_inicio.strftime("%m/%Y")
        return None

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        indexes = [
            models.Index(fields=['idsede'], name='idx_eventos_sede'),
            models.Index(fields=['fecha_inicio'], name='idx_eventos_fecha'),
        ]

    def save(self, *args, **kwargs):
        # Cálculo automático de duración al guardar
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

    def __str__(self):
        return f"Falla {self.idsede.nombre} - {self.idproveedor.nombre} ({self.periodo})"


class ConfiguracionGlobal(models.Model):
    # Punto C: Parámetros del sistema
    meta_disponibilidad = models.FloatField(default=0.99, help_text="Ejemplo: 0.99 para 99%")
    minutos_dia = models.IntegerField(default=1440, help_text="Minutos en un día (24h = 1440)")

    class Meta:
        verbose_name = "Configuración Global"
        verbose_name_plural = "Configuración Global"

    def __str__(self):
        return "Configuración del Sistema"
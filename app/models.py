from django.db import models

class Empresa(models.Model):
    idempresa = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.nombre

class Sede(models.Model):
    idsede = models.AutoField(primary_key=True)
    idempresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='sedes')
    nombre = models.CharField(max_length=20)
    ciudad = models.CharField(max_length=15, blank=True, null=True)
    pais = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.idempresa.nombre})"

class Proveedor(models.Model):
    idproveedor = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.nombre

class Inventario(models.Model):
    TIPO_CHOICES = [
        ('Principal', 'Principal'),
        ('Respaldo', 'Respaldo'),
    ]

    idinventario = models.AutoField(primary_key=True)
    idempresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    idsede = models.ForeignKey(Sede, on_delete=models.CASCADE)
    idproveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)

    class Meta:
        # Esto replica el CONSTRAINT UQ_sede_proveedor
        unique_together = ('idsede', 'idproveedor')

class Evento(models.Model):
    idevento = models.AutoField(primary_key=True)
    idsede = models.ForeignKey(Sede, on_delete=models.CASCADE)
    idproveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True, blank=True)
    causa = models.CharField(max_length=50, blank=True, null=True)

    # Lógica para columnas calculadas
    @property
    def periodo(self):
        if self.fecha_inicio:
            return self.fecha_inicio.strftime("%m/%Y")
        return None

    @property
    def duracion_minutos(self):
        if self.fecha_inicio and self.fecha_fin:
            delta = self.fecha_fin - self.fecha_inicio
            return int(delta.total_seconds() / 60)
        return None

    @property
    def duracion_horas(self):
        minutos = self.duracion_minutos
        if minutos is not None:
            return round(minutos / 60.0, 2)
        return None

    class Meta:
        # Django crea índices automáticamente para ForeignKeys,
        # pero aquí los declaramos explícitamente como en tu SQL
        indexes = [
            models.Index(fields=['idsede'], name='idx_eventos_sede'),
            models.Index(fields=['idproveedor'], name='idx_eventos_proveedor'),
        ]

    def __str__(self):
        return f"Evento en {self.idsede.nombre} - {self.periodo}"
from django.db import models
from usuarios.models import Usuario


class RegistroAcceso(models.Model):
    TIPO_ACCESO = [
        ("INGRESO", "Ingreso"),
        ("EGRESO", "Egreso"),
    ]

    METODO_DETECCION = [
        ("MANUAL", "Detección manual"),
        ("QR", "Código QR"),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="accesos", db_index=True)
    tipo = models.CharField(max_length=10, choices=TIPO_ACCESO)
    fecha_hora_ingreso = models.DateTimeField(auto_now_add=True, db_index=True)
    metodo_ingreso = models.CharField(max_length=15, choices=METODO_DETECCION, default="MANUAL")
    fecha_hora_egreso = models.DateTimeField(null=True, blank=True)
    metodo_egreso = models.CharField(max_length=15, choices=METODO_DETECCION, null=True, blank=True)
    dispositivo_id = models.CharField(max_length=100, blank=True)
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = "Registro de acceso"
        verbose_name_plural = "Registros de acceso"
        ordering = ["-fecha_hora_ingreso"]
        indexes = [
            models.Index(fields=["usuario", "fecha_hora_ingreso"], name="idx_acceso_usuario_fecha"),
        ]

    def __str__(self):
        return f"{self.usuario} - {self.tipo} - {self.fecha_hora_ingreso}"


class ConfiguracionAforo(models.Model):
    aforo_maximo = models.IntegerField(default=2000)
    aforo_minimo = models.IntegerField(default=1800)
    mensaje_alerta = models.TextField(default="Se está alcanzando el aforo máximo del centro")
    activo = models.BooleanField(default=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de aforo"
        verbose_name_plural = "Configuraciones de aforo"

    def __str__(self):
        return f"Aforo Máximo: {self.aforo_maximo}"

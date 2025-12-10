from django.db import models
from usuarios.models import Usuario

class ConfiguracionReporte(models.Model):

    FRECUENCIA = [
        ('DIARIO', 'Diario'),
        ('SEMANAL', 'Semanal'),
        ('MENSUAL', 'Mensual'),
    ]

    TIPO_REPORTE = [
        ('AFORO', 'Reporte de Aforo'),
        ('ASISTENCIA', 'Reporte de Asistencia'),
        ('INCIDENTES', 'Reporte de Incidentes'),
        ('EQUIPAMIENTO', 'Estado de Equipamiento'),
        ('SEGURIDAD', 'Reporte de Seguridad'),
    ]

    nombre = models.CharField(max_length=200)
    tipo_reporte = models.CharField(max_length=50, choices=TIPO_REPORTE)
    frecuencia = models.CharField(max_length=10, choices=FRECUENCIA)
    hora_generacion = models.TimeField()
    destinatarios = models.ManyToManyField(Usuario, related_name='reportes_suscritos')
    activo = models.BooleanField(default=True)
    ultima_generacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Configuración de Reporte'
        verbose_name_plural = 'Configuraciones de Reportes'

    def __str__(self):
        return f'{self.nombre} - {self.get_frecuencia_display()}'
    
class ReporteGenerado(models.Model):
    configuracion = models.ForeignKey(
        ConfiguracionReporte,
        on_delete=models.CASCADE,
        related_name='reportes'
    )
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    periodo_inicio = models.DateField()
    periodo_fin = models.DateField()
    archivo_pdf = models.FileField(upload_to='reportes/pdf/', null=True, blank=True)
    archivo_excel = models.FileField(upload_to='reportes/excel/', null=True, blank=True)
    datos_json = models.JSONField(default=dict)
    generado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reportes_generados'
    )

    class Meta:
        verbose_name = 'Reporte generado'
        verbose_name_plural = 'Reportes generados'
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f'{self.configuracion.nombre} - {self.fecha_generacion}'
from django.db import models
from usuarios.models import Usuario
from django.utils import timezone

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


# MODELO SIMPLE PARA REPORTAR INCIDENTES/ACCIDENTES
class Incidente(models.Model):
    """
    Modelo SIMPLE para reportar incidentes de seguridad
    Cualquier persona puede reportar un problema
    """

    # Tipos de incidente (BÁSICO)
    TIPO_CHOICES = [
        ('ACCIDENTE', 'Accidente'),
        ('CASI_ACCIDENTE', 'Casi Accidente'),
        ('CONDICION_INSEGURA', 'Condición Insegura'),
        ('ACTO_INSEGURO', 'Acto Inseguro'),
        ('DAÑO_EQUIPO', 'Daño a Equipo'),
        ('OTRO', 'Otro'),
    ]

    # Gravedad (BÁSICO)
    GRAVEDAD_CHOICES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica'),
    ]

    # Estado (BÁSICO)
    ESTADO_CHOICES = [
        ('REPORTADO', 'Reportado'),
        ('EN_REVISION', 'En Revisión'),
        ('EN_PROCESO', 'En Proceso'),
        ('RESUELTO', 'Resuelto'),
        ('CERRADO', 'Cerrado'),
    ]

    # Datos básicos del incidente
    titulo = models.CharField(max_length=200, help_text='Título breve del incidente')
    descripcion = models.TextField(help_text='Describe qué pasó')
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='OTRO')
    gravedad = models.CharField(max_length=20, choices=GRAVEDAD_CHOICES, default='MEDIA')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='REPORTADO')

    # Ubicación
    ubicacion = models.CharField(max_length=200, blank=True, help_text='Dónde ocurrió')

    # Fechas
    fecha_incidente = models.DateTimeField(default=timezone.now, help_text='Cuándo ocurrió')
    fecha_reporte = models.DateTimeField(auto_now_add=True, help_text='Cuándo se reportó')
    fecha_resolucion = models.DateTimeField(null=True, blank=True)

    # Personas involucradas
    reportado_por = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='incidentes_reportados',
        help_text='Quién reportó el incidente'
    )

    asignado_a = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidentes_asignados',
        help_text='Quién está a cargo de resolverlo'
    )

    # Foto opcional (evidencia)
    foto = models.ImageField(upload_to='incidentes/fotos/', null=True, blank=True)

    # Acciones tomadas
    acciones_tomadas = models.TextField(blank=True, help_text='Qué se hizo para resolver')

    class Meta:
        verbose_name = 'Incidente'
        verbose_name_plural = 'Incidentes'
        ordering = ['-fecha_reporte']  # Más recientes primero

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.titulo}'
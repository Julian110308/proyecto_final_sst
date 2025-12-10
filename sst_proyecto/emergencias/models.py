from django.db import models
from usuarios.models import Usuario
from mapas.models import EdificioBloque

class TipoEmergencia(models.Model):

    # Catalogo de tipos de emergencias
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    color = models.CharField(max_length=7, default='#FF0000') # Color hex
    icono = models.CharField(max_length=50, default='warning')

    # Nivel de prioridad
    prioridad = models.IntegerField(
        default=3,
        choices=[
            (1, 'Crítica'),
            (2, 'Alta'),
            (3, 'Media'),
            (4, 'Baja'),
        ]
    )

    # Protocolo de respuesta
    protocolo = models.TextField(help_text='Pasos a seguir')
    tiempo_respuesta_minutos = models.IntegerField(default=5)

    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Tipo de emergencia'
        verbose_name_plural = 'Tipos de emergencias'
        ordering = ['prioridad', 'nombre']
    
    def __str__(self):
        return f'{self.nombre} (Prioridad {self.get_prioridad_display()})'
    
class Emergencia(models.Model):

    # Registro de emergencias reportadas
    ESTADO = [
        ('REPORTADA', 'Reportada'),
        ('EN_ATENCION', 'En atención'),
        ('CONTROLADA', 'Controlada'),
        ('RESUELTA', 'Resuelta'),
        ('FALSA_ALARMA', 'Falsa alarma'),
    ]

    # Datos basicos
    tipo = models.ForeignKey(
        TipoEmergencia,
        on_delete=models.PROTECT,
        related_name='emergencias'
    )
    reportada_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='emergencias_reportadas'
    )

    # Ubicación (usando campos FloatField en lugar de PointField)
    latitud = models.FloatField()
    longitud = models.FloatField()
    edificio = models.ForeignKey(
        EdificioBloque,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='emergencias'
    )
    descripcion_ubicacion = models.CharField(max_length=200, blank=True)

    # Detalles
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO, default='REPORTADA')

    # Fechas y tiempos
    fecha_hora_reporte = models.DateTimeField(auto_now_add=True)
    fecha_hora_atencion = models.DateTimeField(null=True, blank=True)
    fecha_hora_resolucion = models.DateTimeField(null=True, blank=True)

    # Respuesta
    atendida_por = models.ManyToManyField(
        Usuario,
        related_name='emergencias_atendidas',
        blank=True
    )
    acciones_tomadas = models.TextField(blank=True)

    # Multimedia
    foto = models.ImageField(upload_to='emergencias/', null=True, blank=True)

    # Impacto
    personas_afectadas = models.IntegerField(default=0)
    requiere_evacuacion = models.BooleanField(default=False)
    entidades_externas_notificadas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Emergencia'
        verbose_name_plural = 'Emergencias'
        ordering = ['-fecha_hora_reporte']
        indexes = [
            models.Index(fields=['-fecha_hora_reporte']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        return f'{self.tipo.nombre} - {self.fecha_hora_reporte}'
    
    @property
    def tiempo_respuesta(self):

        # Calcula el tiempo de respuesta en minutos
        if self.fecha_hora_atencion:
            from django.utils import timezone
            diff = self.fecha_hora_atencion - self.fecha_hora_reporte
            return diff.total_seconds() / 60
        return None
    
    @property
    def tiempo_resolucion(self):

        # Calcula el tiempo de resolución en minutos
        if self.fecha_hora_resolucion:
            from django.utils import timezone
            diff = self.fecha_hora_resolucion - self.fecha_hora_reporte
            return diff.total_seconds() / 60
        return None
    
    def esta_cerca_de_edificio(self, radio_metros=100):

        # Verifica si la emergencia está cerca de algún edificio
        if not self.latitud or not self.longitud:
            return False
        
        from mapas.services import calcular_distancia

        edificios_cercanos = EdificioBloque.objects.filter(activo=True)
        for edificio in edificios_cercanos:
            distancia = calcular_distancia(
                self.latitud, self.longitud,
                edificio.latitud, edificio.longitud
            )
            if distancia <= radio_metros:
                return True
        return False
    
class BrigadaEmergencia(models.Model):

    # Miembros de la brigada de emergencia
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='brigada'
    )

    # Especialisación
    especializacion = models.CharField(
        max_length=50,
        choices=[
            ('PRIMEROS_AUXILIOS', 'Primeros Auxilios'),
            ('INCENDIOS', 'Control de Incendios'),
            ('EVACUACION', 'Evacuación'),
            ('RESCATE', 'Rescate'),
            ('COMUNICACIONES', 'Comunicaciones'),
            ('GENERAL', 'General'),
        ]
    )

    nivel_certificacion = models.CharField(
        max_length=20,
        choices=[
            ('BASICO', 'Básico'),
            ('INTERMEDIO', 'Intermedio'),
            ('AVANZADO', 'Avanzado'),
        ],
        default='BASICO'
    )

    fecha_certificacion = models.DateField()
    fecha_vencimiento = models.DateField()

    activo = models.BooleanField(default=True)
    disponible = models.BooleanField(default=True)

    # Información de contacto
    telefono_emergencia = models.CharField(max_length=15)

    class Meta:
        verbose_name = 'Miembro de Brigada'
        verbose_name_plural = 'Miembros de Brigada'
        ordering = ['usuario__last_name']

    def __str__(self):
        return f'{self.usuario.get_full_name()} - {self.get_especializacion_display()}'
    
    @property
    def certificacion_vencida(self):

        # Verifica si la certificación está vencida
        from django.utils import timezone
        return self.fecha_vencimiento < timezone.now().date()

class NotificacionEmergencia(models.Model):

    # Log de notificaciones enviadas
    emergencias = models.ForeignKey(
        Emergencia,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )

    destinatario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='notificaciones_recibidas'
    )

    tipo_notificacion = models.CharField(
        max_length=20,
        choices=[
            ('APP', 'Notificación App'),
            ('SMS', 'SMS'),
            ('EMAIL', 'Email'),
            ('LLAMADA', 'Llamada'),
        ]
    )

    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)
    fecha_lectura = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Notificación de Emergencia'
        verbose_name_plural = 'Notificaciones de Emergencia'
        ordering = ['-fecha_envio']

    def __str__(self):
        return f'Notificacion a {self.destinatario} - {self.emergencia}'
    
class ContactoExterno(models.Model):

    # Contactos de entidades externas (Bomberos, Ambulancia, etc.)

    nombre = models.CharField(max_length=200)
    entidad = models.CharField(max_length=200)

    tipo = models.CharField(
        max_length=30,
        choices=[
            ('BOMBEROS', 'Bomberos'),
            ('AMBULANCIA', 'Ambulancia'),
            ('POLICIA', 'Policía'),
            ('DEFENSA_CIVIL', 'Defensa Civil'),
            ('HOSPITAL', 'Hospital'),
            ('OTRO', 'Otro'),
        ]
    )

    telefono_principal = models.CharField(max_length=15)
    telefono_alternativo = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)

    tiempo_llegada_estimado = models.IntegerField(
        help_text='Minutos estimados de llegada',
        null=True,
        blank=True
    )

    activo = models.BooleanField(default=True)
    orden_contacto = models.IntegerField(default=1)

    class Meta:
        verbose_name = 'Contacto Externo'
        verbose_name_plural = 'Contactos Externos'
        ordering = ['orden_contacto', 'tipo', 'nombre']

    def __str__(self):
        return f'{self.nombre} - {self.get_tipo_display()}'
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from usuarios.models import Usuario

class UbicacionBase(models.Model):

    # Modelo base para ubicaciones con latitud y longitud
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    latitud = models.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text='Latitud debe estar entre -90 y 90 grados'
    )
    longitud = models.FloatField(
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        help_text='Longitud debe estar entre -180 y 180 grados'
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

class EdificioBloque(UbicacionBase):

    # Representa los bloques/edificios del centro
    tipo = models.CharField(
        max_length=50,
        choices=[
            ('AULAS', 'Bloque de aulas'),
            ('TALLER', 'Taller'),
            ('LABORATORIO', 'Laboratorio'),
            ('ADMINISTRATIVO', 'Oficinas administrativas'),
            ('CAFETERIA', 'Cafeteria'),
            ('PARQUEADERO', 'Parqueadero'),
            ('CANCHA', 'Cancha deportiva'),
            ('ZONA_VERDE', 'Zona verde'),
            ('MINA', 'Mina didactica'),
            ('BIBLIOTECA', 'Biblioteca'),
            ('BODEGA', 'Almacen/Bodega'),
            ('OTRO', 'Otro'),
        ]
    )
    piso_minimo = models.IntegerField(default=1)
    piso_maximo = models.IntegerField(default=1)
    capacidad = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Edificio/Bloque'
        verbose_name_plural = 'Edificios/Bloques'
        ordering = ['nombre']

    # Campos para representacion SVG del campus
    svg_x = models.FloatField(null=True, blank=True, help_text='Coordenada X en SVG (calculada desde GPS)')
    svg_y = models.FloatField(null=True, blank=True, help_text='Coordenada Y en SVG (calculada desde GPS)')
    svg_ancho = models.FloatField(default=40, help_text='Ancho del edificio en SVG')
    svg_alto = models.FloatField(default=25, help_text='Alto del edificio en SVG')

    def __str__(self):
        return f'{self.nombre} - {self.get_tipo_display()}'


class PuntoEncuentro(UbicacionBase):

    # Puntos de encuentro para evacuación
    capacidad = models.IntegerField()
    tipo_terreno = models.CharField(
        max_length=50,
        choices=[
            ('ABIERTO', 'Espacio abierto'),
            ('TECHADO', 'Espacio techado'),
            ('PARQUE', 'Parque/Zona verde'),
        ],
        default='ABIERTO'
    )
    prioridad = models.IntegerField(
        default=1,
        help_text='1=Principal, 2=Secundario, 3=Terciario'
    )

    # Caracteristicas de seguridad
    tiene_agua = models.BooleanField(default=False)
    tiene_sombra = models.BooleanField(default=False)
    tiene_baños = models.BooleanField(default=False)

    foto = models.ImageField(upload_to='puntos_encuentro/', null=True, blank=True)

    class Meta:
        verbose_name = 'Punto de encuentro'
        verbose_name_plural = 'Puntos de encuentro'
        ordering = ['prioridad', 'nombre']
    
    def __str__(self):
        return f'{self.nombre} - (P{self.prioridad})'


class EquipamientoSeguridad(UbicacionBase):

    # Extintores, botiquines, alarmas, etc.
    TIPO_EQUIPAMIENTO = [
        ('EXTINTOR', 'Extintor'),
        ('BOTIQUIN', 'Botiquin'),
        ('ALARMA', 'Alarma de emergencia'),
        ('HIDRANTE', 'Hidrante'),
        ('SALIDA_EMERGENCIA', 'Señal de salida de emergencia'),
        ('CAMILLA', 'Camilla'),
        ('DEA', 'Desfibrilador (DEA)'),
        ('OTRO', 'Otro'),
    ]
    
    tipo = models.CharField(max_length=30, choices=TIPO_EQUIPAMIENTO)
    codigo = models.CharField(max_length=50, unique=True)

    edificio = models.ForeignKey(
        EdificioBloque,
        on_delete=models.CASCADE,
        related_name='equipamientos',
        null=True,
        blank=True
    )
    piso = models.IntegerField(default=1)

    # Estado y mantenimiento
    estado = models.CharField(
        max_length=20,
        choices=[
            ('OPERATIVO', 'Operativo'),
            ('MANTENIMIENTO', 'En mantenimiento'),
            ('FUERA_SERVICIO', 'Fuera de servicio'),
        ],
        default='OPERATIVO'
    )

    fecha_instalacion = models.DateTimeField(null=True, blank=True)
    ultima_revision = models.DateTimeField(null=True, blank=True)
    proxima_revision = models.DateTimeField(null=True, blank=True)

    responsable = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipamientos_responsables'
    )

    foto = models.ImageField(upload_to='equipamientos/', null=True, blank=True)

    class Meta:
        verbose_name = 'Equipamiento de seguridad'
        verbose_name_plural = 'Equipamientos de seguridad'
        ordering = ['tipo', 'codigo']
    
    def __str__(self):
        return f'{self.get_tipo_display()} - {self.codigo}'
    

class RutaEvacuacion(models.Model):

    # Rutas de evacuación
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()

    # Coordenadas de inicio
    inicio_latitud = models.FloatField()
    inicio_longitud = models.FloatField()

    punto_fin = models.ForeignKey(
        PuntoEncuentro,
        on_delete=models.CASCADE,
        related_name='rutas',
    )

    distancia_metros = models.FloatField(help_text='Distancia en metros')
    tiempo_estimado_minutos = models.FloatField(help_text='Tiempo estimado en minutos')

    waypoints = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de coordenadas intermedias: [[lat1,lng1],[lat2,lng2],...]'
    )

    bloques_atraviesa = models.ManyToManyField(
        EdificioBloque,
        related_name='rutas_evacuacion',
        blank=True
    )

    activa = models.BooleanField(default=True)
    prioridad = models.IntegerField(default=1)

    class Meta:
        verbose_name = 'Ruta de evacuación'
        verbose_name_plural = 'Rutas de evacuación'
        ordering = ['prioridad', 'nombre']
    
    def __str__(self):
        return f'{self.nombre} -> {self.punto_fin.nombre}'


class EstadoEdificio(models.Model):
    ESTADOS = [
        ('NORMAL', 'Normal'),
        ('DANADO', 'Danado'),
        ('EVACUANDO', 'Evacuando'),
        ('CERRADO', 'Cerrado'),
        ('EN_EMERGENCIA', 'En emergencia'),
    ]

    COLOR_MAP = {
        'NORMAL': '#4CAF50',
        'DANADO': '#F44336',
        'EVACUANDO': '#FF9800',
        'CERRADO': '#9E9E9E',
        'EN_EMERGENCIA': '#D32F2F',
    }

    edificio = models.OneToOneField(
        EdificioBloque,
        on_delete=models.CASCADE,
        related_name='estado_actual'
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='NORMAL')
    motivo = models.TextField(blank=True)
    actualizado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    @property
    def color(self):
        return self.COLOR_MAP.get(self.estado, '#4CAF50')

    class Meta:
        verbose_name = 'Estado de edificio'
        verbose_name_plural = 'Estados de edificios'

    def __str__(self):
        return f'{self.edificio.nombre} - {self.get_estado_display()}'


class HistorialEstadoEdificio(models.Model):
    edificio = models.ForeignKey(
        EdificioBloque,
        on_delete=models.CASCADE,
        related_name='historial_estados'
    )
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    motivo = models.TextField(blank=True)
    cambiado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historial de estado'
        verbose_name_plural = 'Historial de estados'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.edificio.nombre}: {self.estado_anterior} -> {self.estado_nuevo}'
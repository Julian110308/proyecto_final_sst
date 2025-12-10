from django.db import models
from usuarios.models import Usuario

class UbicacionBase(models.Model):

    # Modelo base para ubicaciones con latitud y longitud
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    latitud = models.FloatField()
    longitud = models.FloatField()
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
            ('Cafeteria', 'Cafeteria'),
            ('PARQUEADERO', 'Parqueadero'),
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
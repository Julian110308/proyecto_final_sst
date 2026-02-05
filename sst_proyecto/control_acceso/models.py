from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from usuarios.models import Usuario
from mapas.services import calcular_distancia

class Geocerca(models.Model):

    # Define el perímetro virtual del Centro Minero SIN campos geoespaciales
    nombre = models.CharField(max_length=100, default='Centro Minero SENA')
    descripcion = models.TextField(blank=True)

    # Coordenadas del centro y radio (en lugar de polígono)
    centro_latitud = models.FloatField(
        default=5.7303596,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text='Latitud debe estar entre -90 y 90 grados'
    )
    centro_longitud = models.FloatField(
        default=-72.8943613,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        help_text='Longitud debe estar entre -180 y 180 grados'
    )
    radio_metros = models.IntegerField(
        default=200,
        validators=[MinValueValidator(1)],
        help_text='Radio en metros (mínimo 1 metro)'
    )

    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Geocerca'
        verbose_name_plural = 'Geocercas'
    
    def __str__(self):
        return self.nombre
    
    def punto_esta_dentro(self, latitud, longitud):
        """
        Verifica si un punto está dentro de la geocerca usando la fórmula de Haversine
        Retorna True si está dentro del radio, False si está fuera
        """
        distancia = calcular_distancia(
            self.centro_latitud,
            self.centro_longitud,
            latitud,
            longitud
        )
        return distancia <= self.radio_metros
    
    @classmethod
    def verificar_ubicacion_usuario(cls, latitud, longitud):

        """
        Verifica si una ubicación está dentro de alguna geocerca activa
        Retorna la geocerca si está dentro, None si está fuera
        """

        geocercas_actives = cls.objects.filter(activo=True)

        for geocerca in geocercas_actives:
            if geocerca.punto_esta_dentro(latitud, longitud):
                return geocerca
            
        return None
    
class RegistroAcceso(models.Model):

    TIPO_ACCESO = [
        ('INGRESO', 'Ingreso'),
        ('EGRESO', 'Egreso'),
    ]

    METODO_DETECCION = [
        ('AUTOMATICO', 'Deteccion automática'),
        ('MANUAL', 'Detección manual'),
        ('QR', 'Código QR'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='accesos', db_index=True)
    tipo = models.CharField(max_length=10, choices=TIPO_ACCESO)
    fecha_hora_ingreso = models.DateTimeField(auto_now_add=True, db_index=True)
    latitud_ingreso = models.FloatField(null=True, blank=True)
    longitud_ingreso = models.FloatField(null=True, blank=True)
    metodo_ingreso = models.CharField(max_length=15, choices=METODO_DETECCION, default='AUTOMATICO')
    fecha_hora_egreso = models.DateTimeField(null=True, blank=True)
    latitud_egreso = models.FloatField(null=True, blank=True)
    longitud_egreso = models.FloatField(null=True, blank=True)
    metodo_egreso = models.CharField(max_length=15, choices=METODO_DETECCION, null=True, blank=True)
    dispositivo_id = models.CharField(max_length=100, blank=True)
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Registro de acceso'
        verbose_name_plural = 'Registros de acceso'
        ordering = ['-fecha_hora_ingreso']

    def __str__(self):
        return f'{self.usuario} - {self.tipo} - {self.fecha_hora_ingreso}'
    
class ConfiguracionAforo(models.Model):
    aforo_maximo = models.IntegerField(default=2000)
    aforo_minimo = models.IntegerField(default=1800)
    mensaje_alerta = models.TextField(default='Se está alcanzando el aforo máximo del centro')
    activo = models.BooleanField(default=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración de aforo'
        verbose_name_plural = 'Configuraciones de aforo'

    def __str__(self):
        return f'Aforo Máximo: {self.aforo_maximo}'
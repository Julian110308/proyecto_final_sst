from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    
    # Modelo personalizado de usuario para el sistema SST
    
    ROLES = [
        ('APRENDIZ', 'Aprendiz'),
        ('INSTRUCTOR', 'Instructor'),
        ('ADMINISTRATIVO', 'Administrativo'),
        ('VIGILANCIA', 'Vigilancia'),
        ('BRIGADA', 'Brigada de Emergencia'),
        ('VISITANTE', 'Visitante'),
    ]
    
    TIPO_DOCUMENTO = [
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('TI', 'Tarjeta de Identidad'),
        ('PAS', 'Pasaporte'),
    ]
    
    # Campos adicionales
    rol = models.CharField(max_length=20, choices=ROLES, default='APRENDIZ')
    tipo_documento = models.CharField(max_length=3, choices=TIPO_DOCUMENTO, default='CC')
    numero_documento = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=15, blank=True)
    telefono_emergencia = models.CharField(max_length=15, blank=True)
    contacto_emergencia = models.CharField(max_length=100, blank=True)
    foto = models.ImageField(upload_to='usuarios/fotos/', null=True, blank=True)
    
    # Para aprendices
    ficha = models.CharField(max_length=20, blank=True, null=True)
    programa_formacion = models.CharField(max_length=200, blank=True, null=True)
    
    # Control
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f'{self.get_full_name()} - {self.get_rol_display()}'
    
    @property
    def esta_en_centro(self):
        
        # Verifica si el usuario está actualmente en el centro
        from control_acceso.models import RegistroAcceso
        ultimo_registro = RegistroAcceso.objects.filter(
            usuario=self
        ).order_by('-fecha_hora_ingreso').first()
        
        if ultimo_registro:
            return ultimo_registro.fecha_hora_egreso is None
        return False


class Visitante(models.Model):
    
    # Modelo para visitantes externos
    
    nombre_completo = models.CharField(max_length=200)
    tipo_documento = models.CharField(max_length=3, choices=Usuario.TIPO_DOCUMENTO)
    numero_documento = models.CharField(max_length=20)
    entidad = models.CharField(max_length=200, blank=True)
    telefono = models.CharField(max_length=15)
    
    # Visita
    persona_a_visitar = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE,
        related_name='visitantes'
    )
    motivo_visita = models.TextField()
    fecha_visita = models.DateField(auto_now_add=True)
    hora_ingreso = models.TimeField(auto_now_add=True)
    hora_salida = models.TimeField(null=True, blank=True)
    
    # Control
    registrado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='visitantes_registrados'
    )
    foto = models.ImageField(upload_to='visitantes/', null=True, blank=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Visitante'
        verbose_name_plural = 'Visitantes'
        ordering = ['-fecha_visita', '-hora_ingreso']
    
    def __str__(self):
        return f'{self.nombre_completo} - {self.fecha_visita}'
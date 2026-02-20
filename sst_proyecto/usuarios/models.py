# usuarios/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class RolePermissions:
    """
    Clase para gestión centralizada de permisos por rol - VERSIÓN CORREGIDA
    """
    PERMISSIONS_MAP = {
        'APRENDIZ': {
            'can_view_dashboard': True,
            'can_view_reports': True,
            'can_view_own_data': True,
            'can_view_capacity': True,
            'can_view_alerts': True,
            'can_report_emergency': True,
            'can_view_emergencies': False,
            'can_view_own_emergencies': True,
            'can_view_map': True,
            'can_view_evacuation_routes': True,
            'can_create_report': True,
            'can_view_own_reports': True,
            'can_report_incident': True,
            'can_view_own_access': True,
            'can_manage_users': False,
            'can_manage_visitors': False,
            'can_configure_system': False,
            'can_export_data': False,
        },

        'INSTRUCTOR': {
            'can_view_dashboard': True,
            'can_view_reports': True,
            'can_view_own_data': True,
            'can_view_apprentice_data': True,
            'can_view_capacity': True,
            'can_report_emergency': True,
            'can_view_emergencies': True,
            'can_view_all_emergencies': False,
            'can_view_map': True,
            'can_view_evacuation_routes': True,
            'can_view_full_map': True,
            'can_create_report': True,
            'can_view_own_reports': True,
            'can_view_apprentice_reports': True,
            'can_approve_reports': True,
            'can_export_data': True,
            'can_view_apprentices': True,
            'can_manage_apprentices': True,
            'can_register_attendance': True,
            'can_manage_visitors': False,
            'can_view_visitors_to_me': True,
            'can_report_incident': True,
            'can_view_area_incidents': True,
            'can_manage_users': False,
            'can_configure_system': False,
        },

        'ADMINISTRATIVO': {
            'can_view_dashboard': True,
            'can_view_all_reports': True,
            'can_view_all_data': True,
            'can_manage_all_users': True,
            'can_view_capacity': True,
            'can_report_emergency': True,
            'can_view_all_emergencies': True,
            'can_manage_emergencies': True,
            'can_activate_emergency_protocol': True,
            'can_view_map': True,
            'can_view_full_map': True,
            'can_edit_map': True,
            'can_view_evacuation_routes': True,
            'can_create_report': True,
            'can_approve_reports': True,
            'can_export_data': True,
            'can_manage_users': True,
            'can_manage_visitors': True,
            'can_create_users': True,
            'can_edit_users': True,
            'can_block_users': True,
            'can_configure_system': True,
            'can_view_all_access': True,
            'can_register_manual_access': True,
        },

        'VIGILANCIA': {
            'can_view_dashboard': True,
            'can_view_reports': True,
            'can_view_access_data': True,
            'can_view_capacity': True,
            'can_register_access': True,
            'can_view_all_access': True,
            'can_register_manual_access': True,
            'can_block_users': True,
            'can_manage_visitors': True,
            'can_register_visitors': True,
            'can_view_all_visitors': True,
            'can_report_emergency': True,
            'can_view_emergencies': True,
            'can_view_security_emergencies': True,
            'can_view_all_emergencies': False,
            'can_view_map': True,
            'can_view_security_map': True,
            'can_create_report': True,
            'can_view_security_reports': True,
            'can_export_data': True,
            'can_configure_system': False,
            'can_manage_users': False,
        },

        'BRIGADA': {
            'can_view_dashboard': True,
            'can_view_reports': True,
            'can_view_emergency_data': True,
            'can_view_capacity': True,
            'can_report_emergency': True,
            'can_view_all_emergencies': True,
            'can_update_emergencies': True,
            'can_attend_emergencies': True,
            'can_resolve_emergencies': True,
            'can_activate_emergency_protocol': True,
            'can_evacuate_zones': True,
            'can_view_map': True,
            'can_view_emergency_map': True,
            'can_view_evacuation_routes': True,
            'can_edit_evacuation_routes': True,
            'can_verify_equipment': True,
            'can_manage_own_availability': True,
            'can_view_brigade_members': True,
            'can_create_report': True,
            'can_view_emergency_reports': True,
            'can_export_data': True,
            'can_configure_system': False,
            'can_manage_users': False,
            'can_view_all_access': False,
        },

        'VISITANTE': {
            'can_view_dashboard': False,
            'can_view_welcome': True,
            'can_register_arrival': True,
            'can_view_own_visit': True,
            'can_view_map': True,
            'can_view_help': True,
            'can_report_emergency': True,
            'can_view_reports': False,
            'can_manage_users': False,
            'can_view_emergencies': False,
            'can_export_data': False,
        }
    }
    
    @classmethod
    def has_permission(cls, user, permission_name):
        """Verifica si un usuario tiene un permiso específico"""
        if not user.is_authenticated:
            return False
            
        user_role = user.rol
        role_permissions = cls.PERMISSIONS_MAP.get(user_role, {})
        
        return role_permissions.get(permission_name, False)
    
    @classmethod
    def get_user_permissions(cls, user):
        """Obtiene todos los permisos de un usuario"""
        if not user.is_authenticated:
            return {}
            
        user_role = user.rol
        return cls.PERMISSIONS_MAP.get(user_role, {}).copy()
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

    def save(self, *args, **kwargs):
        # Mantener sincronizados activo e is_active
        self.is_active = self.activo
        super().save(*args, **kwargs)

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
    
    # Métodos para el sistema de permisos
    def has_perm(self, perm, obj=None):
        """
        Mantiene compatibilidad con el sistema de permisos nativo de Django
        (necesario para admin, is_superuser, etc.) y agrega soporte para
        permisos personalizados del sistema SST.
        """
        if self.is_superuser:
            return True
        # Si el permiso es del sistema SST (no tiene formato 'app.perm')
        if '.' not in perm:
            return RolePermissions.has_permission(self, perm)
        # Para permisos estándar de Django, usar el comportamiento por defecto
        return super().has_perm(perm, obj)

    def has_permission(self, permission_name):
        """Método conveniente para verificar permisos específicos"""
        return RolePermissions.has_permission(self, permission_name)
    
    def get_permissions(self):
        """Obtiene todos los permisos del usuario"""
        return RolePermissions.get_user_permissions(self)
    
    @property
    def is_administrativo(self):
        """Verifica si el usuario es administrativo"""
        return self.rol == 'ADMINISTRATIVO'
    
    @property
    def is_instructor(self):
        """Verifica si el usuario es instructor"""
        return self.rol == 'INSTRUCTOR'
    
    @property
    def is_aprendiz(self):
        """Verifica si el usuario es aprendiz"""
        return self.rol == 'APRENDIZ'
    
    @property
    def is_vigilancia(self):
        """Verifica si el usuario es de vigilancia"""
        return self.rol == 'VIGILANCIA'
    
    @property
    def is_brigada(self):
        """Verifica si el usuario es de brigada"""
        return self.rol == 'BRIGADA'
    
    @property
    def is_visitante(self):
        """Verifica si el usuario es visitante"""
        return self.rol == 'VISITANTE'
    
    def puede_gestionar_usuarios(self):
        """Verifica si puede gestionar otros usuarios"""
        return self.has_permission('can_manage_users') or self.has_permission('can_manage_all_users')
    
    def puede_gestionar_visitantes(self):
        """Verifica si puede gestionar visitantes"""
        return self.has_permission('can_manage_visitors')
    
    def puede_exportar_datos(self):
        """Verifica si puede exportar datos"""
        return self.has_permission('can_export_data')
    
    def puede_ver_emergencias(self):
        """Verifica si puede ver emergencias"""
        return self.has_permission('can_view_emergencies') or self.has_permission('can_view_all_emergencies')
    
    def get_dashboard_template(self):
        """Devuelve el template del dashboard según el rol"""
        templates = {
            'APRENDIZ': 'dashboard/aprendiz.html',
            'INSTRUCTOR': 'dashboard/instructor.html',
            'ADMINISTRATIVO': 'dashboard/administrativo.html',
            'VIGILANCIA': 'dashboard/vigilancia.html',
            'BRIGADA': 'dashboard/brigada.html',
            'VISITANTE': 'dashboard/visitante.html',
        }
        return templates.get(self.rol, 'dashboard/base.html')


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
    
    @property
    def esta_en_centro(self):
        """Verifica si el visitante aún está en el centro"""
        return self.hora_salida is None
    
    @property
    def duracion_visita(self):
        """Calcula la duración de la visita si ya salió"""
        if self.hora_salida:
            from datetime import datetime, timedelta
            entrada = datetime.combine(self.fecha_visita, self.hora_ingreso)
            salida = datetime.combine(self.fecha_visita, self.hora_salida)
            # Si la hora de salida es menor que la de entrada, cruzó medianoche
            if salida < entrada:
                salida += timedelta(days=1)
            duracion = salida - entrada
            return duracion.total_seconds() / 3600  # Horas
        return None


class Notificacion(models.Model):
    """
    Sistema de notificaciones general para todos los usuarios
    """
    TIPO_NOTIFICACION = [
        ('EMERGENCIA', 'Emergencia'),
        ('INCIDENTE', 'Incidente'),
        ('SISTEMA', 'Sistema'),
        ('ASISTENCIA', 'Asistencia'),
        ('CAPACITACION', 'Capacitacion'),
        ('RECORDATORIO', 'Recordatorio'),
        ('INFO', 'Informativo'),
    ]

    PRIORIDAD = [
        ('ALTA', 'Alta'),
        ('MEDIA', 'Media'),
        ('BAJA', 'Baja'),
    ]

    # Destinatario
    destinatario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )

    # Contenido
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_NOTIFICACION, default='INFO')
    prioridad = models.CharField(max_length=10, choices=PRIORIDAD, default='MEDIA')

    # Estado
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)

    # Opcional: enlace relacionado
    url_relacionada = models.CharField(max_length=500, blank=True)

    # Opcional: fecha de vencimiento (para recordatorios)
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Notificacion'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['destinatario', '-fecha_creacion']),
            models.Index(fields=['destinatario', 'leida']),
        ]

    def __str__(self):
        return f'{self.titulo} - {self.destinatario.username}'

    def marcar_leida(self):
        """Marca la notificacion como leida"""
        from django.utils import timezone
        if not self.leida:
            self.leida = True
            self.fecha_lectura = timezone.now()
            self.save()

    @property
    def esta_vencida(self):
        """Verifica si la notificacion tiene fecha de vencimiento y esta vencida"""
        if self.fecha_vencimiento:
            from django.utils import timezone
            return self.fecha_vencimiento < timezone.now()
        return False

    @classmethod
    def crear_notificacion(cls, destinatario, titulo, mensaje, tipo='INFO', prioridad='MEDIA', url='', vencimiento=None):
        """Metodo helper para crear notificaciones facilmente"""
        return cls.objects.create(
            destinatario=destinatario,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo,
            prioridad=prioridad,
            url_relacionada=url,
            fecha_vencimiento=vencimiento
        )


class PushSubscripcion(models.Model):
    """
    Suscripciones Web Push para notificaciones nativas en dispositivos móviles.
    Cada dispositivo/navegador genera una suscripción única al aceptar notificaciones.
    """
    usuario = models.ForeignKey(
        'Usuario',
        on_delete=models.CASCADE,
        related_name='push_subscripciones'
    )
    endpoint = models.TextField(unique=True)
    p256dh = models.TextField()
    auth = models.TextField()
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Suscripcion Push'
        verbose_name_plural = 'Suscripciones Push'

    def __str__(self):
        return f'Push: {self.usuario.username} ({self.endpoint[:40]}...)'

    @classmethod
    def notificar_usuarios_por_rol(cls, rol, titulo, mensaje, tipo='INFO', prioridad='MEDIA'):
        """Crea notificaciones masivas para todos los usuarios de un rol"""
        usuarios = Usuario.objects.filter(rol=rol, activo=True)
        notificaciones = []
        for usuario in usuarios:
            notificaciones.append(cls(
                destinatario=usuario,
                titulo=titulo,
                mensaje=mensaje,
                tipo=tipo,
                prioridad=prioridad
            ))
        return cls.objects.bulk_create(notificaciones)
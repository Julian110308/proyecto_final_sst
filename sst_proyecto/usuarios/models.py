# usuarios/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class RolePermissions:
    """
    Clase para gestión centralizada de permisos por rol - VERSIÓN CORREGIDA
    """
    PERMISSIONS_MAP = {
        'APRENDIZ': {
            # Dashboard y datos personales
            'can_view_dashboard': True,
            'can_view_reports': True,
            'can_view_own_data': True,
            'can_view_capacity': True,
            'can_view_alerts': True,
            
            # Emergencias - CAMBIO: Solo reportar y ver las propias
            'can_report_emergency': True,
            'can_view_emergencies': False,  # ❌ NO ve todas las emergencias
            'can_view_own_emergencies': True,  # ✅ Solo las que reportó
            
            # Mapas - CAMBIO CRÍTICO: Ahora SÍ puede ver
            'can_view_map': True,  # ✅ CAMBIADO de False a True
            'can_view_evacuation_routes': True,  # ✅ NUEVO: Importante para seguridad
            
            # Reportes e incidentes
            'can_create_report': True,
            'can_view_own_reports': True,
            'can_report_incident': True,
            
            # Capacitaciones - NUEVO
            'can_view_own_trainings': True,  # ✅ Ver sus capacitaciones
            'can_view_sst_norms': True,  # ✅ Ver normas SST
            
            # Control de acceso
            'can_view_own_access': True,
            'can_use_qr_code': True,
            
            # Permisos denegados
            'can_view_income': False,
            'can_manage_users': False,
            'can_manage_visitors': False,
            'can_configure_system': False,
            'can_export_data': False,
        },
        
        'INSTRUCTOR': {
            # Dashboard y vistas
            'can_view_dashboard': True,
            'can_view_reports': True,
            'can_view_own_data': True,
            'can_view_apprentice_data': True,
            'can_view_capacity': True,
            
            # Emergencias
            'can_report_emergency': True,
            'can_view_emergencies': True,
            'can_view_all_emergencies': False,
            
            # Mapas
            'can_view_map': True,
            'can_view_evacuation_routes': True,
            'can_view_full_map': True,
            
            # Reportes
            'can_create_report': True,
            'can_view_own_reports': True,
            'can_view_apprentice_reports': True,
            'can_approve_reports': True,
            'can_export_data': True,
            
            # Aprendices
            'can_view_apprentices': True,
            'can_manage_apprentices': True,
            'can_register_attendance': True,
            
            # Visitantes - CAMBIO CRÍTICO
            'can_manage_visitors': False,  # ❌ CAMBIADO de True a False
            'can_view_visitors_to_me': True,  # ✅ Solo visitantes que vienen a verlo
            
            # Capacitaciones - NUEVO
            'can_view_own_trainings': True,
            'can_create_trainings': True,
            'can_manage_trainings': True,
            'can_view_sst_norms': True,
            
            # Incidentes
            'can_report_incident': True,
            'can_view_area_incidents': True,
            
            # Permisos denegados
            'can_view_income': False,
            'can_manage_users': False,
            'can_configure_system': False,
        },
        
        'ADMINISTRATIVO': {
            # Acceso total
            'can_view_dashboard': True,
            'can_view_all_reports': True,
            'can_view_all_data': True,
            'can_manage_all_users': True,
            'can_view_capacity': True,
            
            # Emergencias
            'can_report_emergency': True,
            'can_view_all_emergencies': True,
            'can_manage_emergencies': True,
            'can_activate_emergency_protocol': True,
            
            # Mapas
            'can_view_map': True,
            'can_view_full_map': True,
            'can_edit_map': True,
            'can_view_evacuation_routes': True,
            
            # Reportes
            'can_create_report': True,
            'can_approve_reports': True,
            'can_export_data': True,
            
            # Usuarios y visitantes
            'can_manage_users': True,
            'can_manage_visitors': True,
            'can_create_users': True,
            'can_edit_users': True,
            'can_block_users': True,
            
            # Capacitaciones - NUEVO
            'can_view_all_trainings': True,
            'can_create_trainings': True,
            'can_manage_trainings': True,
            'can_view_sst_norms': True,
            
            # Configuración y auditoría
            'can_view_income': True,
            'can_configure_system': True,
            'can_view_audit_logs': True,  # ✅ NUEVO
            
            # Control de acceso
            'can_view_all_access': True,
            'can_register_manual_access': True,
            
            # EPP - NUEVO
            'can_manage_epp_inventory': True,  # ✅ NUEVO
        },
        
        'VIGILANCIA': {
            # Dashboard
            'can_view_dashboard': True,
            'can_view_reports': True,
            'can_view_access_data': True,
            'can_view_capacity': True,
            
            # Control de acceso
            'can_register_access': True,
            'can_view_all_access': True,
            'can_register_manual_access': True,
            'can_block_users': True,
            
            # Visitantes
            'can_manage_visitors': True,
            'can_register_visitors': True,
            'can_view_all_visitors': True,
            
            # Emergencias - CAMBIO: Solo de seguridad
            'can_report_emergency': True,
            'can_view_security_emergencies': True,  # ✅ Solo seguridad
            'can_view_all_emergencies': False,  # ❌ NO todas
            
            # Mapas
            'can_view_map': True,
            'can_view_security_map': True,
            'can_view_camera_locations': True,
            
            # Cámaras
            'can_view_cameras': True,
            'can_manage_cameras': True,
            
            # Rondas de seguridad - NUEVO
            'can_register_security_rounds': True,  # ✅ NUEVO
            'can_view_security_rounds': True,  # ✅ NUEVO
            'can_manage_lost_items': True,  # ✅ NUEVO
            
            # Reportes
            'can_create_report': True,
            'can_view_security_reports': True,
            'can_export_data': True,
            
            # Capacitaciones
            'can_view_own_trainings': True,
            'can_view_sst_norms': True,
            
            # Permisos denegados
            'can_view_income': False,
            'can_configure_system': False,
            'can_manage_users': False,
        },
        
        'BRIGADA': {
            # Dashboard
            'can_view_dashboard': True,
            'can_view_reports': True,
            'can_view_emergency_data': True,
            'can_view_capacity': True,
            
            # Emergencias
            'can_report_emergency': True,
            'can_view_all_emergencies': True,
            'can_update_emergencies': True,
            'can_attend_emergencies': True,
            'can_resolve_emergencies': True,
            'can_activate_emergency_protocol': True,
            'can_evacuate_zones': True,
            
            # Mapas
            'can_view_map': True,
            'can_view_emergency_map': True,
            'can_view_evacuation_routes': True,
            'can_edit_evacuation_routes': True,
            
            # Capacitaciones
            'can_view_own_trainings': True,
            'can_create_trainings': True,
            'can_view_sst_norms': True,
            
            # Simulacros - NUEVO
            'can_create_drills': True,  # ✅ NUEVO
            'can_manage_drills': True,  # ✅ NUEVO
            'can_evaluate_drills': True,  # ✅ NUEVO
            
            # EPP y equipos - NUEVO
            'can_view_epp_inventory': True,  # ✅ NUEVO
            'can_manage_epp_inventory': True,  # ✅ NUEVO
            'can_verify_equipment': True,  # ✅ NUEVO
            
            # Primeros auxilios - NUEVO
            'can_register_first_aid': True,  # ✅ NUEVO
            'can_view_medical_data': True,
            
            # Disponibilidad
            'can_manage_own_availability': True,
            'can_view_brigade_members': True,
            
            # Reportes
            'can_create_report': True,
            'can_view_emergency_reports': True,
            'can_export_data': True,
            
            # Permisos denegados
            'can_view_income': False,
            'can_configure_system': False,
            'can_manage_users': False,
            'can_view_all_access': False,  # ❌ NO necesita control de acceso
        },
        
        'VISITANTE': {
            # Dashboard limitado
            'can_view_dashboard': False,
            'can_view_welcome': True,
            
            # Solo su visita
            'can_register_arrival': True,
            'can_view_own_visit': True,
            
            # Información básica
            'can_view_map': True,  # ✅ Mapa básico
            'can_view_sst_norms': True,  # ✅ Normas
            'can_view_help': True,
            
            # Emergencia
            'can_report_emergency': True,
            
            # Permisos denegados
            'can_view_reports': False,
            'can_view_income': False,
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
        """Sobreescribe el método has_perm para usar nuestro sistema de permisos"""
        return RolePermissions.has_permission(self, perm)
    
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
    
    def puede_ver_ingresos(self):
        """Verifica si puede ver datos financieros"""
        return self.has_permission('can_view_income')
    
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
            from datetime import datetime, date
            # Combinar fecha y hora
            entrada = datetime.combine(self.fecha_visita, self.hora_ingreso)
            salida = datetime.combine(self.fecha_visita, self.hora_salida)
            duracion = salida - entrada
            return duracion.total_seconds() / 3600  # Horas
        return None
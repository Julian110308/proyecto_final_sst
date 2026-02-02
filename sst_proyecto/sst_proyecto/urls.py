"""
URL configuration for sst_proyecto project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from usuarios.permissions import rol_requerido, excluir_visitantes
from usuarios.login_view import custom_login_view

# Vista principal de dashboard que redirige según el rol
@login_required
def dashboard_view(request):
    """
    Vista principal que redirige al dashboard específico según el rol del usuario
    CON DATOS REALES DE LA BASE DE DATOS
    """
    from usuarios.models import Usuario, Visitante
    from control_acceso.models import RegistroAcceso, ConfiguracionAforo
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import timedelta

    usuario = request.user

    # Mapeo de roles a templates
    dashboard_templates = {
        'APRENDIZ': 'dashboard/aprendiz.html',
        'INSTRUCTOR': 'dashboard/instructor.html',
        'ADMINISTRATIVO': 'dashboard/administrativo.html',
        'VIGILANCIA': 'dashboard/vigilancia.html',
        'BRIGADA': 'dashboard/brigada.html',
        'VISITANTE': 'dashboard/visitante.html',
    }

    # Obtener el template según el rol
    template = dashboard_templates.get(usuario.rol, 'dashboard.html')

    # CALCULAR DATOS REALES
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)

    # Total de usuarios registrados
    total_usuarios = Usuario.objects.filter(activo=True).count()

    # Usuarios nuevos este mes
    usuarios_mes = Usuario.objects.filter(
        fecha_registro__gte=inicio_mes,
        activo=True
    ).count()

    # Personas actualmente en el centro (tienen ingreso pero no egreso)
    personas_en_centro = RegistroAcceso.objects.filter(
        tipo='INGRESO',
        fecha_hora_egreso__isnull=True,
        fecha_hora_ingreso__date=hoy
    ).count()

    # Ingresos totales hoy
    ingresos_hoy = RegistroAcceso.objects.filter(
        tipo='INGRESO',
        fecha_hora_ingreso__date=hoy
    ).count()

    # Visitantes hoy
    visitantes_hoy = Visitante.objects.filter(
        fecha_visita=hoy
    ).count()

    # Configuración de aforo
    try:
        config_aforo = ConfiguracionAforo.objects.filter(activo=True).first()
        aforo_maximo = config_aforo.aforo_maximo if config_aforo else 2000
    except:
        aforo_maximo = 2000

    # Porcentaje de ocupación
    porcentaje_ocupacion = round((personas_en_centro / aforo_maximo) * 100, 1) if aforo_maximo > 0 else 0

    # Últimos 7 días de registros (para gráficas)
    ultimos_7_dias = []
    for i in range(6, -1, -1):
        fecha = hoy - timedelta(days=i)
        cantidad = RegistroAcceso.objects.filter(
            tipo='INGRESO',
            fecha_hora_ingreso__date=fecha
        ).count()
        ultimos_7_dias.append({
            'fecha': fecha.strftime('%d/%m'),
            'cantidad': cantidad
        })

    # Últimos 5 accesos
    ultimos_accesos = RegistroAcceso.objects.select_related('usuario').filter(
        tipo='INGRESO'
    ).order_by('-fecha_hora_ingreso')[:5]

    # Contexto con datos reales
    context = {
        'usuario': usuario,
        'rol': usuario.rol,
        'permisos': usuario.get_permissions(),
        # Métricas principales
        'total_usuarios': total_usuarios,
        'usuarios_mes': usuarios_mes,
        'personas_en_centro': personas_en_centro,
        'ingresos_hoy': ingresos_hoy,
        'visitantes_hoy': visitantes_hoy,
        'aforo_maximo': aforo_maximo,
        'porcentaje_ocupacion': porcentaje_ocupacion,
        # Datos para gráficas
        'ultimos_7_dias': ultimos_7_dias,
        'ultimos_accesos': ultimos_accesos,
    }

    return render(request, template, context)

# ==============================================
# VISTAS ESPECÍFICAS PARA APRENDIZ
# ==============================================

@login_required
@rol_requerido('APRENDIZ')
def mi_horario_view(request):
    """
    Vista del horario del aprendiz
    """
    return render(request, 'dashboard/aprendiz/mi_horario.html')

@login_required
@rol_requerido('APRENDIZ')
def mi_asistencia_view(request):
    """
    Vista de asistencia del aprendiz
    """
    # Aquí puedes agregar lógica para obtener datos reales de asistencia
    from control_acceso.models import RegistroAcceso
    from django.utils import timezone
    from datetime import timedelta
    
    usuario = request.user
    hoy = timezone.now().date()
    
    # Obtener registros de este mes
    inicio_mes = hoy.replace(day=1)
    registros_mes = RegistroAcceso.objects.filter(
        usuario=usuario,
        tipo='INGRESO',
        fecha_hora_ingreso__gte=inicio_mes
    ).order_by('-fecha_hora_ingreso')
    
    context = {
        'usuario': usuario,
        'registros_mes': registros_mes,
        'dias_asistidos': registros_mes.count(),
        'total_dias_mes': hoy.day,
    }
    
    return render(request, 'dashboard/aprendiz/mi_asistencia.html', context)

@login_required
@rol_requerido('APRENDIZ')
def informacion_sst_view(request):
    """
    Vista de información SST para el aprendiz
    """
    return render(request, 'dashboard/aprendiz/informacion_sst.html')

@login_required
@rol_requerido('APRENDIZ')
def mis_alertas_view(request):
    """
    Vista de alertas del aprendiz
    """
    return render(request, 'dashboard/aprendiz/mis_alertas.html')

@login_required
@rol_requerido('APRENDIZ')
def mis_reportes_view(request):
    """
    Vista de reportes del aprendiz
    """
    return render(request, '/aprendiz/mis_reportes.html')

# ==============================================
# FIN VISTAS PARA APRENDIZ
# ==============================================

# ==============================================
# VISTAS ESPECÍFICAS PARA INSTRUCTOR
# ==============================================

@login_required
@rol_requerido('INSTRUCTOR')
def mis_aprendices_view(request):
    """
    Vista para que el instructor vea el listado de aprendices
    """
    from usuarios.models import Usuario
    # Obtenemos todos los aprendices activos, ordenados por ficha y apellido
    aprendices = Usuario.objects.filter(rol='APRENDIZ', activo=True).order_by('ficha', 'last_name')
    
    context = {
        'aprendices': aprendices,
        'total_aprendices': aprendices.count()
    }
    return render(request, 'dashboard/instructor/mis_aprendices.html', context)

@login_required
@rol_requerido('INSTRUCTOR')
def registrar_asistencia_view(request):
    """
    Vista específica para que el instructor registre asistencia
    """
    from usuarios.models import Usuario
    # Obtener fichas únicas para filtrar
    fichas = Usuario.objects.filter(rol='APRENDIZ', activo=True).values_list('ficha', flat=True).distinct().order_by('ficha')
    
    context = {
        'fichas': fichas
    }
    return render(request, 'dashboard/instructor/registrar_asistencia.html', context)

# ==============================================
# VISTAS ESPECÍFICAS PARA ADMINISTRATIVO
# ==============================================

@login_required
@rol_requerido('ADMINISTRATIVO')
def gestion_usuarios_view(request):
    """
    Vista para gestión de usuarios (Administrativo)
    """
    from usuarios.models import Usuario
    # Excluir superusuarios para seguridad básica en la vista
    usuarios = Usuario.objects.all().exclude(is_superuser=True).order_by('-fecha_registro')
    
    context = {
        'usuarios': usuarios,
        'total_usuarios': usuarios.count()
    }
    return render(request, 'dashboard/administrativo/gestion_usuarios.html', context)

@login_required
@rol_requerido('ADMINISTRATIVO')
def configuracion_view(request):
    """
    Vista de configuración del sistema
    """
    from control_acceso.models import ConfiguracionAforo
    config_aforo = ConfiguracionAforo.objects.filter(activo=True).first()
    
    context = {
        'config_aforo': config_aforo
    }
    return render(request, 'dashboard/administrativo/configuracion.html', context)

# ==============================================
# VISTAS ESPECÍFICAS PARA VIGILANCIA
# ==============================================

@login_required
@rol_requerido('VIGILANCIA')
def gestion_visitantes_view(request):
    """
    Vista para gestión de visitantes (Vigilancia)
    """
    from usuarios.models import Visitante
    from django.utils import timezone
    
    hoy = timezone.now().date()
    # Visitantes registrados hoy
    visitantes_hoy = Visitante.objects.filter(fecha_visita=hoy).order_by('-hora_ingreso')
    
    context = {
        'visitantes': visitantes_hoy,
        'total_hoy': visitantes_hoy.count(),
        'activos_ahora': visitantes_hoy.filter(hora_salida__isnull=True).count()
    }
    return render(request, 'dashboard/vigilancia/gestion_visitantes.html', context)

@login_required
@rol_requerido('BRIGADA')
def equipos_brigada_view(request):
    """
    Vista para gestión de equipos de emergencia (Brigada)
    """
    # Placeholder data
    context = {
        'equipos': [
            {'id': 1, 'nombre': 'Extintor ABC (PQS)', 'ubicacion': 'Pasillo A-1', 'estado': 'ÓPTIMO', 'ultima_revision': '2026-01-15'},
            {'id': 2, 'nombre': 'Botiquín de Primeros Auxilios', 'ubicacion': 'Taller de Soldadura', 'estado': 'REQUIERE REVISIÓN', 'ultima_revision': '2025-12-10'},
            {'id': 3, 'nombre': 'Camilla de Emergencia', 'ubicacion': 'Punto de Encuentro 2', 'estado': 'ÓPTIMO', 'ultima_revision': '2026-01-20'},
            {'id': 4, 'nombre': 'Gabinete Contra Incendios', 'ubicacion': 'Bloque B', 'estado': 'FUERA DE SERVICIO', 'ultima_revision': '2025-11-01'},
        ]
    }
    return render(request, 'dashboard/brigada/equipos.html', context)

@login_required
@rol_requerido('BRIGADA')
def mi_brigada_view(request):
    """
    Vista para ver los miembros de la brigada
    """
    from usuarios.models import Usuario
    miembros = Usuario.objects.filter(rol='BRIGADA', activo=True).exclude(id=request.user.id)
    context = {
        'miembros': miembros,
        'total_miembros': miembros.count() + 1 # Contando al usuario actual
    }
    return render(request, 'dashboard/brigada/mi_brigada.html', context)

@login_required
@rol_requerido('BRIGADA')
def capacitaciones_brigada_view(request):
    """
    Vista para capacitaciones de la brigada
    """
    # Placeholder data
    context = {
        'capacitaciones_disponibles': [],
        'capacitaciones_completadas': []
    }
    return render(request, 'dashboard/brigada/capacitaciones.html', context)
# ==============================================

# Vistas para usuarios autenticados (usan base.html)
@rol_requerido('ADMINISTRATIVO', 'VIGILANCIA')
def control_acceso_view(request):
    """
    Vista de Control de Acceso
    PERMISOS: Solo ADMINISTRATIVO y VIGILANCIA
    """
    return render(request, 'control_acceso.html')

# Importar la vista completa de mapas
from mapas.views import mapa_interactivo

# Decorador aplicado directamente en la vista mapa_interactivo en mapas/views.py

@excluir_visitantes
def emergencias_view(request):
    """
    Vista de Emergencias
    PERMISOS: Todos excepto VISITANTE
    """
    return render(request, 'emergencias.html')

@excluir_visitantes
def reportes_view(request):
    """
    Vista de Reportes
    PERMISOS: Todos excepto VISITANTE
    """
    return render(request, 'reportes.html')

urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticación - Rutas principales (con debugging temporal)
    path('accounts/login/', custom_login_view, name='login'),

    path('accounts/logout/', auth_views.LogoutView.as_view(
        next_page='login'
    ), name='logout'),

    # Recuperar Clave
    path('accounts/password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/recuperar_clave.html',
            email_template_name='registration/email_recuperacion.html',
            subject_template_name='registration/asunto_email.txt',
        ),
        name='password_reset'
    ),

    path('accounts/password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/correo_enviado.html'
        ),
        name='password_reset_done'
    ),

    path('accounts/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/nueva_clave.html'
        ),
        name='password_reset_confirm'
    ),

    path('accounts/reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/clave_cambiada.html'
        ),
        name='password_reset_complete'
    ),

    # Vistas principales del sistema (HTML templates)
    path('', dashboard_view, name='dashboard'),
    path('dashboard/', RedirectView.as_view(url='/', permanent=False)),
    path('acceso/', control_acceso_view, name='control_acceso'),
    path('mapas/', mapa_interactivo, name='mapas'),
    path('emergencias/', emergencias_view, name='emergencias'),

    # ==============================================
    # URLs ESPECÍFICAS PARA APRENDIZ
    # ==============================================
    path('aprendiz/horario/', mi_horario_view, name='mi_horario'),
    path('aprendiz/asistencia/', mi_asistencia_view, name='mi_asistencia'),
    path('aprendiz/informacion-sst/', informacion_sst_view, name='informacion_sst'),
    path('aprendiz/alertas/', mis_alertas_view, name='mis_alertas'),
    path('aprendiz/mis-reportes/', mis_reportes_view, name='mis_reportes'),
    # ==============================================

    # URLs PARA INSTRUCTOR
    path('instructor/mis-aprendices/', mis_aprendices_view, name='mis_aprendices'),
    path('instructor/asistencia/', registrar_asistencia_view, name='registrar_asistencia'),

    # URLs PARA ADMINISTRATIVO
    path('administrativo/usuarios/', gestion_usuarios_view, name='gestion_usuarios'),
    path('administrativo/configuracion/', configuracion_view, name='configuracion_sistema'),

    # URLs PARA VIGILANCIA
    path('vigilancia/visitantes/', gestion_visitantes_view, name='gestion_visitantes'),

    # URLs PARA BRIGADA
    path('brigada/equipos/', equipos_brigada_view, name='equipos_brigada'),
    path('brigada/mi-brigada/', mi_brigada_view, name='mi_brigada'),
    path('brigada/capacitaciones/', capacitaciones_brigada_view, name='capacitaciones_brigada'),

    # Vista General de Reportes
    path('reportes/general/', reportes_view, name='reportes_general'),

    # APIs REST (para operaciones AJAX/fetch desde el frontend)
    path('api/auth/', include('usuarios.urls')),
    path('api/acceso/', include('control_acceso.urls')),
    path('api/mapas/', include('mapas.urls')),
    path('api/emergencias/', include('emergencias.urls')),

    # Módulo de reportes (incluye vistas HTML de incidentes y API)
    path('reportes/', include('reportes.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
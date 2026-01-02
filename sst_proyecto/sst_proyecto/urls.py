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

# Vistas para usuarios autenticados (usan base.html)
@rol_requerido('ADMINISTRATIVO', 'VIGILANCIA', 'INSTRUCTOR')
def control_acceso_view(request):
    """
    Vista de Control de Acceso
    PERMISOS: Solo ADMINISTRATIVO, VIGILANCIA e INSTRUCTOR
    """
    return render(request, 'control_acceso.html')

@excluir_visitantes
def mapas_view(request):
    """
    Vista de Mapas
    PERMISOS: Todos excepto VISITANTE
    """
    return render(request, 'mapas.html')

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
    path('mapas/', mapas_view, name='mapas'),
    path('emergencias/', emergencias_view, name='emergencias'),

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
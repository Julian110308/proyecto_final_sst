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

# Vista principal de dashboard que redirige según el rol
@login_required
def dashboard_view(request):
    """
    Vista principal que redirige al dashboard específico según el rol del usuario
    """
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
    
    # Contexto común para todos los dashboards
    context = {
        'usuario': usuario,
        'rol': usuario.rol,
        'permisos': usuario.get_permissions(),
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
    
    # Autenticación - Rutas principales
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='login.html',
        redirect_authenticated_user=True
    ), name='login'),
    
    path('accounts/logout/', auth_views.LogoutView.as_view(
        next_page='login'
    ), name='logout'),
    
    # Vistas principales del sistema (HTML templates)
    path('', dashboard_view, name='dashboard'),
    path('dashboard/', RedirectView.as_view(url='/', permanent=False)),
    path('acceso/', control_acceso_view, name='control_acceso'),
    path('mapas/', mapas_view, name='mapas'),
    path('emergencias/', emergencias_view, name='emergencias'),
    path('reportes/', reportes_view, name='reportes'),
    
    # APIs REST (para operaciones AJAX/fetch desde el frontend)
    path('api/auth/', include('usuarios.urls')),
    path('api/acceso/', include('control_acceso.urls')),
    path('api/mapas/', include('mapas.urls')),
    path('api/emergencias/', include('emergencias.urls')),
    path('api/reportes/', include('reportes.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
"""
URL configuration for sst_proyecto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

# Vistas para usuarios autenticados (usan base.html)
@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html')

@login_required
def control_acceso_view(request):
    return render(request, 'control_acceso.html')

@login_required
def mapas_view(request):
    return render(request, 'mapas.html')

@login_required
def emergencias_view(request):
    return render(request, 'emergencias.html')

@login_required
def reportes_view(request):
    return render(request, 'reportes.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Autenticación - Rutas principales
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='login.html',
        redirect_authenticated_user=True  # Si ya está autenticado, redirige al dashboard
    ), name='login'),
    
    path('accounts/logout/', auth_views.LogoutView.as_view(
        next_page='login'
    ), name='logout'),
    
    # Vistas principales del sistema (HTML templates)
    path('', dashboard_view, name='dashboard'),
    path('dashboard/', RedirectView.as_view(url='/', permanent=False)),  # Redirección por si acaso
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
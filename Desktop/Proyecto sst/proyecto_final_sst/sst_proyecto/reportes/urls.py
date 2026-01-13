from django.urls import path, include
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.routers import DefaultRouter
from .views import ReporteViewSet, dashboard_estadisticas
from .views_incidentes import (
    listar_incidentes,
    crear_incidente,
    detalle_incidente,
    actualizar_incidente
)

# Vista simple para /reportes/ (página principal de reportes)
@login_required
def reportes_index(request):
    """Vista principal del módulo de reportes"""
    return render(request, 'reportes/index.html')

router = DefaultRouter()
router.register('api', ReporteViewSet, basename='reportes')

urlpatterns = [
    # Vista principal de reportes
    path('', reportes_index, name='reportes'),

    # URLs de la API (existentes)
    path('dashboard/', dashboard_estadisticas, name='api-reportes-dashboard'),
    path('', include(router.urls)),

    # URLs NUEVAS para Incidentes (HTML)
    path('incidentes/', listar_incidentes, name='listar_incidentes'),
    path('incidentes/nuevo/', crear_incidente, name='crear_incidente'),
    path('incidentes/<int:pk>/', detalle_incidente, name='detalle_incidente'),
    path('incidentes/<int:pk>/actualizar/', actualizar_incidente, name='actualizar_incidente'),
]
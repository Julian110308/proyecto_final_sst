from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    EdificioBloqueViewSet, PuntoEncuentroViewSet,
    EquipamientoSeguridadViewSet, RutaEvacuacionViewSet,
    mapa_interactivo, campus_svg, plano_centro,
    estados_edificios, cambiar_estado_edificio,
)

router = DefaultRouter()
router.register('edificios', EdificioBloqueViewSet)
router.register('puntos-encuentro', PuntoEncuentroViewSet)
router.register('equipamientos', EquipamientoSeguridadViewSet)
router.register('rutas-evacuacion', RutaEvacuacionViewSet)

urlpatterns = [
    # Ruta principal para el mapa HTML
    path('', views.mapa_interactivo, name='mapa_interactivo'),
    # APIs de estados de edificios
    path('api/edificios/estados/', views.estados_edificios, name='estados_edificios'),
    path('api/edificios/<int:pk>/cambiar-estado/', views.cambiar_estado_edificio, name='cambiar_estado_edificio'),
    # Rutas de la API REST
    path('api/', include(router.urls)),
    # Endpoint adicional para punto mas cercano
    path('api/puntos-encuentro/<int:pk>/mas_cercano/', views.PuntoEncuentroViewSet.as_view({'get': 'mas_cercano'})),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import EdificioBloqueViewSet, PuntoEncuentroViewSet, EquipamientoSeguridadViewSet, RutaEvacuacionViewSet, mapa_interactivo

router = DefaultRouter()
router.register('edificios', EdificioBloqueViewSet)
router.register('puntos-encuentro', PuntoEncuentroViewSet)
router.register('equipamientos', EquipamientoSeguridadViewSet)
router.register('rutas-evacuacion', RutaEvacuacionViewSet)

urlpatterns = [
    # Ruta principal para el mapa HTML
    path('', views.mapa_interactivo, name='mapa_interactivo'),
    # Rutas de la API REST
    path('', include(router.urls)),
    # Endpoint adicional para punto más cercano
    path('puntos-encuentro/<int:pk>/mas_cercano/', views.PuntoEncuentroViewSet.as_view({'get': 'mas_cercano'})),
]
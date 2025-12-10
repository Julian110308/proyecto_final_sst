from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EdificioBloqueViewSet, PuntoEncuentroViewSet, EquipamientoSeguridadViewSet, RutaEvacuacionViewSet

router = DefaultRouter()
router.register('edificios', EdificioBloqueViewSet)
router.register('puntos-encuentro', PuntoEncuentroViewSet)
router.register('equipamientos', EquipamientoSeguridadViewSet)
router.register('rutas-evacuacion', RutaEvacuacionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TipoEmergenciaViewSet,
    EmergenciaViewSet,
    BrigadaEmergenciaViewSet,
    NotificacionEmergenciaViewSet,
    ContactoExternoViewSet,
)

router = DefaultRouter()
router.register('tipos', TipoEmergenciaViewSet)
router.register('emergencias', EmergenciaViewSet)
router.register('brigada', BrigadaEmergenciaViewSet)
router.register('notificaciones', NotificacionEmergenciaViewSet)
router.register('contactos', ContactoExternoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UsuarioViewSet, VisitanteViewSet, NotificacionViewSet, EstadisticasViewSet, PushSubscripcionViewSet

router = DefaultRouter()
router.register('usuarios', UsuarioViewSet)
router.register('visitantes', VisitanteViewSet)
router.register('notificaciones', NotificacionViewSet, basename='notificaciones')
router.register('estadisticas', EstadisticasViewSet, basename='estadisticas')
router.register('push', PushSubscripcionViewSet, basename='push')

urlpatterns = [
    path('', include(router.urls)),
]
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UsuarioViewSet, VisitanteViewSet

router = DefaultRouter()
router.register('usuarios', UsuarioViewSet)
router.register('visitantes', VisitanteViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegistroAccesoViewSet, ConfiguracionAforoViewSet, mi_qr_view

router = DefaultRouter()
router.register("registros", RegistroAccesoViewSet)
router.register("config-aforo", ConfiguracionAforoViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("mi-qr/", mi_qr_view, name="mi_qr"),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReporteViewSet,dashboard_estadisticas

router = DefaultRouter()
router.register('', ReporteViewSet, basename='reportes')    

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', dashboard_estadisticas, name='dashboard'),
]
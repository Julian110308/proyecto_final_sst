from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    EdificioBloqueViewSet,
    PuntoEncuentroViewSet,
    EquipamientoSeguridadViewSet,
)

router = DefaultRouter()
router.register("edificios", EdificioBloqueViewSet)
router.register("puntos-encuentro", PuntoEncuentroViewSet)
router.register("equipamientos", EquipamientoSeguridadViewSet)

urlpatterns = [
    # Vistas HTML
    path("", views.mapa_interactivo, name="mapa_interactivo"),
    path("editor/", views.editor_mapa, name="editor_mapa"),
    # APIs de estados de edificios
    path("api/edificios/estados/", views.estados_edificios, name="estados_edificios"),
    path("api/edificios/<int:pk>/cambiar-estado/", views.cambiar_estado_edificio, name="cambiar_estado_edificio"),
    path(
        "api/edificios/<int:edificio_id>/poligono/", views.guardar_poligono_edificio, name="guardar_poligono_edificio"
    ),
    # API de ruteo peatonal
    path("api/ruta/", views.calcular_ruta_evacuacion, name="calcular_ruta_evacuacion"),
    # API del grafo de caminos
    path("api/grafo/", views.grafo_caminos, name="grafo_caminos"),
    path("api/grafo/nodo/", views.guardar_nodo, name="guardar_nodo"),
    path("api/grafo/nodo/<int:nodo_id>/", views.eliminar_nodo, name="eliminar_nodo"),
    path("api/grafo/tramo/", views.guardar_tramo, name="guardar_tramo"),
    path("api/grafo/tramo/<int:tramo_id>/", views.eliminar_tramo, name="eliminar_tramo"),
    # Rutas de la API REST (ViewSets)
    path("api/", include(router.urls)),
    path("api/puntos-encuentro/<int:pk>/mas_cercano/", views.PuntoEncuentroViewSet.as_view({"get": "mas_cercano"})),
]

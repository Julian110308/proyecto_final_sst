from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import (
    EdificioBloque,
    PuntoEncuentro,
    EquipamientoSeguridad,
    RutaEvacuacion,
)
from .serializers import (
    EdificioBloqueSerializer,
    PuntoEncuentroSerializer,
    EquipamientoSeguridadSerializer,
    RutaEvacuacionSerializer,
)
from .services import encontrar_mas_cercano

class EdificioBloqueViewSet(viewsets.ModelViewSet):

    # ViewSet para edificios/bloques
    queryset = EdificioBloque.objects.filter(activo=True)
    serializer_class = EdificioBloqueSerializer
    permission_classes = [IsAuthenticated]

class PuntoEncuentroViewSet(viewsets.ModelViewSet):

    # ViewSet para puntos de encuentro
    queryset = PuntoEncuentro.objects.filter(activo=True)
    serializer_class = PuntoEncuentroSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def mas_cercano(self, request):

        # Encuentra el punto de encuentro más cercano
        latitud = request.query_params.get('lat')
        longitud = request.query_params.get('lon')

        if not latitud or not longitud:
            return Response({'error': 'Parámetros lat y lon son requeridos.'}, status=400)
        
        try:
            lat = float(latitud)
            lon = float(longitud)
        except ValueError:
            return Response({'error': 'Parámetros lat y lon deben ser números válidos.'}, status=400)
        
        punto_cercano, distancia = encontrar_mas_cercano(
            lat, lon, self.get_queryset()
        )

        if punto_cercano:
            serializer = self.get_serializer(punto_cercano)
            return Response({
                'punto': serializer.data,
                'distancia_metros': round(distancia, 2)
            })
        
        return Response({'mensaje': 'No hay puntos de encuentro cercanos.'})
    
class EquipamientoSeguridadViewSet(viewsets.ModelViewSet):

    # ViewSet para equipamientos de seguridad
    queryset = EquipamientoSeguridad.objects.all()
    serializer_class = EquipamientoSeguridadSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def cercanos(self, request):

        # Encuentra equipamientos cercanos a una ubicación
        latitud = request.query_params.get('lat')
        longitud = request.query_params.get('lon')
        radio_metros = float(request.query_params.get('radio', 500))

        if not latitud or not longitud:
            return Response({'error': 'Latitud y longitud son requeridos.'}, status=400)
        
        try:
            lat = float(latitud)
            lon = float(longitud)
        except ValueError:
            return Response({'error': 'Latitud y longitud deben ser números válidos.'}, status=400)
        
        equipos_cercanos = []
        for equipo in self.queryset.filter(estado='OPERATIVO'):
            from .services import calcular_distancia
            distancia = calcular_distancia(lat, lon, equipo.latitud, equipo.longitud)
            if distancia <= radio_metros:
                equipos_cercanos.append({
                    'equipo': EquipamientoSeguridadSerializer(equipo).data,
                    'distancia_metros': round(distancia, 2)
                })
        
        # Ordenar por distancia
        equipos_cercanos.sort(key=lambda x: x['distancia_metros'])

        return Response(equipos_cercanos)
    
class RutaEvacuacionViewSet(viewsets.ModelViewSet):

    # ViewSet para rutas de evacuación
    queryset = RutaEvacuacion.objects.filter(activa=True)
    serializer_class = RutaEvacuacionSerializer
    permission_classes = [IsAuthenticated]
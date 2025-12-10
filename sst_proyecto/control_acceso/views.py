from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Geocerca, RegistroAcceso, ConfiguracionAforo
from .serializers import GeocercaSerializer, RegistroAccesoSerializer, ConfiguracionAforoSerializer

class GeocercaViewSet(viewsets.ModelViewSet):
    queryset = Geocerca.objects.filter(activo=True)
    serializer_class = GeocercaSerializer
    permission_classes = [IsAuthenticated]

class RegistroAccesoViewSet(viewsets.ModelViewSet):
    queryset = RegistroAcceso.objects.all()
    serializer_class = RegistroAccesoSerializer
    permission_classes = [IsAuthenticated]

class ConfiguracionAforoViewSet(viewsets.ModelViewSet):
    queryset = ConfiguracionAforo.objects.all()
    serializer_class = ConfiguracionAforoSerializer
    permission_classes = [IsAuthenticated]
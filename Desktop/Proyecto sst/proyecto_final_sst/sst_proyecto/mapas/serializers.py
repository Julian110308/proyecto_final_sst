from rest_framework import serializers
from .models import (
    EdificioBloque,
    PuntoEncuentro,
    EquipamientoSeguridad,
    RutaEvacuacion,
)

class EdificioBloqueSerializer(serializers.ModelSerializer):

    # Serializer para edificios/bloques
    class Meta:
        model = EdificioBloque
        fields = '__all__'

class PuntoEncuentroSerializer(serializers.ModelSerializer):

    # Serializer para puntos de encuentro
    class Meta:
        model = PuntoEncuentro
        fields = '__all__'

class EquipamientoSeguridadSerializer(serializers.ModelSerializer):

    # Serializer para equipamientos de seguridad
    class Meta:
        model = EquipamientoSeguridad
        fields = '__all__'

class RutaEvacuacionSerializer(serializers.ModelSerializer):

    # Serializer para rutas de evacuación
    punto_fin_nombre = serializers.CharField(source='punto_fin.nombre', read_only=True)

    class Meta:
        model = RutaEvacuacion
        fields = '__all__'
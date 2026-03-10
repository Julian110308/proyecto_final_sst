from rest_framework import serializers
from .models import (
    EdificioBloque,
    PuntoEncuentro,
    EquipamientoSeguridad,
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


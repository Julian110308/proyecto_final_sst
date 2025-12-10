from rest_framework import serializers
from .models import Geocerca, RegistroAcceso, ConfiguracionAforo

class GeocercaSerializer(serializers.ModelSerializer):

    class Meta:
        model = Geocerca
        fields = '__all__'

class RegistroAccesoSerializer(serializers.ModelSerializer):

    class Meta:
        model = RegistroAcceso
        fields = '__all__'

class ConfiguracionAforoSerializer(serializers.ModelSerializer):

    class Meta:
        model = ConfiguracionAforo
        fields = '__all__'
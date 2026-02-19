from rest_framework import serializers
from .models import Geocerca, RegistroAcceso, ConfiguracionAforo
from usuarios.models import Usuario


class GeocercaSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Geocerca
    """
    class Meta:
        model = Geocerca
        fields = '__all__'


class UsuarioBasicoSerializer(serializers.ModelSerializer):
    """
    Serializer básico para mostrar información del usuario en registros
    """
    nombre_completo = serializers.CharField(source='get_full_name', read_only=True)
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'nombre_completo', 'numero_documento', 'rol', 'rol_display']


class RegistroAccesoSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo RegistroAcceso
    """
    usuario_info = UsuarioBasicoSerializer(source='usuario', read_only=True)
    metodo_ingreso_display = serializers.CharField(source='get_metodo_ingreso_display', read_only=True)
    metodo_egreso_display = serializers.CharField(source='get_metodo_egreso_display', read_only=True)
    estado = serializers.SerializerMethodField()
    tiempo_permanencia = serializers.SerializerMethodField()

    class Meta:
        model = RegistroAcceso
        fields = '__all__'

    def get_estado(self, obj):
        """Retorna el estado del registro"""
        return 'DENTRO' if not obj.fecha_hora_egreso else 'SALIO'

    def get_tiempo_permanencia(self, obj):
        """Calcula el tiempo de permanencia"""
        if obj.fecha_hora_egreso:
            duracion = obj.fecha_hora_egreso - obj.fecha_hora_ingreso
            return str(duracion)
        return None


class ConfiguracionAforoSerializer(serializers.ModelSerializer):
    """
    Serializer para la configuración de aforo
    """
    class Meta:
        model = ConfiguracionAforo
        fields = '__all__'


class RegistrarAccesoSerializer(serializers.Serializer):
    """
    Serializer para registrar ingresos y egresos manuales
    """
    usuario_id = serializers.IntegerField(required=True)
    latitud = serializers.FloatField(required=False, allow_null=True)
    longitud = serializers.FloatField(required=False, allow_null=True)
    metodo = serializers.ChoiceField(
        choices=['MANUAL', 'AUTOMATICO'],  # Removido 'QR' - solo registro físico
        default='MANUAL',
        required=False
    )

    def validate_usuario_id(self, value):
        """Valida que el usuario exista"""
        try:
            Usuario.objects.get(id=value)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError('Usuario no encontrado')
        return value

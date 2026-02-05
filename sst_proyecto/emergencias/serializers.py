from rest_framework import serializers
from .models import (
    TipoEmergencia,
    Emergencia,
    BrigadaEmergencia,
    NotificacionEmergencia,
    ContactoExterno,
)
from usuarios.serializers import UsuarioSerializer

class TipoEmergenciaSerializer(serializers.ModelSerializer):

    # Serializer para tipos de emergencia
    prioridad_display = serializers.CharField(
        source='get_prioridad_display',
        read_only=True
    )

    class Meta:
        model = TipoEmergencia
        fields = '__all__'

class EmergenciaSerializer(serializers.ModelSerializer):

    # Serializer para emergencias
    tipo_detalle = TipoEmergenciaSerializer(source='tipo', read_only=True)
    tipo_nombre = serializers.CharField(source='tipo.nombre', read_only=True)
    reportada_por_detalle = UsuarioSerializer(source='reportada_por', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tiempo_respuesta = serializers.ReadOnlyField()
    tiempo_resolucion = serializers.ReadOnlyField()

    class Meta:
        model = Emergencia
        fields = '__all__'

class EmergenciaCreateSerializer(serializers.ModelSerializer):

    # Serializer para crear emergencias (desde app móvil y botón de pánico)
    foto = serializers.ImageField(required=False, allow_null=True)
    personas_afectadas = serializers.IntegerField(required=False, default=0)
    requiere_evacuacion = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = Emergencia
        fields = [
            'tipo', 'descripcion', 'descripcion_ubicacion',
            'latitud', 'longitud', 'foto', 'personas_afectadas',
            'requiere_evacuacion'
        ]

class BrigadaEmergenciaSerializer(serializers.ModelSerializer):

    # Serializer para brigada de emergencia
    usuario_detalle = UsuarioSerializer(source='usuario', read_only=True)
    usuario_nombre = serializers.SerializerMethodField()
    especializacion_display = serializers.CharField(
        source='get_especializacion_display',
        read_only=True
    )
    nivel_certificacion_display = serializers.CharField(
        source='get_nivel_certificacion_display',
        read_only=True
    )
    certificacion_vencida = serializers.ReadOnlyField()

    class Meta:
        model = BrigadaEmergencia
        fields = '__all__'

    def get_usuario_nombre(self, obj):
        return obj.usuario.get_full_name() or obj.usuario.username

class NotificacionEmergenciaSerializer(serializers.ModelSerializer):

    # Serializer para notificaciones
    emergencia_resumen = serializers.SerializerMethodField()
    tipo_notificacion_display = serializers.CharField(
        source='get_tipo_notificacion_display',
        read_only=True
    )

    class Meta:
        model = NotificacionEmergencia
        fields = '__all__'

    def get_emergencia_resumen(self, obj):
        return {
            'id': obj.emergencia.id,
            'tipo': obj.emergencia.tipo.nombre,
            'estado': obj.emergencia.estado,
            'fecha_reporte': obj.emergencia.fecha_hora_reporte,
        }
    
class ContactoExternoSerializer(serializers.ModelSerializer):

    # Serializer para contactos externos
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model = ContactoExterno
        fields = '__all__'
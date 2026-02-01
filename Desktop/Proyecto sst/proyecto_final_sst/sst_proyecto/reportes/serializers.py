from rest_framework import serializers
from .models import ConfiguracionReporte, ReporteGenerado
from usuarios.serializers import UsuarioSerializer

class ConfiguracionReporteSerializer(serializers.ModelSerializer):

    # Serializer para configuraciones de reportes
    frecuencia_display = serializers.CharField(source='get_frecuencia_display', read_only=True)
    tipo_reporte_display = serializers.CharField(source='get_tipo_reporte_display', read_only=True)
    destinatarios_info = UsuarioSerializer(source='destinatarios', many=True, read_only=True)

    class Meta:
        model = ConfiguracionReporte
        fields = '__all__'

class ReporteGeneradoSerializer(serializers.ModelSerializer):

    # Serializer para reportes generados
    configuracion_nombre = serializers.CharField(source='configuracion.nombre', read_only=True)
    tipo_reporte = serializers.CharField(source='configuracion.tipo_reporte', read_only=True)
    generado_por_nombre = serializers.CharField(source='generado_por.get_full_name', read_only=True)

    class Meta:
        model = ReporteGenerado
        fields = '__all__'
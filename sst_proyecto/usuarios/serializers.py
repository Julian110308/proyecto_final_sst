from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Usuario, Visitante, Notificacion

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'password', 'first_name', 'last_name',
            'rol', 'tipo_documento', 'numero_documento', 'telefono',
            'telefono_emergencia', 'contacto_emergencia', 'foto',
            'ficha', 'programa_formacion', 'activo',
            'fecha_registro', 'ultima_actualizacion'
        ]
        read_only_fields = ['fecha_registro', 'ultima_actualizacion']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        usuario = Usuario(**validated_data)
        if password:
            usuario.set_password(password)
        usuario.save()
        return usuario
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            usuario = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            if not usuario:
                raise serializers.ValidationError('Credenciales incorrectas.')
            if not usuario.activo:
                raise serializers.ValidationError('Usuario inactivo.')
            
        else:
            raise serializers.ValidationError('Debe proporcionar username y password.')
        
        data['usuario'] = usuario
        return data

class VisitanteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Visitante
        fields = '__all__'
        read_only_fields = ['fecha_visita', 'hora_ingreso', 'registrado_por']


class NotificacionSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    tiempo_transcurrido = serializers.SerializerMethodField()

    class Meta:
        model = Notificacion
        fields = [
            'id', 'titulo', 'mensaje', 'tipo', 'tipo_display',
            'prioridad', 'prioridad_display', 'leida',
            'fecha_creacion', 'fecha_lectura', 'fecha_vencimiento',
            'url_relacionada', 'tiempo_transcurrido'
        ]
        read_only_fields = ['fecha_creacion', 'fecha_lectura']

    def get_tiempo_transcurrido(self, obj):
        from django.utils import timezone
        from django.utils.timesince import timesince
        return timesince(obj.fecha_creacion, timezone.now())
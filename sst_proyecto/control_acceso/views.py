from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta

from .models import Geocerca, RegistroAcceso, ConfiguracionAforo
from .serializers import (
    GeocercaSerializer,
    RegistroAccesoSerializer,
    ConfiguracionAforoSerializer,
    RegistrarAccesoSerializer,
    EscanearQRSerializer
)
from .utils import (
    generar_qr_usuario,
    generar_qr_visitante,
    decodificar_qr,
    verificar_aforo_actual,
    obtener_estadisticas_hoy
)
from usuarios.models import Usuario, Visitante
from usuarios.permissions import (
    EsVigilanciaOAdministrativo,
    EsAdministrativo,
    NoEsVisitante
)


class GeocercaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar geocercas del centro
    PERMISOS: Solo ADMINISTRATIVO puede crear/editar, otros solo ver
    """
    queryset = Geocerca.objects.filter(activo=True)
    serializer_class = GeocercaSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Permisos personalizados según la acción
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Solo ADMINISTRATIVO puede modificar geocercas
            return [EsAdministrativo()]
        # Todos los autenticados pueden ver
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'])
    def verificar_ubicacion(self, request, pk=None):
        """
        Verifica si una ubicación está dentro de la geocerca
        """
        geocerca = self.get_object()
        latitud = request.data.get('latitud')
        longitud = request.data.get('longitud')

        if not latitud or not longitud:
            return Response(
                {'error': 'Se requieren latitud y longitud'},
                status=status.HTTP_400_BAD_REQUEST
            )

        dentro = geocerca.punto_esta_dentro(float(latitud), float(longitud))

        return Response({
            'dentro': dentro,
            'geocerca': geocerca.nombre,
            'mensaje': 'Ubicación dentro del centro' if dentro else 'Ubicación fuera del centro'
        })


class RegistroAccesoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar registros de acceso
    PERMISOS: VIGILANCIA, ADMINISTRATIVO e INSTRUCTOR pueden registrar acceso
    """
    queryset = RegistroAcceso.objects.all()
    serializer_class = RegistroAccesoSerializer
    permission_classes = [EsVigilanciaOAdministrativo]

    def get_queryset(self):
        """
        Filtrar registros según parámetros de consulta
        """
        queryset = RegistroAcceso.objects.all()

        # Filtrar por fecha
        fecha = self.request.query_params.get('fecha', None)
        if fecha:
            queryset = queryset.filter(fecha_hora_ingreso__date=fecha)

        # Filtrar por usuario
        usuario_id = self.request.query_params.get('usuario', None)
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)

        # Filtrar por estado (dentro del centro)
        dentro = self.request.query_params.get('dentro', None)
        if dentro == 'true':
            queryset = queryset.filter(fecha_hora_egreso__isnull=True)
        elif dentro == 'false':
            queryset = queryset.filter(fecha_hora_egreso__isnull=False)

        return queryset.order_by('-fecha_hora_ingreso')

    @action(detail=False, methods=['post'])
    def registrar_ingreso(self, request):
        """
        Registra el ingreso de un usuario al centro
        """
        serializer = RegistrarAccesoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        usuario_id = serializer.validated_data.get('usuario_id')
        latitud = serializer.validated_data.get('latitud')
        longitud = serializer.validated_data.get('longitud')
        metodo = serializer.validated_data.get('metodo', 'MANUAL')

        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verificar que el usuario no esté ya dentro
        acceso_abierto = RegistroAcceso.objects.filter(
            usuario=usuario,
            fecha_hora_egreso__isnull=True
        ).first()

        if acceso_abierto:
            return Response(
                {'error': 'El usuario ya tiene un ingreso activo sin salida'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar geocerca si hay coordenadas
        if latitud and longitud:
            geocerca = Geocerca.verificar_ubicacion_usuario(latitud, longitud)
            if not geocerca and metodo == 'AUTOMATICO':
                return Response(
                    {'error': 'Ubicación fuera del centro'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Verificar aforo
        aforo_info = verificar_aforo_actual()
        if aforo_info['alerta'] == 'CRITICO':
            return Response(
                {
                    'error': 'Aforo máximo alcanzado',
                    'mensaje': aforo_info['mensaje'],
                    'aforo_actual': aforo_info['personas_dentro'],
                    'aforo_maximo': aforo_info['aforo_maximo']
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crear registro de ingreso
        registro = RegistroAcceso.objects.create(
            usuario=usuario,
            tipo='INGRESO',
            latitud_ingreso=latitud,
            longitud_ingreso=longitud,
            metodo_ingreso=metodo
        )

        return Response({
            'success': True,
            'mensaje': f'Ingreso registrado para {usuario.get_full_name()}',
            'registro_id': registro.id,
            'fecha_hora': registro.fecha_hora_ingreso,
            'aforo': aforo_info
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def registrar_egreso(self, request):
        """
        Registra la salida de un usuario del centro
        """
        serializer = RegistrarAccesoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        usuario_id = serializer.validated_data.get('usuario_id')
        latitud = serializer.validated_data.get('latitud')
        longitud = serializer.validated_data.get('longitud')
        metodo = serializer.validated_data.get('metodo', 'MANUAL')

        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Buscar el último ingreso sin egreso
        registro = RegistroAcceso.objects.filter(
            usuario=usuario,
            fecha_hora_egreso__isnull=True
        ).order_by('-fecha_hora_ingreso').first()

        if not registro:
            return Response(
                {'error': 'No hay un ingreso activo para este usuario'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Actualizar el registro con la salida
        registro.fecha_hora_egreso = timezone.now()
        registro.latitud_egreso = latitud
        registro.longitud_egreso = longitud
        registro.metodo_egreso = metodo
        registro.save()

        # Calcular tiempo de permanencia
        tiempo_permanencia = registro.fecha_hora_egreso - registro.fecha_hora_ingreso

        return Response({
            'success': True,
            'mensaje': f'Salida registrada para {usuario.get_full_name()}',
            'registro_id': registro.id,
            'fecha_hora_ingreso': registro.fecha_hora_ingreso,
            'fecha_hora_egreso': registro.fecha_hora_egreso,
            'tiempo_permanencia': str(tiempo_permanencia)
        })

    @action(detail=False, methods=['post'])
    def escanear_qr(self, request):
        """
        Procesa el escaneo de un código QR y registra ingreso/egreso automáticamente
        """
        serializer = EscanearQRSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        codigo_qr = serializer.validated_data.get('codigo_qr')
        latitud = serializer.validated_data.get('latitud')
        longitud = serializer.validated_data.get('longitud')

        # Decodificar el QR
        tipo, id_persona = decodificar_qr(codigo_qr)

        if not tipo or not id_persona:
            return Response(
                {'error': 'Código QR inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if tipo == 'USUARIO':
            try:
                usuario = Usuario.objects.get(id=id_persona)
            except Usuario.DoesNotExist:
                return Response(
                    {'error': 'Usuario no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Verificar si tiene un ingreso activo
            acceso_abierto = RegistroAcceso.objects.filter(
                usuario=usuario,
                fecha_hora_egreso__isnull=True
            ).first()

            # Si tiene ingreso activo, registrar salida; si no, registrar ingreso
            if acceso_abierto:
                # Registrar salida
                acceso_abierto.fecha_hora_egreso = timezone.now()
                acceso_abierto.latitud_egreso = latitud
                acceso_abierto.longitud_egreso = longitud
                acceso_abierto.metodo_egreso = 'QR'
                acceso_abierto.save()

                tiempo_permanencia = acceso_abierto.fecha_hora_egreso - acceso_abierto.fecha_hora_ingreso

                return Response({
                    'success': True,
                    'tipo': 'EGRESO',
                    'mensaje': f'Salida registrada - {usuario.get_full_name()}',
                    'usuario': {
                        'nombre': usuario.get_full_name(),
                        'documento': usuario.numero_documento,
                        'rol': usuario.get_rol_display()
                    },
                    'tiempo_permanencia': str(tiempo_permanencia)
                })
            else:
                # Verificar aforo
                aforo_info = verificar_aforo_actual()
                if aforo_info['alerta'] == 'CRITICO':
                    return Response({
                        'error': 'Aforo máximo alcanzado',
                        'mensaje': aforo_info['mensaje']
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Registrar ingreso
                registro = RegistroAcceso.objects.create(
                    usuario=usuario,
                    tipo='INGRESO',
                    latitud_ingreso=latitud,
                    longitud_ingreso=longitud,
                    metodo_ingreso='QR'
                )

                return Response({
                    'success': True,
                    'tipo': 'INGRESO',
                    'mensaje': f'Ingreso registrado - {usuario.get_full_name()}',
                    'usuario': {
                        'nombre': usuario.get_full_name(),
                        'documento': usuario.numero_documento,
                        'rol': usuario.get_rol_display()
                    },
                    'aforo': aforo_info
                }, status=status.HTTP_201_CREATED)

        else:
            return Response(
                {'error': 'Tipo de código QR no soportado'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtiene estadísticas de acceso
        """
        estadisticas = obtener_estadisticas_hoy()
        return Response(estadisticas)

    @action(detail=False, methods=['get'])
    def registros_recientes(self, request):
        """
        Obtiene los registros más recientes
        """
        limite = int(request.query_params.get('limite', 20))
        registros = RegistroAcceso.objects.all().order_by('-fecha_hora_ingreso')[:limite]

        data = []
        for registro in registros:
            data.append({
                'id': registro.id,
                'usuario': {
                    'id': registro.usuario.id,
                    'nombre': registro.usuario.get_full_name(),
                    'documento': registro.usuario.numero_documento,
                    'rol': registro.usuario.get_rol_display()
                },
                'fecha_hora_ingreso': registro.fecha_hora_ingreso,
                'fecha_hora_egreso': registro.fecha_hora_egreso,
                'metodo_ingreso': registro.get_metodo_ingreso_display(),
                'metodo_egreso': registro.get_metodo_egreso_display() if registro.metodo_egreso else None,
                'estado': 'DENTRO' if not registro.fecha_hora_egreso else 'SALIO'
            })

        return Response(data)


class ConfiguracionAforoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para configuración de aforo
    """
    queryset = ConfiguracionAforo.objects.all()
    serializer_class = ConfiguracionAforoSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def aforo_actual(self, request):
        """
        Obtiene el aforo actual del centro
        """
        aforo_info = verificar_aforo_actual()
        return Response(aforo_info)
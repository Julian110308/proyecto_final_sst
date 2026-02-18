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
)
from .utils import (
    verificar_aforo_actual,
    obtener_estadisticas_hoy
)
from usuarios.models import Usuario, Visitante
from usuarios.permissions import (
    EsVigilanciaOAdministrativo,
    EsAdministrativo,
    NoEsVisitante
)
# Servicio centralizado de notificaciones
from usuarios.services import NotificacionService


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

    def get_permissions(self):
        """
        Instructor puede acceder a acciones de asistencia y estadísticas/registros recientes.
        Las demás acciones requieren VIGILANCIA o ADMINISTRATIVO.
        """
        if self.action in [
            'registrar_asistencia_manual',
            'registrar_asistencia_masiva',
            'estadisticas',
            'registros_recientes',
            'auto_registro',
        ]:
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=['post'], url_path='auto-registro')
    def auto_registro(self, request):
        """
        Endpoint llamado periodicamente por el frontend con la ubicacion GPS.
        Detecta automaticamente si el usuario cruza la geocerca y registra
        ingreso/egreso segun corresponda.
        """
        latitud = request.data.get('latitud')
        longitud = request.data.get('longitud')

        if latitud is None or longitud is None:
            return Response({
                'error': 'Se requieren latitud y longitud'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            lat = float(latitud)
            lng = float(longitud)
        except (ValueError, TypeError):
            return Response({
                'error': 'Coordenadas invalidas'
            }, status=status.HTTP_400_BAD_REQUEST)

        usuario = request.user
        hoy = timezone.now().date()

        # Verificar si esta dentro de la geocerca
        geocerca = Geocerca.verificar_ubicacion_usuario(lat, lng)
        esta_dentro = geocerca is not None

        # Buscar registro abierto de hoy (ingreso sin egreso)
        registro_abierto = RegistroAcceso.objects.filter(
            usuario=usuario,
            tipo='INGRESO',
            fecha_hora_egreso__isnull=True,
            fecha_hora_ingreso__date=hoy
        ).order_by('-fecha_hora_ingreso').first()

        accion = None

        if esta_dentro and not registro_abierto:
            # Usuario entro al centro: registrar INGRESO
            # Verificar aforo
            aforo = verificar_aforo_actual()
            if aforo['alerta'] == 'CRITICO':
                return Response({
                    'estado': 'FUERA',
                    'accion': None,
                    'mensaje': 'Aforo maximo alcanzado, no se puede registrar ingreso'
                })

            RegistroAcceso.objects.create(
                usuario=usuario,
                tipo='INGRESO',
                latitud_ingreso=lat,
                longitud_ingreso=lng,
                metodo_ingreso='AUTOMATICO'
            )
            accion = 'INGRESO'

        elif not esta_dentro and registro_abierto:
            # Usuario salio del centro: registrar EGRESO
            registro_abierto.fecha_hora_egreso = timezone.now()
            registro_abierto.latitud_egreso = lat
            registro_abierto.longitud_egreso = lng
            registro_abierto.metodo_egreso = 'AUTOMATICO'
            registro_abierto.save()
            accion = 'EGRESO'

        return Response({
            'estado': 'DENTRO' if esta_dentro else 'FUERA',
            'accion': accion,
            'dentro_geocerca': esta_dentro,
            'registro_abierto': registro_abierto is not None if accion != 'EGRESO' else False,
        })

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

        # Notificar si el aforo está en nivel de alerta (>90%)
        if aforo_info['alerta'] in ['ALERTA', 'ALTO']:
            NotificacionService.notificar_aforo_critico(
                aforo_info['personas_dentro'],
                aforo_info['aforo_maximo'],
                porcentaje_alerta=90
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
        registros = RegistroAcceso.objects.select_related('usuario').all().order_by('-fecha_hora_ingreso')[:limite]

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

    @action(detail=False, methods=['get'])
    def personas_en_centro(self, request):
        """
        Retorna las personas actualmente dentro del centro con sus coordenadas.
        Usado para el monitoreo en tiempo real en el mapa.
        Accesible por VIGILANCIA y ADMINISTRATIVO.
        """
        hoy = timezone.now().date()
        registros_activos = RegistroAcceso.objects.filter(
            tipo='INGRESO',
            fecha_hora_egreso__isnull=True,
            fecha_hora_ingreso__date=hoy
        ).select_related('usuario')

        personas = []
        for registro in registros_activos:
            personas.append({
                'id': registro.usuario.id,
                'nombre': registro.usuario.get_full_name() or registro.usuario.username,
                'rol': registro.usuario.get_rol_display(),
                'rol_code': registro.usuario.rol,
                'latitud': registro.latitud_ingreso,
                'longitud': registro.longitud_ingreso,
                'hora_ingreso': registro.fecha_hora_ingreso.strftime('%H:%M'),
                'metodo': registro.get_metodo_ingreso_display(),
            })

        return Response({
            'total': len(personas),
            'personas': personas
        })

    @action(detail=False, methods=['post'], url_path='registrar_asistencia_manual')
    def registrar_asistencia_manual(self, request):
        """
        Registra la asistencia manual de un aprendiz (para instructores)
        PERMISOS: INSTRUCTOR, VIGILANCIA, ADMINISTRATIVO
        """
        # Verificar permisos
        if request.user.rol not in ['INSTRUCTOR', 'VIGILANCIA', 'ADMINISTRATIVO']:
            return Response({
                'success': False,
                'error': 'No tiene permisos para registrar asistencia'
            }, status=status.HTTP_403_FORBIDDEN)

        usuario_id = request.data.get('usuario_id')

        if not usuario_id:
            return Response({
                'success': False,
                'error': 'Se requiere el ID del usuario'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        # Verificar que no tenga ya un registro de hoy
        hoy = timezone.now().date()
        registro_existente = RegistroAcceso.objects.filter(
            usuario=usuario,
            fecha_hora_ingreso__date=hoy
        ).first()

        if registro_existente:
            return Response({
                'success': False,
                'error': 'El usuario ya tiene un registro de asistencia para hoy'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Crear registro de asistencia manual (ingreso sin coordenadas)
        # Usar coordenadas del centro por defecto
        geocerca = Geocerca.objects.filter(activo=True).first()
        lat_default = geocerca.centro_latitud if geocerca else 5.7303596
        lng_default = geocerca.centro_longitud if geocerca else -72.8943613

        registro = RegistroAcceso.objects.create(
            usuario=usuario,
            tipo='INGRESO',
            latitud_ingreso=lat_default,
            longitud_ingreso=lng_default,
            metodo_ingreso='MANUAL'
        )

        return Response({
            'success': True,
            'message': f'Asistencia registrada para {usuario.get_full_name()}',
            'registro_id': registro.id,
            'hora_registro': registro.fecha_hora_ingreso.strftime('%H:%M')
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='registrar_asistencia_masiva')
    def registrar_asistencia_masiva(self, request):
        """
        Registra la asistencia manual de multiples aprendices
        PERMISOS: INSTRUCTOR, VIGILANCIA, ADMINISTRATIVO
        """
        # Verificar permisos
        if request.user.rol not in ['INSTRUCTOR', 'VIGILANCIA', 'ADMINISTRATIVO']:
            return Response({
                'success': False,
                'error': 'No tiene permisos para registrar asistencia'
            }, status=status.HTTP_403_FORBIDDEN)

        usuarios_ids = request.data.get('usuarios_ids', [])

        if not usuarios_ids:
            return Response({
                'success': False,
                'error': 'Se requiere una lista de IDs de usuarios'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Obtener coordenadas por defecto
        geocerca = Geocerca.objects.filter(activo=True).first()
        lat_default = geocerca.centro_latitud if geocerca else 5.7303596
        lng_default = geocerca.centro_longitud if geocerca else -72.8943613

        hoy = timezone.now().date()
        errores = []

        # Obtener todos los usuarios de una sola query
        usuarios = Usuario.objects.filter(id__in=usuarios_ids)
        usuarios_dict = {u.id: u for u in usuarios}

        # IDs no encontrados
        ids_no_encontrados = set(usuarios_ids) - set(usuarios_dict.keys())
        for uid in ids_no_encontrados:
            errores.append(f'Usuario ID {uid} no encontrado')

        # Obtener IDs que ya tienen registro hoy (una sola query)
        ids_con_registro = set(
            RegistroAcceso.objects.filter(
                usuario_id__in=usuarios_dict.keys(),
                fecha_hora_ingreso__date=hoy
            ).values_list('usuario_id', flat=True)
        )

        for uid in ids_con_registro:
            errores.append(f'{usuarios_dict[uid].get_full_name()} ya tiene registro')

        # Crear registros en bulk para los que sí proceden
        registros_nuevos = []
        for uid, usuario in usuarios_dict.items():
            if uid not in ids_con_registro:
                registros_nuevos.append(RegistroAcceso(
                    usuario=usuario,
                    tipo='INGRESO',
                    latitud_ingreso=lat_default,
                    longitud_ingreso=lng_default,
                    metodo_ingreso='MANUAL'
                ))

        if registros_nuevos:
            RegistroAcceso.objects.bulk_create(registros_nuevos)

        registrados = len(registros_nuevos)

        return Response({
            'success': True,
            'message': f'Asistencia registrada para {registrados} aprendiz(es)',
            'registrados': registrados,
            'errores': errores if errores else None
        }, status=status.HTTP_201_CREATED)


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
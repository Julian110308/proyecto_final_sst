from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import (
    TipoEmergencia,
    Emergencia,
    BrigadaEmergencia,
    NotificacionEmergencia,
    ContactoExterno,
)
from .serializers import (
    TipoEmergenciaSerializer,
    EmergenciaSerializer,
    EmergenciaCreateSerializer,
    BrigadaEmergenciaSerializer,
    NotificacionEmergenciaSerializer,
    ContactoExternoSerializer,
)
# Servicio centralizado de notificaciones
from usuarios.services import NotificacionService

class TipoEmergenciaViewSet(viewsets.ModelViewSet):

    # ViewSet para tipos de emergencia (solo lectura)
    queryset = TipoEmergencia.objects.all()
    serializer_class = TipoEmergenciaSerializer
    permission_classes = [IsAuthenticated]

class EmergenciaViewSet(viewsets.ModelViewSet):

    # ViewSet para gestión de emergencias
    queryset = Emergencia.objects.all()
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Permisos específicos por acción:
        - list, retrieve, create, boton_panico: Todos los autenticados
        - atender, resolver: Solo Brigada y Administrativo
        - update, partial_update, destroy: Solo Administrativo
        """
        from usuarios.permissions import EsBrigadaOAdministrativo, EsAdministrativo

        if self.action in ['atender', 'resolver']:
            return [EsBrigadaOAdministrativo()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [EsAdministrativo()]

        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return EmergenciaCreateSerializer
        return EmergenciaSerializer
    
    def perform_create(self, serializer):
        emergencia = serializer.save(reportada_por=self.request.user)
        # Notificar via sistema centralizado a Brigada y Administrativos
        NotificacionService.notificar_emergencia_creada(emergencia)
        # También notificar vía NotificacionEmergencia (modelo específico)
        self.notificar_brigada(emergencia)

    @action(detail=False, methods=['post'])
    def boton_panico(self, request):

        # Endpoint para botón de pánico desde app móvil
        serializer = EmergenciaCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        emergencia = serializer.save(reportada_por=self.request.user)

        # Notificar via sistema centralizado a Brigada y Administrativos
        NotificacionService.notificar_emergencia_creada(emergencia)
        # También notificar vía NotificacionEmergencia (modelo específico de emergencias)
        self.notificar_brigada(emergencia)

        return Response({
            'emergencia': EmergenciaSerializer(emergencia).data,
            'mensaje': 'Emergencia reportada exitosamente. Ayuda en camino.'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def atender(self, request, pk=None):

        # Marcar emergencia como en atención
        emergencia = self.get_object()

        if emergencia.estado == 'REPORTADA':
            emergencia.estado = 'EN_ATENCION'
            emergencia.fecha_hora_atencion = timezone.now()
            emergencia.atendida_por.add(self.request.user)
            emergencia.save()

            # Notificar al usuario que reportó la emergencia
            NotificacionService.notificar_emergencia_atendida(emergencia, self.request.user)

            return Response({
                'mensaje': 'Emergencia marcada como en atención',
                'tiempo_respuesta_minutos': emergencia.tiempo_respuesta
            })

        return Response(
            {'error': 'La emergencia ya está siendo atendida o no está en estado reportada.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def resolver(self, request, pk=None):

        # Marcar emergencia como resuelta
        emergencia = self.get_object()

        acciones = request.data.get('acciones_tomadas', '')

        emergencia.estado = 'RESUELTA'
        emergencia.fecha_hora_resolucion = timezone.now()
        emergencia.acciones_tomadas = acciones
        emergencia.save()

        # Notificar que la emergencia fue resuelta
        NotificacionService.notificar_emergencia_resuelta(emergencia)

        return Response({
            'mensaje': 'Emergencia resuelta exitosamente',
            'tiempo_total_minutos': emergencia.tiempo_resolucion
        })
    
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):

        # Filtrar emergencias por tipo
        tipo_id = request.query_params.get('tipo_id')
        if tipo_id:
            emergencias = self.queryset.filter(tipo_id=tipo_id)
            serializer = self.get_serializer(emergencias, many=True)
            return Response(serializer.data)
        return Response({'error': 'Parámetros tipo_id requerido.'}, status=400)
    
    def notificar_brigada(self, emergencia):

        # Notificar a miembros de la brigada
        brigada = BrigadaEmergencia.objects.filter(
            activo=True,
            disponible=True
        )

        for miembro in brigada:
            NotificacionEmergencia.objects.create(
                emergencia=emergencia,
                destinatario=miembro.usuario,
                tipo_notificacion='APP',
                mensaje=f'EMERGENCIA: {emergencia.tipo.nombre} en {emergencia.descripcion_ubicacion}'
            )

    def _notificar_personal_clave(self, emergencia):

        # Notificar a vigilancia y personal SST
        from usuarios.models import Usuario

        personal = Usuario.objects.filter(
            Q(rol='VIGILANCIA') | Q(rol='BRIGADA'),
            activo=True
        )

        for persona in personal:
            NotificacionEmergencia.objects.create(
                emergencia=emergencia,
                destinatario=persona,
                tipo_notificacion='APP',
                mensaje=f'ALERTA: {emergencia.tipo.nombre} reportada por {emergencia.reportada_por.get_full_name()}'
            )

class BrigadaEmergenciaViewSet(viewsets.ModelViewSet):

    # ViewSet para brigada de emergencia
    queryset = BrigadaEmergencia.objects.all()
    serializer_class = BrigadaEmergenciaSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def disponibles(self, request):

        # Obtener brigadistas disponibles
        brigadistas = BrigadaEmergencia.objects.filter(activo=True, disponible=True)
        serializer = BrigadaEmergenciaSerializer(brigadistas, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cambiar_disponibilidad(self, request, pk=None):

        # Cambiar disponibilidad de brigadista
        brigadista = self.get_object()
        disponible = request.data.get('disponible', None)

        if disponible is not None:
            brigadista.disponible = disponible
            brigadista.save()

            return Response({
                'mensaje': f'Disponibilidad actualizada a {disponible}',
                'disponible': brigadista.disponible
            })

        return Response({'error': 'Parámetro disponible requerido.'}, status=400)

    @action(detail=False, methods=['post', 'get'], url_path='mi-disponibilidad')
    def mi_disponibilidad(self, request):
        """
        GET: Obtiene el estado de disponibilidad del brigadista actual
        POST: Toggle la disponibilidad del brigadista actual

        POST body (opcional):
        - disponible: boolean (si no se envía, hace toggle)
        """
        try:
            brigadista = BrigadaEmergencia.objects.get(usuario=request.user)
        except BrigadaEmergencia.DoesNotExist:
            return Response({
                'error': 'No eres miembro de la brigada de emergencia'
            }, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            return Response({
                'brigadista_id': brigadista.id,
                'usuario': request.user.get_full_name(),
                'disponible': brigadista.disponible,
                'especializacion': brigadista.especializacion,
                'especializacion_display': brigadista.get_especializacion_display(),
                'activo': brigadista.activo
            })

        # POST - Toggle o set disponibilidad
        nuevo_estado = request.data.get('disponible')

        if nuevo_estado is None:
            # Toggle si no se especifica
            brigadista.disponible = not brigadista.disponible
        else:
            brigadista.disponible = bool(nuevo_estado)

        brigadista.save()

        return Response({
            'success': True,
            'mensaje': f'Disponibilidad {"activada" if brigadista.disponible else "desactivada"}',
            'disponible': brigadista.disponible
        })

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtiene estadísticas de la brigada
        """
        total = BrigadaEmergencia.objects.filter(activo=True).count()
        disponibles = BrigadaEmergencia.objects.filter(activo=True, disponible=True).count()

        # Por especialización
        from django.db.models import Count
        por_especializacion = BrigadaEmergencia.objects.filter(
            activo=True
        ).values('especializacion').annotate(
            total=Count('id'),
            disponibles=Count('id', filter=Q(disponible=True))
        )

        return Response({
            'total': total,
            'disponibles': disponibles,
            'no_disponibles': total - disponibles,
            'porcentaje_disponible': round((disponibles / total) * 100, 1) if total > 0 else 0,
            'por_especializacion': list(por_especializacion)
        })
    
class NotificacionEmergenciaViewSet(viewsets.ModelViewSet):

    # ViewSet para notificaciones
    queryset = NotificacionEmergencia.objects.all()
    serializer_class = NotificacionEmergenciaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        
        #Filtrar notificaciones del usuario actual
        return self.queryset.filter(destinatario=self.request.user)
    
    @action(detail=False, methods=['get'])
    def no_leidas(self, request):

        # Obtener notificaciones no leídas
        notificaciones = self.get_queryset().filter(leida=False)
        serializer = self.get_serializer(notificaciones, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def marcar_leida(self, request, pk=None):

        # Marcar notificación como leída
        notificacion = self.get_object()
        notificacion.leida = True
        notificacion.fecha_lectura = timezone.now()
        notificacion.save()
        return Response({'mensaje': 'Notificación marcada como leída'})

class ContactoExternoViewSet(viewsets.ModelViewSet):

    # ViewSet para contactos externos
    queryset = ContactoExterno.objects.filter(activo=True)
    serializer_class = ContactoExternoSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def por_tipo(self, request):

        # Filtrar contactos por tipo
        tipo = request.query_params.get('tipo')
        if tipo:
            contactos = self.queryset.filter(tipo=tipo)
            serializer = self.get_serializer(contactos, many=True)
            return Response(serializer.data)
        return Response({'error': 'Parámetros tipo requerido.'}, status=400)
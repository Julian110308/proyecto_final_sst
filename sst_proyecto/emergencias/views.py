from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django_ratelimit.core import is_ratelimited
from .models import (
    TipoEmergencia,
    Emergencia,
    BrigadaEmergencia,
    NotificacionEmergencia,
    ContactoExterno,
    RegistroEvacuacion,
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


# Solo brigadistas pueden activar emergencias naturales (sismo, deslizamiento)
ROLES_EMERGENCIA_NATURAL = {"BRIGADA"}


class TipoEmergenciaViewSet(viewsets.ModelViewSet):
    # ViewSet para tipos de emergencia — filtra según el rol del usuario
    queryset = TipoEmergencia.objects.all()
    serializer_class = TipoEmergenciaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = TipoEmergencia.objects.filter(activo=True)
        # Solo la brigada ve los tipos de emergencia natural (solo_autorizado)
        if user.rol not in ROLES_EMERGENCIA_NATURAL:
            qs = qs.filter(solo_autorizado=False)
        return qs


class EmergenciaViewSet(viewsets.ModelViewSet):
    # ViewSet para gestión de emergencias
    queryset = Emergencia.objects.select_related("tipo", "reportada_por", "edificio").prefetch_related("atendida_por")
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        Permisos específicos por acción:
        - list, retrieve, create, boton_panico: Todos los autenticados
        - atender, resolver: Solo Brigada y Administrativo
        - update, partial_update, destroy: Solo Administrativo
        - alerta_automatica: AllowAny — autenticación via token en el body/header
        """
        from usuarios.permissions import EsBrigadaOAdministrativo, EsAdministrativo

        if self.action == "alerta_automatica":
            return [AllowAny()]
        elif self.action in ["atender", "resolver", "marcar_falsa_alarma"]:
            return [EsBrigadaOAdministrativo()]
        elif self.action in ["update", "partial_update", "destroy"]:
            return [EsAdministrativo()]

        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return EmergenciaCreateSerializer
        return EmergenciaSerializer

    def create(self, request, *args, **kwargs):
        # Validar que el usuario puede reportar este tipo de emergencia
        tipo_id = request.data.get("tipo")
        if tipo_id:
            try:
                tipo = TipoEmergencia.objects.get(pk=tipo_id)
                if tipo.solo_autorizado and request.user.rol not in ROLES_EMERGENCIA_NATURAL:
                    return Response(
                        {
                            "error": "Este tipo de emergencia (causa natural) solo puede ser activado por la Brigada de Emergencia."
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
            except TipoEmergencia.DoesNotExist:
                pass
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        emergencia = serializer.save(reportada_por=self.request.user)
        if emergencia.tipo.alerta_masiva:
            # Alerta a TODOS los usuarios activos del sistema
            NotificacionService.notificar_emergencia_masiva(emergencia)
        else:
            # Notificación estándar: solo Brigada, Administrativo, Vigilancia
            NotificacionService.notificar_emergencia_creada(emergencia)
        # También notificar vía NotificacionEmergencia (modelo específico)
        self.notificar_brigada(emergencia)

    @extend_schema(
        summary="Botón de pánico",
        description="Activa una emergencia inmediata. Notifica a Brigada y Administrativos. Limitado a 3 activaciones/hora por usuario.",
        tags=["emergencias"],
        responses={201: EmergenciaSerializer, 429: OpenApiResponse(description="Rate limit excedido")},
    )
    @action(detail=False, methods=["post"])
    def boton_panico(self, request):
        # Máximo 3 activaciones por usuario por hora (previene falsas alarmas en loop)
        if is_ratelimited(request, group="boton_panico", key="user_or_ip", rate="3/h", method="POST", increment=True):
            return Response(
                {
                    "error": "Has activado demasiadas alertas de emergencia en poco tiempo. Si es una emergencia real, llama al número de emergencias directamente."
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Endpoint para botón de pánico desde app móvil
        serializer = EmergenciaCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        emergencia = serializer.save(reportada_por=self.request.user)

        # Si el tipo es de alerta masiva (ej. Sismo, Deslizamiento), notificar a TODOS
        if emergencia.tipo.alerta_masiva:
            NotificacionService.notificar_emergencia_masiva(emergencia)
        else:
            NotificacionService.notificar_emergencia_creada(emergencia)
        # También notificar vía NotificacionEmergencia (modelo específico de emergencias)
        self.notificar_brigada(emergencia)

        return Response(
            {
                "emergencia": EmergenciaSerializer(emergencia).data,
                "mensaje": "Emergencia reportada exitosamente. Ayuda en camino.",
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Atender emergencia",
        description="Marca una emergencia como EN_ATENCION. Solo Brigada y Administrativo.",
        tags=["emergencias"],
    )
    @action(detail=True, methods=["post"])
    def atender(self, request, pk=None):
        # Marcar emergencia como en atención
        emergencia = self.get_object()

        if emergencia.estado == "REPORTADA":
            emergencia.estado = "EN_ATENCION"
            emergencia.fecha_hora_atencion = timezone.now()
            emergencia.atendida_por.add(self.request.user)
            emergencia.save()

            # Notificar al usuario que reportó la emergencia
            NotificacionService.notificar_emergencia_atendida(emergencia, self.request.user)

            return Response(
                {
                    "mensaje": "Emergencia marcada como en atención",
                    "tiempo_respuesta_minutos": emergencia.tiempo_respuesta,
                }
            )

        return Response(
            {"error": "La emergencia ya está siendo atendida o no está en estado reportada."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        summary="Resolver emergencia",
        description="Marca una emergencia como RESUELTA. Solo Brigada y Administrativo.",
        tags=["emergencias"],
    )
    @action(detail=True, methods=["post"])
    def resolver(self, request, pk=None):
        # Marcar emergencia como resuelta
        emergencia = self.get_object()

        acciones = request.data.get("acciones_tomadas", "")

        emergencia.estado = "RESUELTA"
        emergencia.fecha_hora_resolucion = timezone.now()
        emergencia.acciones_tomadas = acciones
        emergencia.save()

        # Notificar que la emergencia fue resuelta
        NotificacionService.notificar_emergencia_resuelta(emergencia)

        return Response(
            {"mensaje": "Emergencia resuelta exitosamente", "tiempo_total_minutos": emergencia.tiempo_resolucion}
        )

    @action(detail=True, methods=["post"], url_path="marcar-falsa-alarma")
    def marcar_falsa_alarma(self, request, pk=None):
        emergencia = self.get_object()

        if emergencia.estado in ["RESUELTA", "FALSA_ALARMA"]:
            return Response(
                {"error": "Esta emergencia ya fue resuelta o ya está marcada como falsa alarma."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        motivo = request.data.get("motivo", "")
        if not motivo.strip():
            return Response(
                {"error": "Debe proporcionar un motivo para marcar como falsa alarma."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        emergencia.estado = "FALSA_ALARMA"
        emergencia.motivo_falsa_alarma = motivo
        emergencia.marcada_falsa_por = request.user
        emergencia.fecha_hora_falsa_alarma = timezone.now()
        emergencia.save()

        # Notificar al reportante y a administrativos
        NotificacionService.notificar_falsa_alarma(emergencia, request.user)

        # Contar falsas alarmas del usuario que reportó
        total_falsas = Emergencia.objects.filter(reportada_por=emergencia.reportada_por, estado="FALSA_ALARMA").count()

        return Response(
            {
                "mensaje": "Emergencia marcada como falsa alarma",
                "reportada_por": emergencia.reportada_por.get_full_name()
                if emergencia.reportada_por
                else "Desconocido",
                "total_falsas_alarmas_usuario": total_falsas,
            }
        )

    @action(detail=False, methods=["get"], url_path="falsas-alarmas")
    def falsas_alarmas(self, request):
        from django.db.models import Count

        falsas = Emergencia.objects.filter(estado="FALSA_ALARMA").select_related(
            "reportada_por", "tipo", "marcada_falsa_por"
        )

        # Estadísticas por usuario
        reincidentes = (
            Emergencia.objects.filter(estado="FALSA_ALARMA", reportada_por__isnull=False)
            .values(
                "reportada_por__id",
                "reportada_por__first_name",
                "reportada_por__last_name",
                "reportada_por__numero_documento",
                "reportada_por__rol",
            )
            .annotate(total_falsas=Count("id"))
            .order_by("-total_falsas")
        )

        serializer = EmergenciaSerializer(falsas, many=True)

        return Response(
            {"falsas_alarmas": serializer.data, "reincidentes": list(reincidentes), "total": falsas.count()}
        )

    @action(detail=False, methods=["get"])
    def por_tipo(self, request):
        # Filtrar emergencias por tipo
        tipo_id = request.query_params.get("tipo_id")
        if tipo_id:
            emergencias = self.queryset.filter(tipo_id=tipo_id)
            serializer = self.get_serializer(emergencias, many=True)
            return Response(serializer.data)
        return Response({"error": "Parámetros tipo_id requerido."}, status=400)

    @extend_schema(
        summary="Alerta automática por sensor externo",
        description=(
            "Endpoint para sensores sísmicos u otros sistemas externos. "
            "Requiere el header X-Webhook-Token o campo 'token' en el body. "
            "Crea una emergencia automáticamente y notifica a todos los usuarios."
        ),
        tags=["emergencias"],
        responses={201: EmergenciaSerializer, 401: OpenApiResponse(description="Token inválido")},
    )
    @action(detail=False, methods=["post"], url_path="alerta-automatica")
    def alerta_automatica(self, request):
        # Verificar token secreto del webhook
        token = request.headers.get("X-Webhook-Token") or request.data.get("token", "")
        expected = getattr(settings, "WEBHOOK_EMERGENCIA_TOKEN", "")
        if not token or token != expected:
            return Response({"error": "Token inválido o ausente."}, status=status.HTTP_401_UNAUTHORIZED)

        tipo_nombre = request.data.get("tipo_nombre", "Sismo")
        try:
            tipo = TipoEmergencia.objects.get(nombre=tipo_nombre, activo=True, solo_autorizado=True)
        except TipoEmergencia.DoesNotExist:
            return Response(
                {"error": f"Tipo '{tipo_nombre}' no encontrado o no es un tipo de emergencia natural."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lat = request.data.get("latitud", 5.852)
        lng = request.data.get("longitud", -73.031)
        descripcion = request.data.get(
            "descripcion", f"{tipo_nombre} detectado automáticamente por el sistema de monitoreo."
        )
        ubicacion = request.data.get("ubicacion", "Centro Minero SENA - Detección automática")

        emergencia = Emergencia.objects.create(
            tipo=tipo,
            reportada_por=None,
            latitud=lat,
            longitud=lng,
            descripcion=descripcion,
            descripcion_ubicacion=ubicacion,
            estado="REPORTADA",
            requiere_evacuacion=True,
        )

        NotificacionService.notificar_emergencia_masiva(emergencia)

        return Response(
            {
                "mensaje": f"Alerta masiva de {tipo_nombre} activada automáticamente.",
                "emergencia_id": emergencia.id,
            },
            status=status.HTTP_201_CREATED,
        )

    def notificar_brigada(self, emergencia):
        # Notificar a miembros de la brigada
        brigada = BrigadaEmergencia.objects.filter(activo=True, disponible=True)

        for miembro in brigada:
            NotificacionEmergencia.objects.create(
                emergencia=emergencia,
                destinatario=miembro.usuario,
                tipo_notificacion="APP",
                mensaje=f"EMERGENCIA: {emergencia.tipo.nombre} en {emergencia.descripcion_ubicacion}",
            )

    # ── Evacuación ────────────────────────────────────────────────────────

    @action(detail=False, methods=["get"], url_path="evacuacion-stats")
    def evacuacion_stats(self, request):
        """
        Estadísticas de evacuación para la emergencia de alerta masiva activa.
        Devuelve: total esperado, confirmados, faltantes, detalle por rol/ficha.
        Solo accesible por BRIGADA, COORDINADOR_SST y ADMINISTRATIVO.
        """
        from usuarios.models import Usuario

        if request.user.rol not in {"BRIGADA", "COORDINADOR_SST", "ADMINISTRATIVO"}:
            return Response({"error": "Sin permiso."}, status=status.HTTP_403_FORBIDDEN)

        # Buscar la emergencia de alerta masiva más reciente que esté activa
        emergencia = (
            Emergencia.objects.filter(
                tipo__alerta_masiva=True,
                estado__in=["REPORTADA", "EN_ATENCION"],
            )
            .order_by("-fecha_hora_reporte")
            .first()
        )

        if not emergencia:
            return Response({"activa": False})

        ROLES_ESPERADOS = ["APRENDIZ", "INSTRUCTOR", "ADMINISTRATIVO", "VIGILANCIA", "BRIGADA", "COORDINADOR_SST"]
        usuarios_esperados = Usuario.objects.filter(rol__in=ROLES_ESPERADOS, activo=True)
        total = usuarios_esperados.count()

        confirmados_ids = set(
            RegistroEvacuacion.objects.filter(emergencia=emergencia, confirmado=True).values_list(
                "usuario_id", flat=True
            )
        )
        confirmados = len(confirmados_ids)
        faltantes = total - confirmados

        # Detalle por ficha (aprendices)

        detalle_fichas = []
        fichas = (
            Usuario.objects.filter(rol="APRENDIZ", activo=True, ficha__isnull=False)
            .exclude(ficha="")
            .values_list("ficha", flat=True)
            .distinct()
        )
        for ficha in fichas:
            aprendices_ficha = Usuario.objects.filter(rol="APRENDIZ", activo=True, ficha=ficha)
            total_ficha = aprendices_ficha.count()
            confirmados_ficha = aprendices_ficha.filter(id__in=confirmados_ids).count()
            detalle_fichas.append(
                {
                    "ficha": ficha,
                    "total": total_ficha,
                    "confirmados": confirmados_ficha,
                    "faltantes": total_ficha - confirmados_ficha,
                }
            )

        return Response(
            {
                "activa": True,
                "emergencia_id": emergencia.id,
                "emergencia_tipo": emergencia.tipo.nombre,
                "emergencia_fecha": emergencia.fecha_hora_reporte,
                "total": total,
                "confirmados": confirmados,
                "faltantes": faltantes,
                "porcentaje": round(confirmados / total * 100) if total else 0,
                "fichas": detalle_fichas,
            }
        )

    @action(detail=False, methods=["post"], url_path="evacuacion-confirmar")
    def evacuacion_confirmar(self, request):
        """
        El instructor confirma la presencia de uno o varios aprendices en el punto de encuentro.
        Body: { "emergencia_id": int, "usuario_ids": [int, ...] }
        """
        from usuarios.models import Usuario

        if request.user.rol not in {"INSTRUCTOR", "BRIGADA", "COORDINADOR_SST", "ADMINISTRATIVO"}:
            return Response({"error": "Sin permiso."}, status=status.HTTP_403_FORBIDDEN)

        emergencia_id = request.data.get("emergencia_id")
        usuario_ids = request.data.get("usuario_ids", [])

        if not emergencia_id or not usuario_ids:
            return Response(
                {"error": "emergencia_id y usuario_ids son requeridos."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            emergencia = Emergencia.objects.get(pk=emergencia_id, tipo__alerta_masiva=True)
        except Emergencia.DoesNotExist:
            return Response({"error": "Emergencia no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        # Instructores solo pueden confirmar sus propios aprendices
        if request.user.rol == "INSTRUCTOR":
            fichas = request.user.get_fichas_list() or ([request.user.ficha] if request.user.ficha else [])
            usuarios_permitidos = set(
                Usuario.objects.filter(rol="APRENDIZ", ficha__in=fichas, activo=True).values_list("id", flat=True)
            )
            usuario_ids = [uid for uid in usuario_ids if uid in usuarios_permitidos]

        ahora = timezone.now()
        confirmados = 0
        for uid in usuario_ids:
            obj, created = RegistroEvacuacion.objects.get_or_create(
                emergencia=emergencia,
                usuario_id=uid,
                defaults={"confirmado": True, "confirmado_por": request.user, "fecha_confirmacion": ahora},
            )
            if not created and not obj.confirmado:
                obj.confirmado = True
                obj.confirmado_por = request.user
                obj.fecha_confirmacion = ahora
                obj.save(update_fields=["confirmado", "confirmado_por", "fecha_confirmacion"])
            confirmados += 1

        # Notificar en tiempo real a brigada via WebSocket
        from usuarios.services import _ws_dispatch_roles

        _ws_dispatch_roles(
            roles=["BRIGADA"],
            tipo="SISTEMA",
            titulo="Actualización de evacuación",
            mensaje=f"{request.user.get_full_name()} confirmó {confirmados} persona(s) en punto de encuentro.",
            prioridad="NORMAL",
            url="/",
        )

        return Response({"confirmados": confirmados, "ok": True})


class BrigadaEmergenciaViewSet(viewsets.ModelViewSet):
    # ViewSet para brigada de emergencia
    queryset = BrigadaEmergencia.objects.all()
    serializer_class = BrigadaEmergenciaSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def disponibles(self, request):
        # Obtener brigadistas disponibles
        brigadistas = BrigadaEmergencia.objects.filter(activo=True, disponible=True)
        serializer = BrigadaEmergenciaSerializer(brigadistas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def cambiar_disponibilidad(self, request, pk=None):
        # Cambiar disponibilidad de brigadista
        brigadista = self.get_object()
        disponible = request.data.get("disponible", None)

        if disponible is not None:
            brigadista.disponible = disponible
            brigadista.save()

            return Response(
                {"mensaje": f"Disponibilidad actualizada a {disponible}", "disponible": brigadista.disponible}
            )

        return Response({"error": "Parámetro disponible requerido."}, status=400)

    @action(detail=False, methods=["post", "get"], url_path="mi-disponibilidad")
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
            return Response({"error": "No eres miembro de la brigada de emergencia"}, status=status.HTTP_404_NOT_FOUND)

        if request.method == "GET":
            return Response(
                {
                    "brigadista_id": brigadista.id,
                    "usuario": request.user.get_full_name(),
                    "disponible": brigadista.disponible,
                    "especializacion": brigadista.especializacion,
                    "especializacion_display": brigadista.get_especializacion_display(),
                    "activo": brigadista.activo,
                }
            )

        # POST - Toggle o set disponibilidad
        nuevo_estado = request.data.get("disponible")

        if nuevo_estado is None:
            # Toggle si no se especifica
            brigadista.disponible = not brigadista.disponible
        else:
            brigadista.disponible = bool(nuevo_estado)

        brigadista.save()

        return Response(
            {
                "success": True,
                "mensaje": f"Disponibilidad {'activada' if brigadista.disponible else 'desactivada'}",
                "disponible": brigadista.disponible,
            }
        )

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        """
        Obtiene estadísticas de la brigada
        """
        total = BrigadaEmergencia.objects.filter(activo=True).count()
        disponibles = BrigadaEmergencia.objects.filter(activo=True, disponible=True).count()

        # Por especialización
        from django.db.models import Count

        por_especializacion = (
            BrigadaEmergencia.objects.filter(activo=True)
            .values("especializacion")
            .annotate(total=Count("id"), disponibles=Count("id", filter=Q(disponible=True)))
        )

        return Response(
            {
                "total": total,
                "disponibles": disponibles,
                "no_disponibles": total - disponibles,
                "porcentaje_disponible": round((disponibles / total) * 100, 1) if total > 0 else 0,
                "por_especializacion": list(por_especializacion),
            }
        )


class NotificacionEmergenciaViewSet(viewsets.ModelViewSet):
    # ViewSet para notificaciones
    queryset = NotificacionEmergencia.objects.all()
    serializer_class = NotificacionEmergenciaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filtrar notificaciones del usuario actual
        return self.queryset.filter(destinatario=self.request.user)

    @action(detail=False, methods=["get"])
    def no_leidas(self, request):
        # Obtener notificaciones no leídas
        notificaciones = self.get_queryset().filter(leida=False)
        serializer = self.get_serializer(notificaciones, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def marcar_leida(self, request, pk=None):
        # Marcar notificación como leída
        notificacion = self.get_object()
        notificacion.leida = True
        notificacion.fecha_lectura = timezone.now()
        notificacion.save()
        return Response({"mensaje": "Notificación marcada como leída"})


class ContactoExternoViewSet(viewsets.ModelViewSet):
    # ViewSet para contactos externos
    queryset = ContactoExterno.objects.filter(activo=True)
    serializer_class = ContactoExternoSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def por_tipo(self, request):
        # Filtrar contactos por tipo
        tipo = request.query_params.get("tipo")
        if tipo:
            contactos = self.queryset.filter(tipo=tipo)
            serializer = self.get_serializer(contactos, many=True)
            return Response(serializer.data)
        return Response({"error": "Parámetros tipo requerido."}, status=400)

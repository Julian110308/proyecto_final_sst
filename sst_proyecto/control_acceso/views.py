import io

import qrcode
from PIL import Image, ImageDraw, ImageFont

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse

from .models import RegistroAcceso, ConfiguracionAforo
from .serializers import (
    RegistroAccesoSerializer,
    ConfiguracionAforoSerializer,
    RegistrarAccesoSerializer,
)
from .utils import (
    verificar_aforo_actual,
    obtener_estadisticas_hoy,
    generar_token_qr,
    validar_token_qr,
)
from usuarios.models import Usuario
from usuarios.permissions import EsVigilanciaOAdministrativo

# Servicio centralizado de notificaciones
from usuarios.services import NotificacionService


class RegistroAccesoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar registros de acceso
    PERMISOS: VIGILANCIA, ADMINISTRATIVO e INSTRUCTOR pueden registrar acceso
    """

    queryset = RegistroAcceso.objects.select_related("usuario")
    serializer_class = RegistroAccesoSerializer
    permission_classes = [EsVigilanciaOAdministrativo]

    def get_permissions(self):
        """
        Instructor puede acceder a acciones de asistencia y estadísticas/registros recientes.
        Las demás acciones requieren VIGILANCIA o ADMINISTRATIVO.
        """
        if self.action in [
            "registrar_asistencia_manual",
            "registrar_asistencia_masiva",
            "estadisticas",
            "registros_recientes",
            "mi_estado",
            "mi_qr",
            "mi_qr_imagen",
            "escanear_qr",
        ]:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        """
        Filtrar registros según parámetros de consulta.
        Usuarios sin rol privilegiado solo ven sus propios registros.
        """
        user = self.request.user
        ROLES_PRIVILEGIADOS = {"VIGILANCIA", "ADMINISTRATIVO", "COORDINADOR_SST", "INSTRUCTOR"}

        if user.is_superuser or user.rol in ROLES_PRIVILEGIADOS:
            queryset = RegistroAcceso.objects.all()
        else:
            queryset = RegistroAcceso.objects.filter(usuario=user)

        # Filtrar por fecha
        fecha = self.request.query_params.get("fecha", None)
        if fecha:
            queryset = queryset.filter(fecha_hora_ingreso__date=fecha)

        # Filtrar por usuario (solo roles privilegiados pueden filtrar por otro usuario)
        usuario_id = self.request.query_params.get("usuario", None)
        if usuario_id and (user.is_superuser or user.rol in ROLES_PRIVILEGIADOS):
            queryset = queryset.filter(usuario_id=usuario_id)

        # Filtrar por estado (dentro del centro)
        dentro = self.request.query_params.get("dentro", None)
        if dentro == "true":
            queryset = queryset.filter(fecha_hora_egreso__isnull=True)
        elif dentro == "false":
            queryset = queryset.filter(fecha_hora_egreso__isnull=False)

        return queryset.order_by("-fecha_hora_ingreso")

    @action(detail=False, methods=["post"])
    def registrar_ingreso(self, request):
        """
        Registra el ingreso de un usuario al centro
        """
        serializer = RegistrarAccesoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        usuario_id = serializer.validated_data.get("usuario_id")
        metodo = serializer.validated_data.get("metodo", "MANUAL")

        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        # Verificar que el usuario no esté ya dentro
        acceso_abierto = RegistroAcceso.objects.filter(usuario=usuario, fecha_hora_egreso__isnull=True).first()

        if acceso_abierto:
            return Response(
                {"error": "El usuario ya tiene un ingreso activo sin salida"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar aforo
        aforo_info = verificar_aforo_actual()
        if aforo_info["alerta"] == "CRITICO":
            return Response(
                {
                    "error": "Aforo máximo alcanzado",
                    "mensaje": aforo_info["mensaje"],
                    "aforo_actual": aforo_info["personas_dentro"],
                    "aforo_maximo": aforo_info["aforo_maximo"],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Crear registro de ingreso
        registro = RegistroAcceso.objects.create(
            usuario=usuario,
            tipo="INGRESO",
            metodo_ingreso=metodo,
        )

        # Notificar si el aforo está en nivel ADVERTENCIA (≥70%) o CRITICO (≥90%)
        if aforo_info["alerta"] in ["ADVERTENCIA", "CRITICO"]:
            NotificacionService.notificar_aforo_critico(
                aforo_info["personas_dentro"], aforo_info["aforo_maximo"], porcentaje_alerta=70
            )

        return Response(
            {
                "success": True,
                "mensaje": f"Ingreso registrado para {usuario.get_full_name()}",
                "registro_id": registro.id,
                "fecha_hora": registro.fecha_hora_ingreso,
                "aforo": aforo_info,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"])
    def registrar_egreso(self, request):
        """
        Registra la salida de un usuario del centro
        """
        serializer = RegistrarAccesoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        usuario_id = serializer.validated_data.get("usuario_id")
        metodo = serializer.validated_data.get("metodo", "MANUAL")

        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        # Buscar el último ingreso sin egreso
        registro = (
            RegistroAcceso.objects.filter(usuario=usuario, fecha_hora_egreso__isnull=True)
            .order_by("-fecha_hora_ingreso")
            .first()
        )

        if not registro:
            return Response({"error": "No hay un ingreso activo para este usuario"}, status=status.HTTP_400_BAD_REQUEST)

        # Actualizar el registro con la salida
        registro.fecha_hora_egreso = timezone.now()
        registro.metodo_egreso = metodo
        registro.save()

        # Calcular tiempo de permanencia
        tiempo_permanencia = registro.fecha_hora_egreso - registro.fecha_hora_ingreso

        return Response(
            {
                "success": True,
                "mensaje": f"Salida registrada para {usuario.get_full_name()}",
                "registro_id": registro.id,
                "fecha_hora_ingreso": registro.fecha_hora_ingreso,
                "fecha_hora_egreso": registro.fecha_hora_egreso,
                "tiempo_permanencia": str(tiempo_permanencia),
            }
        )

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        """
        Obtiene estadísticas de acceso
        """
        estadisticas = obtener_estadisticas_hoy()
        return Response(estadisticas)

    @action(detail=False, methods=["get"])
    def registros_recientes(self, request):
        """
        Obtiene los registros más recientes.
        Solo accesible por roles privilegiados (VIGILANCIA, ADMINISTRATIVO, INSTRUCTOR).
        Soporta filtros: ?limite=, ?ficha=, ?programa=, ?rol=, ?estado=dentro|fuera
        """
        ROLES_PRIVILEGIADOS = {"VIGILANCIA", "ADMINISTRATIVO", "COORDINADOR_SST", "INSTRUCTOR"}
        if not request.user.is_superuser and request.user.rol not in ROLES_PRIVILEGIADOS:
            return Response(
                {"error": "No tiene permisos para ver registros de acceso de otros usuarios."},
                status=status.HTTP_403_FORBIDDEN,
            )

        limite = int(request.query_params.get("limite", 200))
        ficha = request.query_params.get("ficha", "").strip()
        programa = request.query_params.get("programa", "").strip()
        fecha = request.query_params.get("fecha", "").strip()  # YYYY-MM-DD

        qs = RegistroAcceso.objects.select_related("usuario").all().order_by("-fecha_hora_ingreso")

        if fecha:
            qs = qs.filter(fecha_hora_ingreso__date=fecha)
        if ficha:
            qs = qs.filter(usuario__ficha__icontains=ficha)
        if programa:
            qs = qs.filter(usuario__programa_formacion__icontains=programa)

        # Mostrar solo el registro más reciente por usuario (el más reciente es el primero por el order_by)
        vistos = set()
        registros_unicos = []
        for reg in qs[: limite * 5]:  # margen extra para cubrir duplicados
            if reg.usuario_id not in vistos:
                vistos.add(reg.usuario_id)
                registros_unicos.append(reg)
            if len(registros_unicos) >= limite:
                break
        registros = registros_unicos

        data = []
        for registro in registros:
            data.append(
                {
                    "id": registro.id,
                    "usuario": {
                        "id": registro.usuario.id,
                        "nombre": registro.usuario.get_full_name(),
                        "documento": registro.usuario.numero_documento,
                        "rol": registro.usuario.get_rol_display(),
                        "ficha": registro.usuario.ficha or "",
                        "programa_formacion": registro.usuario.programa_formacion or "",
                    },
                    "fecha_hora_ingreso": registro.fecha_hora_ingreso,
                    "fecha_hora_egreso": registro.fecha_hora_egreso,
                    "metodo_ingreso": registro.get_metodo_ingreso_display(),
                    "metodo_egreso": registro.get_metodo_egreso_display() if registro.metodo_egreso else None,
                    "estado": "DENTRO" if not registro.fecha_hora_egreso else "SALIO",
                }
            )

        return Response(data)

    @action(detail=False, methods=["get"])
    def personas_en_centro(self, request):
        """
        Retorna las personas actualmente dentro del centro.
        Usado para el monitoreo en tiempo real.
        Accesible por VIGILANCIA y ADMINISTRATIVO.
        Soporta filtros: ?ficha=, ?programa=
        """
        hoy = timezone.now().date()
        ficha = request.query_params.get("ficha", "").strip()
        programa = request.query_params.get("programa", "").strip()

        registros_activos = RegistroAcceso.objects.filter(
            tipo="INGRESO", fecha_hora_egreso__isnull=True, fecha_hora_ingreso__date=hoy
        ).select_related("usuario")

        if ficha:
            registros_activos = registros_activos.filter(usuario__ficha__icontains=ficha)
        if programa:
            registros_activos = registros_activos.filter(usuario__programa_formacion__icontains=programa)

        personas = []
        for registro in registros_activos:
            personas.append(
                {
                    "id": registro.usuario.id,
                    "nombre": registro.usuario.get_full_name() or registro.usuario.username,
                    "rol": registro.usuario.get_rol_display(),
                    "rol_code": registro.usuario.rol,
                    "ficha": registro.usuario.ficha or "",
                    "programa_formacion": registro.usuario.programa_formacion or "",
                    "hora_ingreso": registro.fecha_hora_ingreso.strftime("%H:%M"),
                    "metodo": registro.get_metodo_ingreso_display(),
                }
            )

        return Response({"total": len(personas), "personas": personas})

    @action(detail=False, methods=["post"], url_path="registrar_asistencia_manual")
    def registrar_asistencia_manual(self, request):
        """
        Registra la asistencia manual de un aprendiz (para instructores)
        PERMISOS: INSTRUCTOR, VIGILANCIA, ADMINISTRATIVO
        """
        if request.user.rol not in ["INSTRUCTOR", "VIGILANCIA", "ADMINISTRATIVO"]:
            return Response(
                {"success": False, "error": "No tiene permisos para registrar asistencia"},
                status=status.HTTP_403_FORBIDDEN,
            )

        usuario_id = request.data.get("usuario_id")

        if not usuario_id:
            return Response(
                {"success": False, "error": "Se requiere el ID del usuario"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response({"success": False, "error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        # Verificar que no tenga ya un registro de hoy
        hoy = timezone.now().date()
        registro_existente = RegistroAcceso.objects.filter(usuario=usuario, fecha_hora_ingreso__date=hoy).first()

        if registro_existente:
            return Response(
                {"success": False, "error": "El usuario ya tiene un registro de asistencia para hoy"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        registro = RegistroAcceso.objects.create(
            usuario=usuario,
            tipo="INGRESO",
            metodo_ingreso="MANUAL",
        )

        return Response(
            {
                "success": True,
                "message": f"Asistencia registrada para {usuario.get_full_name()}",
                "registro_id": registro.id,
                "hora_registro": registro.fecha_hora_ingreso.strftime("%H:%M"),
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="registrar_asistencia_masiva")
    def registrar_asistencia_masiva(self, request):
        """
        Registra la asistencia manual de multiples aprendices
        PERMISOS: INSTRUCTOR, VIGILANCIA, ADMINISTRATIVO
        """
        if request.user.rol not in ["INSTRUCTOR", "VIGILANCIA", "ADMINISTRATIVO"]:
            return Response(
                {"success": False, "error": "No tiene permisos para registrar asistencia"},
                status=status.HTTP_403_FORBIDDEN,
            )

        usuarios_ids = request.data.get("usuarios_ids", [])

        if not usuarios_ids:
            return Response(
                {"success": False, "error": "Se requiere una lista de IDs de usuarios"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        hoy = timezone.now().date()
        errores = []

        # Obtener todos los usuarios de una sola query
        usuarios = Usuario.objects.filter(id__in=usuarios_ids)
        usuarios_dict = {u.id: u for u in usuarios}

        # IDs no encontrados
        ids_no_encontrados = set(usuarios_ids) - set(usuarios_dict.keys())
        for uid in ids_no_encontrados:
            errores.append(f"Usuario ID {uid} no encontrado")

        # Obtener IDs que ya tienen registro hoy (una sola query)
        ids_con_registro = set(
            RegistroAcceso.objects.filter(
                usuario_id__in=usuarios_dict.keys(), fecha_hora_ingreso__date=hoy
            ).values_list("usuario_id", flat=True)
        )

        for uid in ids_con_registro:
            errores.append(f"{usuarios_dict[uid].get_full_name()} ya tiene registro")

        # Crear registros en bulk para los que sí proceden
        registros_nuevos = []
        for uid, usuario in usuarios_dict.items():
            if uid not in ids_con_registro:
                registros_nuevos.append(
                    RegistroAcceso(
                        usuario=usuario,
                        tipo="INGRESO",
                        metodo_ingreso="MANUAL",
                    )
                )

        if registros_nuevos:
            RegistroAcceso.objects.bulk_create(registros_nuevos)

        registrados = len(registros_nuevos)

        return Response(
            {
                "success": True,
                "message": f"Asistencia registrada para {registrados} aprendiz(es)",
                "registrados": registrados,
                "errores": errores if errores else None,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="mi-estado")
    def mi_estado(self, request):
        """
        Retorna el estado de acceso actual del usuario autenticado.
        GET /api/acceso/registros/mi-estado/
        """
        hoy = timezone.now().date()
        registro = (
            RegistroAcceso.objects.filter(
                usuario=request.user, tipo="INGRESO", fecha_hora_egreso__isnull=True, fecha_hora_ingreso__date=hoy
            )
            .order_by("-fecha_hora_ingreso")
            .first()
        )

        return Response(
            {
                "en_centro": registro is not None,
                "hora_ingreso": registro.fecha_hora_ingreso.strftime("%H:%M") if registro else None,
            }
        )

    @action(detail=False, methods=["get"], url_path="buscar_usuario")
    def buscar_usuario(self, request):
        """
        Busca un usuario por número de documento.
        GET /api/acceso/registros/buscar_usuario/?documento=<numero>
        Accesible por VIGILANCIA, ADMINISTRATIVO e INSTRUCTOR.
        """
        documento = request.query_params.get("documento", "").strip()
        if not documento:
            return Response({"error": "Se requiere el parámetro documento"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            usuario = Usuario.objects.get(numero_documento=documento, activo=True)
        except Usuario.DoesNotExist:
            return Response({"error": "No se encontró un usuario con ese documento"}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "id": usuario.id,
                "nombre": usuario.get_full_name() or usuario.username,
                "rol": usuario.get_rol_display(),
                "rol_code": usuario.rol,
                "ficha": usuario.ficha or "",
                "programa": usuario.programa_formacion or "",
            }
        )

    @extend_schema(
        summary="Token QR del usuario autenticado",
        tags=["acceso"],
        responses={200: OpenApiResponse(description="Token QR válido para el día")},
    )
    @action(detail=False, methods=["get"], url_path="mi-qr")
    def mi_qr(self, request):
        """
        Devuelve el token QR del usuario autenticado.
        GET /api/acceso/registros/mi-qr/
        """
        token = generar_token_qr(request.user.id)
        return Response(
            {
                "token": token,
                "usuario": request.user.get_full_name() or request.user.username,
                "rol": request.user.get_rol_display(),
                "ficha": request.user.ficha or "",
                "programa": request.user.programa_formacion or "",
                "documento": request.user.numero_documento or "",
            }
        )

    @action(detail=False, methods=["get"], url_path="mi-qr-imagen")
    def mi_qr_imagen(self, request):
        """
        Devuelve el QR del usuario como imagen PNG descargable.
        GET /api/acceso/registros/mi-qr-imagen/
        """
        user = request.user
        token = generar_token_qr(user.id)

        # Generar QR
        qr = qrcode.QRCode(
            version=3,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(token)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        # Agregar banda inferior con nombre y datos
        qr_w, qr_h = qr_img.size
        banda_h = 90
        final_img = Image.new("RGB", (qr_w, qr_h + banda_h), "#ffffff")
        final_img.paste(qr_img, (0, 0))

        draw = ImageDraw.Draw(final_img)

        # Buscar fuente disponible en Windows; caer en la fuente bitmap si no hay ninguna
        font_name = None
        font_data = None
        for ruta in [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
        ]:
            try:
                font_name = ImageFont.truetype(ruta, 17)
                font_data = ImageFont.truetype(ruta, 13)
                break
            except OSError:
                continue
        if font_name is None:
            font_name = ImageFont.load_default()
            font_data = font_name

        def texto_centrado(draw, y, texto, font, fill):
            """Dibuja texto centrado horizontalmente sin usar anchor."""
            try:
                bbox = draw.textbbox((0, 0), texto, font=font)
                tw = bbox[2] - bbox[0]
            except AttributeError:
                tw = len(texto) * 7  # estimación para fuente bitmap
            x = max(0, (qr_w - tw) // 2)
            draw.text((x, y), texto, font=font, fill=fill)

        nombre = user.get_full_name() or user.username
        texto_centrado(draw, qr_h + 10, nombre, font_name, "#1a1a1a")

        linea2_parts = []
        if user.rol:
            linea2_parts.append(user.get_rol_display())
        if user.ficha:
            linea2_parts.append(f"Ficha: {user.ficha}")
        if linea2_parts:
            texto_centrado(draw, qr_h + 34, " · ".join(linea2_parts), font_data, "#555555")

        linea3_parts = []
        if user.numero_documento:
            linea3_parts.append(f"Doc: {user.numero_documento}")
        if user.programa_formacion:
            linea3_parts.append(user.programa_formacion[:30])
        if linea3_parts:
            texto_centrado(draw, qr_h + 56, " · ".join(linea3_parts), font_data, "#888888")

        # Serializar a PNG
        buffer = io.BytesIO()
        final_img.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)

        nombre_archivo = f"QR_{user.username}_SST.png"
        response = HttpResponse(buffer, content_type="image/png")
        response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
        return response

    @action(detail=False, methods=["post"], url_path="escanear-qr")
    def escanear_qr(self, request):
        """
        Vigilancia escanea el QR de un usuario → registra ingreso o egreso automáticamente.
        POST /api/acceso/registros/escanear-qr/
        Body: { "token": "SST-..." }
        Requiere rol VIGILANCIA o ADMINISTRATIVO.
        """
        if request.user.rol not in {"VIGILANCIA", "ADMINISTRATIVO", "COORDINADOR_SST"}:
            return Response({"error": "Sin permiso."}, status=status.HTTP_403_FORBIDDEN)

        token = (request.data.get("token") or "").strip()
        if not token:
            return Response({"error": "Token requerido."}, status=status.HTTP_400_BAD_REQUEST)

        # modo puede ser 'INGRESO' o 'EGRESO'; si no se envía, auto-detecta
        modo = (request.data.get("modo") or "").upper()
        if modo not in {"INGRESO", "EGRESO"}:
            modo = None  # auto-detectar

        user_id, error = validar_token_qr(token)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        try:
            usuario = Usuario.objects.get(pk=user_id, activo=True)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado o inactivo."}, status=status.HTTP_404_NOT_FOUND)

        hoy = timezone.now().date()

        registro_abierto = (
            RegistroAcceso.objects.filter(
                usuario=usuario,
                tipo="INGRESO",
                fecha_hora_egreso__isnull=True,
                fecha_hora_ingreso__date=hoy,
            )
            .order_by("-fecha_hora_ingreso")
            .first()
        )

        # Determinar acción según modo explícito o auto-detección
        accion_final = modo or ("EGRESO" if registro_abierto else "INGRESO")

        if accion_final == "EGRESO":
            if not registro_abierto:
                return Response(
                    {"error": f"{usuario.get_full_name()} no tiene un ingreso activo hoy."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            registro_abierto.fecha_hora_egreso = timezone.now()
            registro_abierto.metodo_egreso = "QR"
            registro_abierto.save(update_fields=["fecha_hora_egreso", "metodo_egreso"])
            accion = "EGRESO"
            hora = registro_abierto.fecha_hora_egreso
        else:
            if registro_abierto:
                return Response(
                    {"error": f"{usuario.get_full_name()} ya tiene un ingreso activo hoy. ¿Desea registrar su egreso?"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            aforo = verificar_aforo_actual()
            if aforo["alerta"] == "CRITICO":
                return Response(
                    {"error": "Aforo máximo alcanzado. No se puede registrar ingreso."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            registro = RegistroAcceso.objects.create(
                usuario=usuario,
                tipo="INGRESO",
                metodo_ingreso="QR",
            )
            accion = "INGRESO"
            hora = registro.fecha_hora_ingreso

        hora_local = timezone.localtime(hora)
        return Response(
            {
                "accion": accion,
                "hora": hora_local.isoformat(),
                "usuario": {
                    "nombre": usuario.get_full_name() or usuario.username,
                    "documento": usuario.numero_documento or "",
                    "rol": usuario.get_rol_display(),
                    "rol_code": usuario.rol,
                    "ficha": usuario.ficha or "",
                    "programa": usuario.programa_formacion or "",
                },
            }
        )


class ConfiguracionAforoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para configuración de aforo
    """

    queryset = ConfiguracionAforo.objects.all()
    serializer_class = ConfiguracionAforoSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Aforo actual del centro",
        description="Retorna las personas actualmente dentro del centro, el límite y el porcentaje de ocupación. Cacheado 30 s.",
        tags=["acceso"],
    )
    @action(detail=False, methods=["get"])
    def aforo_actual(self, request):
        """
        Obtiene el aforo actual del centro
        """
        aforo_info = verificar_aforo_actual()
        return Response(aforo_info)


@login_required
def mi_qr_view(request):
    """Vista Django simple para generar el token QR del usuario actual."""
    user = request.user
    token = generar_token_qr(user.id)
    return JsonResponse(
        {
            "token": token,
            "usuario": user.get_full_name() or user.username,
            "rol": user.get_rol_display(),
            "ficha": user.ficha or "",
            "programa": user.programa_formacion or "",
            "documento": user.numero_documento or "",
        }
    )

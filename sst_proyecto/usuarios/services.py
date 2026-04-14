# usuarios/services.py
"""
Servicio centralizado de notificaciones para el sistema SST.
Este módulo contiene funciones para enviar notificaciones automáticas
cuando ocurren eventos importantes en el sistema.
"""

import json
import logging
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Notificacion, Usuario, PushSubscripcion

logger = logging.getLogger(__name__)


class WebPushService:
    """
    Servicio para enviar notificaciones Web Push a dispositivos móviles.
    Utiliza VAPID para autenticación con los servidores push.
    """

    @staticmethod
    def enviar_a_usuario(usuario, titulo, cuerpo, url="/emergencias/", icono="/static/icons/icon-192.png"):
        """
        Envía una notificación push a todas las suscripciones activas de un usuario.
        Si falla una suscripción caducada, la desactiva automáticamente.
        """
        if not settings.VAPID_PUBLIC_KEY or not settings.VAPID_PRIVATE_KEY:
            return

        try:
            from pywebpush import webpush
        except ImportError:
            logger.warning("pywebpush no instalado. Notificaciones push desactivadas.")
            return

        subscripciones = PushSubscripcion.objects.filter(usuario=usuario, activo=True)
        payload = json.dumps(
            {
                "title": titulo,
                "body": cuerpo,
                "icon": icono,
                "url": url,
                "badge": "/static/icons/icon-192.png",
            }
        )
        vapid_claims = {"sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"}

        for sub in subscripciones:
            try:
                webpush(
                    subscription_info={
                        "endpoint": sub.endpoint,
                        "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                    },
                    data=payload,
                    vapid_private_key=settings.VAPID_PRIVATE_KEY,
                    vapid_claims=vapid_claims,
                )
            except Exception as e:
                logger.warning(f"Push fallido para {usuario.username}: {e}")
                # Suscripción caducada o inválida → desactivar
                sub.activo = False
                sub.save(update_fields=["activo"])

    @staticmethod
    def enviar_a_roles(roles, titulo, cuerpo, url="/emergencias/", icono="/static/icons/icon-192.png"):
        """Envía notificación push a todos los usuarios activos de los roles indicados."""
        usuarios = Usuario.objects.filter(rol__in=roles, activo=True)
        for usuario in usuarios:
            WebPushService.enviar_a_usuario(usuario, titulo, cuerpo, url, icono)


def _ws_dispatch_roles(roles, tipo, titulo, mensaje, prioridad="NORMAL", url="/"):
    """
    Envía un evento WebSocket al grupo de canal de cada rol indicado.
    Si el channel layer no está disponible (tests sin Redis, dev sin Redis)
    falla silenciosamente para no bloquear el flujo principal.
    """
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        if channel_layer is None:
            return
        data = {
            "tipo": tipo,
            "titulo": titulo,
            "mensaje": mensaje[:120],
            "prioridad": prioridad,
            "url": url,
        }
        for rol in roles:
            async_to_sync(channel_layer.group_send)(
                f"notif_rol_{rol}",
                {"type": "notification", "data": data},
            )
    except Exception as e:
        logger.warning("WS dispatch error: %s", e)


def _ws_dispatch_usuario(usuario_id, tipo, titulo, mensaje, prioridad="NORMAL", url="/"):
    """Envía un evento WebSocket al grupo personal de un usuario."""
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        if channel_layer is None:
            return
        data = {
            "tipo": tipo,
            "titulo": titulo,
            "mensaje": mensaje[:120],
            "prioridad": prioridad,
            "url": url,
        }
        async_to_sync(channel_layer.group_send)(
            f"notif_user_{usuario_id}",
            {"type": "notification", "data": data},
        )
    except Exception as e:
        logger.warning("WS dispatch error: %s", e)


class NotificacionService:
    """
    Servicio para crear y enviar notificaciones automáticas
    """

    # ============================================================
    # NOTIFICACIONES DE EMERGENCIA
    # ============================================================

    @staticmethod
    def notificar_emergencia_creada(emergencia):
        """
        Notifica a Brigada y Administrativos cuando se crea una emergencia.

        Args:
            emergencia: Instancia del modelo Emergencia
        """
        titulo = f"EMERGENCIA: {emergencia.tipo.nombre if hasattr(emergencia.tipo, 'nombre') else emergencia.tipo}"
        mensaje = (
            f"Se ha reportado una emergencia.\n"
            f"Descripción: {emergencia.descripcion[:100]}{'...' if len(emergencia.descripcion) > 100 else ''}\n"
            f"Ubicación: {emergencia.descripcion_ubicacion or 'No especificada'}\n"
            f"Reportada por: {emergencia.reportada_por.get_full_name() if emergencia.reportada_por else 'Anónimo'}"
        )

        url = "/emergencias/"

        # Notificar solo a Brigada
        notificaciones = []
        usuarios = Usuario.objects.filter(rol="BRIGADA", activo=True)

        for usuario in usuarios:
            notificaciones.append(
                Notificacion(
                    destinatario=usuario,
                    titulo=titulo,
                    mensaje=mensaje,
                    tipo="EMERGENCIA",
                    prioridad="ALTA",
                    url_relacionada=url,
                )
            )

        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)

        # WebSocket — notificación instantánea en el navegador
        _ws_dispatch_roles(
            roles=["BRIGADA"],
            tipo="EMERGENCIA",
            titulo=titulo,
            mensaje=mensaje,
            prioridad="ALTA",
            url="/emergencias/",
        )

        # Web Push a dispositivos móviles
        tipo_nombre = emergencia.tipo.nombre if emergencia.tipo else "Emergencia"
        WebPushService.enviar_a_roles(
            roles=["BRIGADA"],
            titulo=f"EMERGENCIA: {tipo_nombre}",
            cuerpo=f"{emergencia.descripcion[:80]} — Reportado por {emergencia.reportada_por.get_full_name() if emergencia.reportada_por else 'Anonimo'}",
            url="/emergencias/",
        )

        # Email
        lista_usuarios = list(usuarios)
        EmailNotificationService.notificar_emergencia(emergencia, lista_usuarios)

        return len(notificaciones)

    @staticmethod
    def notificar_emergencia_masiva(emergencia):
        """
        Alerta masiva: notifica solo a los usuarios que están actualmente en el centro.
        Un usuario está en el centro si tiene un RegistroAcceso de tipo INGRESO
        sin egreso registrado el día de hoy.
        """
        from control_acceso.models import RegistroAcceso

        tipo_nombre = emergencia.tipo.nombre if emergencia.tipo else "Emergencia"
        titulo = f"⚠️ ALERTA GENERAL: {tipo_nombre}"
        mensaje = (
            f"Se ha activado una alerta general de {tipo_nombre}.\n"
            f"{emergencia.descripcion[:150]}{'...' if len(emergencia.descripcion) > 150 else ''}\n"
            f"Sigue las instrucciones del personal de seguridad."
        )
        url = "/emergencias/"

        # IDs de usuarios actualmente dentro del centro
        hoy = timezone.now().date()
        ids_en_centro = RegistroAcceso.objects.filter(
            tipo="INGRESO",
            fecha_hora_egreso__isnull=True,
            fecha_hora_ingreso__date=hoy,
        ).values_list("usuario_id", flat=True)

        # Usuarios internos en el centro (por RegistroAcceso)
        usuarios_internos = Usuario.objects.filter(
            id__in=ids_en_centro,
            activo=True,
        ).exclude(rol="VISITANTE")

        # Visitantes en el centro: registrados hoy sin hora de salida
        from usuarios.models import Visitante

        ids_visitantes_en_centro = Visitante.objects.filter(
            fecha_visita=hoy,
            hora_salida__isnull=True,
            usuario__isnull=False,
            usuario__activo=True,
        ).values_list("usuario_id", flat=True)
        visitantes_en_centro = Usuario.objects.filter(
            id__in=ids_visitantes_en_centro,
            rol="VISITANTE",
        )

        todos_en_centro = list(usuarios_internos) + list(visitantes_en_centro)

        notificaciones = [
            Notificacion(
                destinatario=u,
                titulo=titulo,
                mensaje=mensaje,
                tipo="EMERGENCIA",
                prioridad="ALTA",
                url_relacionada=url,
            )
            for u in todos_en_centro
        ]
        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)

        # WebSocket a todos los roles activos incluido VISITANTE
        _ws_dispatch_roles(
            roles=["COORDINADOR_SST", "BRIGADA", "VIGILANCIA", "INSTRUCTOR", "APRENDIZ", "VISITANTE"],
            tipo="EMERGENCIA",
            titulo=titulo,
            mensaje=mensaje,
            prioridad="ALTA",
            url=url,
        )

        # Web Push a todos incluido VISITANTE
        WebPushService.enviar_a_roles(
            roles=["COORDINADOR_SST", "BRIGADA", "VIGILANCIA", "INSTRUCTOR", "APRENDIZ", "VISITANTE"],
            titulo=titulo,
            cuerpo=mensaje[:100],
            url=url,
        )

        # Email a todos los que están en el centro (internos + visitantes)
        EmailNotificationService.notificar_emergencia(emergencia, todos_en_centro)

        return len(notificaciones)

    @staticmethod
    def notificar_emergencia_atendida(emergencia, brigadista):
        """
        Notifica cuando un brigadista atiende una emergencia.

        Args:
            emergencia: Instancia del modelo Emergencia
            brigadista: Usuario que atiende la emergencia
        """
        titulo = "✅ Emergencia en atención"
        mensaje = (
            f"La emergencia ha sido tomada por {brigadista.get_full_name()}.\n"
            f"Tipo: {emergencia.tipo.nombre if hasattr(emergencia.tipo, 'nombre') else emergencia.tipo}"
        )

        # Notificar al usuario que reportó (si existe)
        if emergencia.reportada_por:
            # Usar dashboard para roles sin acceso a emergencias
            url_reportante = "/dashboard/"
            if emergencia.reportada_por.rol in ["BRIGADA", "COORDINADOR_SST", "VIGILANCIA", "INSTRUCTOR"]:
                url_reportante = "/emergencias/"

            Notificacion.crear_notificacion(
                destinatario=emergencia.reportada_por,
                titulo=titulo,
                mensaje=mensaje,
                tipo="EMERGENCIA",
                prioridad="ALTA",
                url=url_reportante,
            )

    @staticmethod
    def notificar_emergencia_resuelta(emergencia):
        """
        Notifica cuando se resuelve una emergencia.
        Si era de alerta masiva (sismo, deslizamiento), notifica a TODOS los usuarios.
        """
        tipo_nombre = emergencia.tipo.nombre if hasattr(emergencia.tipo, "nombre") else str(emergencia.tipo)
        titulo = f"Alerta finalizada: {tipo_nombre}"
        mensaje = (
            f"La emergencia de {tipo_nombre} ha sido controlada y finalizada.\n"
            f"El personal puede regresar a sus actividades con normalidad."
        )

        # Si era alerta masiva → notificar a todos (igual que al activarla)
        if getattr(emergencia.tipo, "alerta_masiva", False):
            usuarios = Usuario.objects.filter(activo=True).exclude(rol="VISITANTE")
            notificaciones = [
                Notificacion(
                    destinatario=u,
                    titulo=titulo,
                    mensaje=mensaje,
                    tipo="EMERGENCIA",
                    prioridad="MEDIA",
                    url_relacionada="/",
                )
                for u in usuarios
            ]
            if notificaciones:
                Notificacion.objects.bulk_create(notificaciones)

            _ws_dispatch_roles(
                roles=["COORDINADOR_SST", "BRIGADA", "VIGILANCIA", "INSTRUCTOR", "APRENDIZ"],
                tipo="EMERGENCIA",
                titulo=titulo,
                mensaje=mensaje,
                prioridad="NORMAL",
                url="/",
            )
            return len(notificaciones)

        # Emergencia normal → solo administrativos y quien reportó
        titulo = "Emergencia resuelta"
        mensaje = f"La emergencia ha sido resuelta.\nTipo: {tipo_nombre}"
        administradores = list(Usuario.objects.filter(rol="COORDINADOR_SST", activo=True))

        notificaciones = []
        for admin in administradores:
            notificaciones.append(
                Notificacion(
                    destinatario=admin,
                    titulo=titulo,
                    mensaje=mensaje,
                    tipo="EMERGENCIA",
                    prioridad="MEDIA",
                    url_relacionada="/emergencias/",
                )
            )

        # Notificar al reportante con URL según su rol
        if emergencia.reportada_por and emergencia.reportada_por not in administradores:
            url_reportante = "/dashboard/"
            if emergencia.reportada_por.rol in ["BRIGADA", "COORDINADOR_SST", "VIGILANCIA", "INSTRUCTOR"]:
                url_reportante = "/emergencias/"
            notificaciones.append(
                Notificacion(
                    destinatario=emergencia.reportada_por,
                    titulo=titulo,
                    mensaje=mensaje,
                    tipo="EMERGENCIA",
                    prioridad="MEDIA",
                    url_relacionada=url_reportante,
                )
            )

        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)

    @staticmethod
    def notificar_falsa_alarma(emergencia, marcada_por):
        """
        Notifica cuando una emergencia es marcada como falsa alarma.
        Notifica al usuario que reportó y a los administrativos.
        """
        nombre_reportante = emergencia.reportada_por.get_full_name() if emergencia.reportada_por else "Desconocido"
        documento = getattr(emergencia.reportada_por, "numero_documento", "N/A") if emergencia.reportada_por else "N/A"

        # Contar falsas alarmas del usuario
        total_falsas = 0
        if emergencia.reportada_por:
            from emergencias.models import Emergencia as EmergenciaModel

            total_falsas = EmergenciaModel.objects.filter(
                reportada_por=emergencia.reportada_por, estado="FALSA_ALARMA"
            ).count()

        # Notificar al usuario que reportó la falsa alarma
        if emergencia.reportada_por:
            # Usar dashboard como URL para roles sin acceso a emergencias
            url_reportante = "/dashboard/"
            if emergencia.reportada_por.rol in ["BRIGADA", "COORDINADOR_SST", "VIGILANCIA", "INSTRUCTOR"]:
                url_reportante = "/emergencias/"

            Notificacion.crear_notificacion(
                destinatario=emergencia.reportada_por,
                titulo="Emergencia marcada como Falsa Alarma",
                mensaje=(
                    f"Tu reporte de emergencia fue marcado como falsa alarma.\n"
                    f"Motivo: {emergencia.motivo_falsa_alarma}\n"
                    f"Marcada por: {marcada_por.get_full_name()}\n\n"
                    f"Llevas {total_falsas} falsa(s) alarma(s) registrada(s). "
                    f"El uso indebido del sistema de emergencias puede tener consecuencias."
                ),
                tipo="EMERGENCIA",
                prioridad="ALTA",
                url=url_reportante,
            )

        # Notificar a administrativos con datos del responsable
        reincidente_texto = f" (REINCIDENTE: {total_falsas} falsas alarmas)" if total_falsas > 1 else ""
        notificaciones = []
        administradores = Usuario.objects.filter(rol="COORDINADOR_SST", activo=True)

        for admin in administradores:
            notificaciones.append(
                Notificacion(
                    destinatario=admin,
                    titulo=f"Falsa Alarma Identificada{reincidente_texto}",
                    mensaje=(
                        f"Se identifico una falsa alarma.\n"
                        f"Reportada por: {nombre_reportante}\n"
                        f"Documento: {documento}\n"
                        f"Tipo de emergencia: {emergencia.tipo.nombre if hasattr(emergencia.tipo, 'nombre') else emergencia.tipo}\n"
                        f"Motivo: {emergencia.motivo_falsa_alarma}\n"
                        f"Marcada por: {marcada_por.get_full_name()}\n"
                        f"Total falsas alarmas de este usuario: {total_falsas}"
                    ),
                    tipo="EMERGENCIA",
                    prioridad="ALTA",
                    url_relacionada="/emergencias/",
                )
            )

        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)

    # ============================================================
    # NOTIFICACIONES DE INCIDENTES
    # ============================================================

    @staticmethod
    def notificar_incidente_critico(incidente):
        """
        Notifica a Administrativos e Instructores cuando se reporta un incidente crítico.

        Args:
            incidente: Instancia del modelo Incidente
        """
        # Determinar nivel de criticidad
        gravedad = getattr(incidente, "gravedad", "MEDIA")

        if gravedad not in ["ALTA", "CRITICA"]:
            return 0  # Solo notificar incidentes críticos

        titulo = f"Incidente {gravedad}: {incidente.titulo if hasattr(incidente, 'titulo') else 'Reportado'}"
        descripcion_texto = str(incidente.descripcion) if incidente.descripcion else ""
        mensaje = (
            f"Se ha reportado un incidente de gravedad {gravedad}.\n"
            f"Tipo: {incidente.get_tipo_display() if hasattr(incidente, 'get_tipo_display') else incidente.tipo}\n"
            f"Descripción: {descripcion_texto[:100]}{'...' if len(descripcion_texto) > 100 else ''}\n"
            f"Ubicación: {incidente.ubicacion or 'No especificada'}\n"
            f"Reportado por: {incidente.reportado_por.get_full_name() if incidente.reportado_por else 'Anónimo'}"
        )

        url = "/reportes/incidentes/"

        # Notificar a Administrativos e Instructores
        notificaciones = []
        usuarios = Usuario.objects.filter(rol__in=["COORDINADOR_SST", "INSTRUCTOR"], activo=True)

        for usuario in usuarios:
            notificaciones.append(
                Notificacion(
                    destinatario=usuario,
                    titulo=titulo,
                    mensaje=mensaje,
                    tipo="INCIDENTE",
                    prioridad="ALTA",
                    url_relacionada=url,
                )
            )

        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)

        # WebSocket — incidente crítico visible al instante
        _ws_dispatch_roles(
            roles=["COORDINADOR_SST", "INSTRUCTOR"],
            tipo="INCIDENTE",
            titulo=titulo,
            mensaje=mensaje,
            prioridad="ALTA",
            url=url,
        )

        return len(notificaciones)

    @staticmethod
    def notificar_incidente_creado(incidente):
        """
        Notifica cuando se crea cualquier incidente (no solo criticos).
        Notifica a Administrativos siempre. Incluye ubicacion y area.

        Args:
            incidente: Instancia del modelo Incidente
        """
        gravedad = getattr(incidente, "gravedad", "MEDIA")
        prioridad_notif = "ALTA" if gravedad in ["ALTA", "CRITICA"] else "MEDIA"

        titulo = f"Nuevo incidente: {incidente.titulo if hasattr(incidente, 'titulo') else 'Reportado'}"
        descripcion_texto = str(incidente.descripcion) if incidente.descripcion else ""

        # Construir informacion de ubicacion
        ubicacion_info = incidente.ubicacion or "No especificada"
        area_info = ""
        if hasattr(incidente, "get_area_incidente_display") and incidente.area_incidente:
            area_info = f"\nArea: {incidente.get_area_incidente_display()}"
        lugar_info = ""
        if hasattr(incidente, "lugar_exacto") and incidente.lugar_exacto:
            lugar_info = f"\nLugar exacto: {incidente.lugar_exacto}"
        persona_info = ""
        if hasattr(incidente, "persona_afectada") and incidente.persona_afectada:
            persona_info = f"\nPersona afectada: {incidente.persona_afectada}"

        mensaje = (
            f"Se ha reportado un nuevo incidente.\n"
            f"Tipo: {incidente.get_tipo_display() if hasattr(incidente, 'get_tipo_display') else incidente.tipo}\n"
            f"Gravedad: {gravedad}\n"
            f"Ubicacion: {ubicacion_info}{area_info}{lugar_info}{persona_info}\n"
            f"Descripcion: {descripcion_texto[:80]}{'...' if len(descripcion_texto) > 80 else ''}\n"
            f"Reportado por: {incidente.reportado_por.get_full_name() if incidente.reportado_por else 'Anonimo'}"
        )

        url = "/reportes/incidentes/"

        # Brigada siempre recibe la notificacion; Instructores solo en incidentes graves
        if gravedad in ["ALTA", "CRITICA"]:
            roles = ["COORDINADOR_SST", "INSTRUCTOR", "BRIGADA"]
        else:
            roles = ["COORDINADOR_SST", "BRIGADA"]

        notificaciones = []
        usuarios = Usuario.objects.filter(rol__in=roles, activo=True)

        for usuario in usuarios:
            notificaciones.append(
                Notificacion(
                    destinatario=usuario,
                    titulo=titulo,
                    mensaje=mensaje,
                    tipo="INCIDENTE",
                    prioridad=prioridad_notif,
                    url_relacionada=url,
                )
            )

        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)

        # Email y WhatsApp solo para incidentes graves
        if gravedad in ["ALTA", "CRITICA"]:
            lista_usuarios = list(usuarios)
            EmailNotificationService.notificar_incidente(incidente, lista_usuarios)

        return len(notificaciones)

    @staticmethod
    def notificar_alarma_incidente(incidente):
        """
        Genera una alarma/alerta de alta prioridad para Brigada e Instructores
        cuando se reporta un incidente de gravedad ALTA o CRITICA.

        Args:
            incidente: Instancia del modelo Incidente
        """
        gravedad = getattr(incidente, "gravedad", "MEDIA")

        ubicacion_info = incidente.ubicacion or "No especificada"
        area_info = ""
        if hasattr(incidente, "get_area_incidente_display") and incidente.area_incidente:
            area_info = f" - {incidente.get_area_incidente_display()}"

        titulo = f"ALARMA - Incidente {gravedad}: {incidente.titulo}"
        mensaje = (
            f"ATENCION: Se ha reportado un incidente de gravedad {gravedad}.\n"
            f"Tipo: {incidente.get_tipo_display() if hasattr(incidente, 'get_tipo_display') else incidente.tipo}\n"
            f"Ubicacion: {ubicacion_info}{area_info}\n"
            f"Reportado por: {incidente.reportado_por.get_full_name() if incidente.reportado_por else 'Anonimo'}\n"
            f"Se requiere atencion inmediata."
        )

        url = "/reportes/incidentes/"

        notificaciones = []
        usuarios = Usuario.objects.filter(rol__in=["BRIGADA", "INSTRUCTOR"], activo=True)

        for usuario in usuarios:
            notificaciones.append(
                Notificacion(
                    destinatario=usuario,
                    titulo=titulo,
                    mensaje=mensaje,
                    tipo="INCIDENTE",
                    prioridad="ALTA",
                    url_relacionada=url,
                )
            )

        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)

        return len(notificaciones)

    # ============================================================
    # NOTIFICACIONES DE EQUIPOS DE SEGURIDAD
    # ============================================================

    @staticmethod
    def notificar_equipo_requiere_revision(equipo):
        """
        Notifica a la Brigada cuando un equipo requiere revisión.

        Args:
            equipo: Instancia del modelo EquipamientoSeguridad
        """
        titulo = f"Equipo requiere revision: {equipo.nombre}"
        # Obtener nombre del edificio si existe
        ubicacion = equipo.edificio.nombre if equipo.edificio else "No especificada"
        mensaje = (
            f"El equipo '{equipo.nombre}' necesita revision.\n"
            f"Tipo: {equipo.get_tipo_display() if hasattr(equipo, 'get_tipo_display') else equipo.tipo}\n"
            f"Codigo: {equipo.codigo}\n"
            f"Ubicacion: {ubicacion}\n"
            f"Estado actual: {equipo.get_estado_display() if hasattr(equipo, 'get_estado_display') else equipo.estado}"
        )

        # Notificar a Brigada
        Notificacion.notificar_usuarios_por_rol(
            rol="BRIGADA", titulo=titulo, mensaje=mensaje, tipo="RECORDATORIO", prioridad="MEDIA"
        )

    @staticmethod
    def notificar_equipos_proximos_vencer():
        """
        Notifica sobre equipos con fecha de revisión próxima (7 días).
        Debe ejecutarse como tarea programada (cron/celery).
        """
        from django.utils import timezone
        from datetime import timedelta
        from mapas.models import EquipamientoSeguridad

        fecha_limite = timezone.now() + timedelta(days=7)

        equipos = EquipamientoSeguridad.objects.filter(proxima_revision__lte=fecha_limite, activo=True)

        if not equipos.exists():
            return 0

        titulo = f"{equipos.count()} equipo(s) requieren revision esta semana"
        mensaje = "Los siguientes equipos tienen revision programada proximamente:\n"
        mensaje += "\n".join(
            [
                f"- {e.nombre} ({e.codigo}) - {e.proxima_revision.strftime('%d/%m/%Y') if e.proxima_revision else 'Sin fecha'}"
                for e in equipos[:5]
            ]
        )

        if equipos.count() > 5:
            mensaje += f"\n... y {equipos.count() - 5} mas"

        return Notificacion.notificar_usuarios_por_rol(
            rol="BRIGADA", titulo=titulo, mensaje=mensaje, tipo="RECORDATORIO", prioridad="MEDIA"
        )

    @staticmethod
    def notificar_revision_hoy():
        """
        Notifica a la Brigada por cada equipo cuya fecha de revisión llegó hoy o está vencida.
        Evita duplicados: solo envía una notificación por equipo por día.
        Retorna el número de notificaciones creadas.
        """
        from django.utils import timezone
        from mapas.models import EquipamientoSeguridad

        hoy = timezone.now().date()
        brigada_users = list(Usuario.objects.filter(rol="BRIGADA", activo=True))
        if not brigada_users:
            return 0

        equipos_pendientes = EquipamientoSeguridad.objects.filter(
            proxima_revision__date__lte=hoy,
            activo=True,
        ).select_related("edificio")

        if not equipos_pendientes.exists():
            return 0

        # IDs de equipos ya notificados hoy (se usa url_relacionada como clave de deduplicación)
        urls_hoy = set(
            Notificacion.objects.filter(
                fecha_creacion__date=hoy,
                url_relacionada__startswith="/brigada/equipos/?revision=",
            ).values_list("url_relacionada", flat=True)
        )

        nuevas = []
        for equipo in equipos_pendientes:
            url_equipo = f"/brigada/equipos/?revision={equipo.id}"
            if url_equipo in urls_hoy:
                continue  # Ya fue notificado hoy

            ubicacion = equipo.edificio.nombre if equipo.edificio else "Sin ubicacion"
            fecha_str = equipo.proxima_revision.strftime("%d/%m/%Y") if equipo.proxima_revision else "Vencida"
            titulo = f"Revision pendiente: {equipo.get_tipo_display()} {equipo.codigo}"
            mensaje = (
                f"El equipo {equipo.codigo} tiene revision programada para hoy ({fecha_str}).\n"
                f"Tipo: {equipo.get_tipo_display()}\n"
                f"Ubicacion: {ubicacion}\n"
                f"Acceda al modulo de equipos para registrar la verificacion."
            )

            for usuario in brigada_users:
                nuevas.append(
                    Notificacion(
                        destinatario=usuario,
                        titulo=titulo,
                        mensaje=mensaje,
                        tipo="RECORDATORIO",
                        prioridad="ALTA",
                        url_relacionada=url_equipo,
                    )
                )

        if nuevas:
            Notificacion.objects.bulk_create(nuevas)

        return len(nuevas)

    # ============================================================
    # NOTIFICACIONES DE VISITANTES
    # ============================================================

    @staticmethod
    def notificar_visitante_excede_tiempo(visitante, tiempo_limite_horas=4):
        """
        Notifica a Vigilancia cuando un visitante excede el tiempo permitido.

        Args:
            visitante: Instancia del modelo Visitante
            tiempo_limite_horas: Tiempo límite en horas (default: 4)
        """
        from django.utils import timezone
        from datetime import datetime

        # Calcular tiempo en el centro
        entrada = datetime.combine(visitante.fecha_visita, visitante.hora_ingreso)
        entrada = timezone.make_aware(entrada) if timezone.is_naive(entrada) else entrada
        tiempo_transcurrido = timezone.now() - entrada

        if tiempo_transcurrido.total_seconds() < tiempo_limite_horas * 3600:
            return  # No ha excedido el tiempo

        horas = int(tiempo_transcurrido.total_seconds() // 3600)
        minutos = int((tiempo_transcurrido.total_seconds() % 3600) // 60)

        titulo = f"⏰ Visitante excede tiempo: {visitante.nombre_completo}"
        mensaje = (
            f"El visitante lleva más de {tiempo_limite_horas} horas en el centro.\n"
            f"Nombre: {visitante.nombre_completo}\n"
            f"Documento: {visitante.numero_documento}\n"
            f"Tiempo en centro: {horas}h {minutos}m\n"
            f"Visita a: {visitante.persona_a_visitar.get_full_name()}"
        )

        # Notificar a Vigilancia
        Notificacion.notificar_usuarios_por_rol(
            rol="VIGILANCIA", titulo=titulo, mensaje=mensaje, tipo="RECORDATORIO", prioridad="MEDIA"
        )

    @staticmethod
    def verificar_visitantes_exceden_tiempo(tiempo_limite_horas=4):
        """
        Verifica todos los visitantes activos y notifica si exceden el tiempo.
        Debe ejecutarse como tarea programada (cron/celery).
        """
        from django.utils import timezone
        from datetime import datetime, timedelta
        from .models import Visitante

        limite = timezone.now() - timedelta(hours=tiempo_limite_horas)

        visitantes_excedidos = Visitante.objects.filter(
            hora_salida__isnull=True,  # Aún en el centro
            activo=True,
        )

        count = 0
        for visitante in visitantes_excedidos:
            entrada = datetime.combine(visitante.fecha_visita, visitante.hora_ingreso)
            entrada = timezone.make_aware(entrada) if timezone.is_naive(entrada) else entrada

            if entrada < limite:
                NotificacionService.notificar_visitante_excede_tiempo(visitante, tiempo_limite_horas)
                count += 1

        return count

    # ============================================================
    # NOTIFICACIONES DE AFORO
    # ============================================================

    @staticmethod
    def notificar_aforo_critico(aforo_actual, aforo_maximo, porcentaje_alerta=90):
        """
        Notifica a Vigilancia y Administrativos cuando el aforo supera el umbral.

        Args:
            aforo_actual: Número de personas actualmente en el centro
            aforo_maximo: Capacidad máxima del centro
            porcentaje_alerta: Porcentaje a partir del cual se alerta (default: 90%)
        """
        porcentaje_ocupacion = (aforo_actual / aforo_maximo) * 100 if aforo_maximo > 0 else 0

        if porcentaje_ocupacion < porcentaje_alerta:
            return 0  # No ha llegado al umbral

        # Determinar nivel de alerta
        if porcentaje_ocupacion >= 100:
            titulo = "🚫 AFORO MÁXIMO ALCANZADO"
            prioridad = "ALTA"
        elif porcentaje_ocupacion >= 95:
            titulo = "⚠️ Aforo crítico (>95%)"
            prioridad = "ALTA"
        else:
            titulo = f"📊 Alerta de aforo ({int(porcentaje_ocupacion)}%)"
            prioridad = "MEDIA"

        mensaje = (
            f"El centro se encuentra al {porcentaje_ocupacion:.1f}% de su capacidad.\n"
            f"Personas actuales: {aforo_actual}\n"
            f"Capacidad máxima: {aforo_maximo}\n"
            f"Espacios disponibles: {max(0, aforo_maximo - aforo_actual)}"
        )

        # Notificar a Vigilancia y Administrativos
        notificaciones = []
        usuarios = Usuario.objects.filter(rol__in=["VIGILANCIA", "COORDINADOR_SST"], activo=True)

        for usuario in usuarios:
            notificaciones.append(
                Notificacion(
                    destinatario=usuario,
                    titulo=titulo,
                    mensaje=mensaje,
                    tipo="SISTEMA",
                    prioridad=prioridad,
                    url_relacionada="/acceso/",
                )
            )

        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)

        # WebSocket — alerta de aforo al instante en la pantalla de vigilancia
        _ws_dispatch_roles(
            roles=["VIGILANCIA", "COORDINADOR_SST"],
            tipo="SISTEMA",
            titulo=titulo,
            mensaje=mensaje,
            prioridad=prioridad,
            url="/acceso/",
        )

        return len(notificaciones)

    # ============================================================
    # NOTIFICACIONES DE ASISTENCIA (para Instructores)
    # ============================================================

    @staticmethod
    def notificar_aprendiz_sin_acceso(aprendiz, instructor):
        """
        Notifica a un instructor cuando un aprendiz no ha registrado acceso.

        Args:
            aprendiz: Usuario con rol APRENDIZ
            instructor: Usuario con rol INSTRUCTOR
        """
        titulo = f"📋 Aprendiz sin registro de acceso: {aprendiz.get_full_name()}"
        mensaje = (
            f"El aprendiz {aprendiz.get_full_name()} no ha registrado acceso hoy.\n"
            f"Ficha: {aprendiz.ficha or 'No asignada'}\n"
            f"Documento: {aprendiz.numero_documento}"
        )

        Notificacion.crear_notificacion(
            destinatario=instructor, titulo=titulo, mensaje=mensaje, tipo="ASISTENCIA", prioridad="BAJA"
        )

    # ============================================================
    # NOTIFICACIONES GENERALES / DE SISTEMA
    # ============================================================

    @staticmethod
    def notificar_sistema(destinatarios, titulo, mensaje, prioridad="MEDIA"):
        """
        Envía una notificación de sistema a múltiples destinatarios.

        Args:
            destinatarios: Lista de usuarios o roles (strings)
            titulo: Título de la notificación
            mensaje: Mensaje de la notificación
            prioridad: 'ALTA', 'MEDIA' o 'BAJA'
        """
        notificaciones = []

        # Si destinatarios es una lista de strings (roles), obtener usuarios
        if destinatarios and isinstance(destinatarios[0], str):
            usuarios = Usuario.objects.filter(rol__in=destinatarios, activo=True)
        else:
            usuarios = destinatarios

        for usuario in usuarios:
            notificaciones.append(
                Notificacion(destinatario=usuario, titulo=titulo, mensaje=mensaje, tipo="SISTEMA", prioridad=prioridad)
            )

        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)

        return len(notificaciones)

    @staticmethod
    def notificar_capacitacion(destinatarios, titulo_capacitacion, fecha, ubicacion):
        """
        Notifica sobre una capacitación programada.

        Args:
            destinatarios: Lista de usuarios
            titulo_capacitacion: Nombre de la capacitación
            fecha: Fecha de la capacitación
            ubicacion: Lugar de la capacitación
        """
        titulo = f"📚 Capacitación: {titulo_capacitacion}"
        mensaje = (
            f"Se ha programado una capacitación.\nTema: {titulo_capacitacion}\nFecha: {fecha}\nUbicación: {ubicacion}"
        )

        notificaciones = []
        for usuario in destinatarios:
            notificaciones.append(
                Notificacion(
                    destinatario=usuario, titulo=titulo, mensaje=mensaje, tipo="CAPACITACION", prioridad="MEDIA"
                )
            )

        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)

        return len(notificaciones)


# ============================================================
# FUNCIONES DE CONVENIENCIA (para usar sin instanciar la clase)
# ============================================================


def notificar_emergencia(emergencia):
    """Atajo para notificar nueva emergencia"""
    return NotificacionService.notificar_emergencia_creada(emergencia)


def notificar_incidente(incidente):
    """Atajo para notificar incidente crítico"""
    return NotificacionService.notificar_incidente_critico(incidente)


def notificar_aforo(aforo_actual, aforo_maximo, umbral=90):
    """Atajo para notificar aforo crítico"""
    return NotificacionService.notificar_aforo_critico(aforo_actual, aforo_maximo, umbral)


def verificar_visitantes():
    """Atajo para verificar visitantes que exceden tiempo"""
    return NotificacionService.verificar_visitantes_exceden_tiempo()


def verificar_equipos():
    """Atajo para verificar equipos próximos a vencer"""
    return NotificacionService.notificar_equipos_proximos_vencer()


# ============================================================
# SERVICIO DE EMAIL
# ============================================================


class EmailNotificationService:
    """Envía notificaciones por correo electrónico usando Django email."""

    SITE_URL = getattr(settings, "SITE_URL", "http://localhost:8000")

    @staticmethod
    def _enviar_lote_sync(destinatarios, asunto, template, contexto):
        """Envía emails a una lista de usuarios en una sola conexión SMTP."""
        from django.core.mail import get_connection

        ctx = {**contexto, "site_url": EmailNotificationService.SITE_URL}
        try:
            html = render_to_string(template, ctx)
        except Exception as e:
            logger.error("Error renderizando template %s: %s", template, e)
            return

        mensajes = []
        for usuario in destinatarios:
            if not usuario.email:
                continue
            if not getattr(usuario, "recibir_notif_email", True):
                continue
            msg = EmailMessage(
                subject=asunto,
                body=html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[usuario.email],
                reply_to=[settings.DEFAULT_FROM_EMAIL],
            )
            msg.content_subtype = "html"
            mensajes.append(msg)

        if not mensajes:
            return

        try:
            connection = get_connection()
            connection.send_messages(mensajes)
            logger.info("Emails enviados: %d/%d destinatarios", len(mensajes), len(destinatarios))
        except Exception as e:
            logger.error("Error enviando lote de emails: %s", e)
            print(f"[EMAIL ERROR] Lote de {len(mensajes)} emails: {e}")

    @staticmethod
    def _enviar_lote(destinatarios, asunto, template, contexto):
        """Envía emails a múltiples usuarios en un único hilo de fondo (una sola conexión SMTP)."""
        import threading

        t = threading.Thread(
            target=EmailNotificationService._enviar_lote_sync,
            args=(destinatarios, asunto, template, contexto),
            daemon=True,
        )
        t.start()

    @staticmethod
    def _enviar_sync(usuario, asunto, template, contexto):
        """Envía un email a un único usuario (reutiliza _enviar_lote_sync)."""
        EmailNotificationService._enviar_lote_sync([usuario], asunto, template, contexto)

    @staticmethod
    def _enviar(usuario, asunto, template, contexto):
        """Envía un email HTML en un hilo de fondo para no bloquear el request."""
        if not usuario.email:
            return
        if not getattr(usuario, "recibir_notif_email", True):
            return
        EmailNotificationService._enviar_lote([usuario], asunto, template, contexto)

    @staticmethod
    def notificar_emergencia(emergencia, destinatarios):
        """Envía alerta de emergencia por email a la lista de usuarios."""
        tipo_nombre = emergencia.tipo.nombre if hasattr(emergencia.tipo, "nombre") else str(emergencia.tipo)
        asunto = f"[EMERGENCIA] {tipo_nombre} – Centro Minero SENA"
        contexto = {
            "titulo": f"EMERGENCIA: {tipo_nombre}",
            "tipo_emergencia": tipo_nombre,
            "descripcion": emergencia.descripcion or "Sin descripción",
            "ubicacion": getattr(emergencia, "descripcion_ubicacion", None) or "No especificada",
            "reportado_por": emergencia.reportada_por.get_full_name() if emergencia.reportada_por else "Anónimo",
            "fecha_hora": timezone.localtime(emergencia.fecha_hora).strftime("%d/%m/%Y %I:%M %p")
            if hasattr(emergencia, "fecha_hora")
            else "—",
            "estado": getattr(emergencia, "estado", "ACTIVA"),
        }
        EmailNotificationService._enviar_lote(destinatarios, asunto, "emails/emergencia_alerta.html", contexto)

    @staticmethod
    def notificar_incidente(incidente, destinatarios):
        """Envía alerta de incidente crítico por email."""
        gravedad = getattr(incidente, "gravedad", "ALTA")
        titulo_inc = getattr(incidente, "titulo", "Incidente reportado")
        asunto = f"[INCIDENTE {gravedad}] {titulo_inc} – Centro Minero SENA"
        descripcion_texto = str(incidente.descripcion) if incidente.descripcion else ""
        area = ""
        if hasattr(incidente, "get_area_incidente_display") and incidente.area_incidente:
            area = incidente.get_area_incidente_display()
        contexto = {
            "titulo": f"Incidente {gravedad}: {titulo_inc}",
            "titulo_incidente": titulo_inc,
            "tipo": incidente.get_tipo_display() if hasattr(incidente, "get_tipo_display") else str(incidente.tipo),
            "gravedad": gravedad,
            "descripcion": descripcion_texto[:200] or "Sin descripción",
            "ubicacion": incidente.ubicacion or "No especificada",
            "area": area or "No especificada",
            "reportado_por": incidente.reportado_por.get_full_name() if incidente.reportado_por else "Anónimo",
            "fecha_hora": timezone.localtime(incidente.fecha_reporte).strftime("%d/%m/%Y %I:%M %p")
            if hasattr(incidente, "fecha_reporte")
            else "—",
        }
        EmailNotificationService._enviar_lote(destinatarios, asunto, "emails/incidente_alerta.html", contexto)

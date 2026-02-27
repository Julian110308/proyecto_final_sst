# usuarios/services.py
"""
Servicio centralizado de notificaciones para el sistema SST.
Este módulo contiene funciones para enviar notificaciones automáticas
cuando ocurren eventos importantes en el sistema.
"""
import json
import logging
from django.db import transaction
from django.conf import settings
from .models import Notificacion, Usuario, PushSubscripcion

logger = logging.getLogger(__name__)


class WebPushService:
    """
    Servicio para enviar notificaciones Web Push a dispositivos móviles.
    Utiliza VAPID para autenticación con los servidores push.
    """

    @staticmethod
    def enviar_a_usuario(usuario, titulo, cuerpo, url='/emergencias/', icono='/static/icons/icon-192.png'):
        """
        Envía una notificación push a todas las suscripciones activas de un usuario.
        Si falla una suscripción caducada, la desactiva automáticamente.
        """
        if not settings.VAPID_PUBLIC_KEY or not settings.VAPID_PRIVATE_KEY:
            return

        try:
            from pywebpush import webpush, WebPushException
        except ImportError:
            logger.warning('pywebpush no instalado. Notificaciones push desactivadas.')
            return

        subscripciones = PushSubscripcion.objects.filter(usuario=usuario, activo=True)
        payload = json.dumps({
            'title': titulo,
            'body': cuerpo,
            'icon': icono,
            'url': url,
            'badge': '/static/icons/icon-192.png',
        })
        vapid_claims = {'sub': f'mailto:{settings.VAPID_ADMIN_EMAIL}'}

        for sub in subscripciones:
            try:
                webpush(
                    subscription_info={
                        'endpoint': sub.endpoint,
                        'keys': {'p256dh': sub.p256dh, 'auth': sub.auth},
                    },
                    data=payload,
                    vapid_private_key=settings.VAPID_PRIVATE_KEY,
                    vapid_claims=vapid_claims,
                )
            except Exception as e:
                logger.warning(f'Push fallido para {usuario.username}: {e}')
                # Suscripción caducada o inválida → desactivar
                sub.activo = False
                sub.save(update_fields=['activo'])

    @staticmethod
    def enviar_a_roles(roles, titulo, cuerpo, url='/emergencias/', icono='/static/icons/icon-192.png'):
        """Envía notificación push a todos los usuarios activos de los roles indicados."""
        usuarios = Usuario.objects.filter(rol__in=roles, activo=True)
        for usuario in usuarios:
            WebPushService.enviar_a_usuario(usuario, titulo, cuerpo, url, icono)


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

        url = f"/emergencias/"

        # Notificar a Brigada, Administrativos y Vigilancia
        notificaciones = []
        usuarios = Usuario.objects.filter(
            rol__in=['BRIGADA', 'ADMINISTRATIVO', 'VIGILANCIA'],
            activo=True
        )

        for usuario in usuarios:
            notificaciones.append(Notificacion(
                destinatario=usuario,
                titulo=titulo,
                mensaje=mensaje,
                tipo='EMERGENCIA',
                prioridad='ALTA',
                url_relacionada=url
            ))

        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)

        # Enviar también Web Push a los dispositivos móviles
        tipo_nombre = emergencia.tipo.nombre if emergencia.tipo else 'Emergencia'
        WebPushService.enviar_a_roles(
            roles=['BRIGADA', 'ADMINISTRATIVO', 'VIGILANCIA'],
            titulo=f'EMERGENCIA: {tipo_nombre}',
            cuerpo=f'{emergencia.descripcion[:80]} — Reportado por {emergencia.reportada_por.get_full_name() if emergencia.reportada_por else "Anonimo"}',
            url='/emergencias/',
        )

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
            url_reportante = '/dashboard/'
            if emergencia.reportada_por.rol in ['BRIGADA', 'ADMINISTRATIVO', 'VIGILANCIA', 'INSTRUCTOR']:
                url_reportante = '/emergencias/'

            Notificacion.crear_notificacion(
                destinatario=emergencia.reportada_por,
                titulo=titulo,
                mensaje=mensaje,
                tipo='EMERGENCIA',
                prioridad='ALTA',
                url=url_reportante
            )

    @staticmethod
    def notificar_emergencia_resuelta(emergencia):
        """
        Notifica cuando se resuelve una emergencia.

        Args:
            emergencia: Instancia del modelo Emergencia
        """
        titulo = "✅ Emergencia resuelta"
        mensaje = (
            f"La emergencia ha sido resuelta.\n"
            f"Tipo: {emergencia.tipo.nombre if hasattr(emergencia.tipo, 'nombre') else emergencia.tipo}"
        )

        # Notificar a administrativos
        administradores = list(Usuario.objects.filter(
            rol='ADMINISTRATIVO',
            activo=True
        ))

        notificaciones = []
        for admin in administradores:
            notificaciones.append(Notificacion(
                destinatario=admin,
                titulo=titulo,
                mensaje=mensaje,
                tipo='EMERGENCIA',
                prioridad='MEDIA',
                url_relacionada='/emergencias/'
            ))

        # Notificar al reportante con URL según su rol
        if emergencia.reportada_por and emergencia.reportada_por not in administradores:
            url_reportante = '/dashboard/'
            if emergencia.reportada_por.rol in ['BRIGADA', 'ADMINISTRATIVO', 'VIGILANCIA', 'INSTRUCTOR']:
                url_reportante = '/emergencias/'
            notificaciones.append(Notificacion(
                destinatario=emergencia.reportada_por,
                titulo=titulo,
                mensaje=mensaje,
                tipo='EMERGENCIA',
                prioridad='MEDIA',
                url_relacionada=url_reportante
            ))

        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)

    @staticmethod
    def notificar_falsa_alarma(emergencia, marcada_por):
        """
        Notifica cuando una emergencia es marcada como falsa alarma.
        Notifica al usuario que reportó y a los administrativos.
        """
        nombre_reportante = emergencia.reportada_por.get_full_name() if emergencia.reportada_por else 'Desconocido'
        documento = getattr(emergencia.reportada_por, 'numero_documento', 'N/A') if emergencia.reportada_por else 'N/A'

        # Contar falsas alarmas del usuario
        total_falsas = 0
        if emergencia.reportada_por:
            from emergencias.models import Emergencia as EmergenciaModel
            total_falsas = EmergenciaModel.objects.filter(
                reportada_por=emergencia.reportada_por,
                estado='FALSA_ALARMA'
            ).count()

        # Notificar al usuario que reportó la falsa alarma
        if emergencia.reportada_por:
            # Usar dashboard como URL para roles sin acceso a emergencias
            url_reportante = '/dashboard/'
            if emergencia.reportada_por.rol in ['BRIGADA', 'ADMINISTRATIVO', 'VIGILANCIA', 'INSTRUCTOR']:
                url_reportante = '/emergencias/'

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
                tipo='EMERGENCIA',
                prioridad='ALTA',
                url=url_reportante
            )

        # Notificar a administrativos con datos del responsable
        reincidente_texto = f" (REINCIDENTE: {total_falsas} falsas alarmas)" if total_falsas > 1 else ""
        notificaciones = []
        administradores = Usuario.objects.filter(rol='ADMINISTRATIVO', activo=True)

        for admin in administradores:
            notificaciones.append(Notificacion(
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
                tipo='EMERGENCIA',
                prioridad='ALTA',
                url_relacionada='/emergencias/'
            ))

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
        gravedad = getattr(incidente, 'gravedad', 'MEDIA')

        if gravedad not in ['ALTA', 'CRITICA']:
            return 0  # Solo notificar incidentes críticos

        titulo = f"Incidente {gravedad}: {incidente.titulo if hasattr(incidente, 'titulo') else 'Reportado'}"
        descripcion_texto = str(incidente.descripcion) if incidente.descripcion else ''
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
        usuarios = Usuario.objects.filter(
            rol__in=['ADMINISTRATIVO', 'INSTRUCTOR'],
            activo=True
        )

        for usuario in usuarios:
            notificaciones.append(Notificacion(
                destinatario=usuario,
                titulo=titulo,
                mensaje=mensaje,
                tipo='INCIDENTE',
                prioridad='ALTA',
                url_relacionada=url
            ))

        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)

        return len(notificaciones)

    @staticmethod
    def notificar_incidente_creado(incidente):
        """
        Notifica cuando se crea cualquier incidente (no solo criticos).
        Notifica a Administrativos siempre. Incluye ubicacion y area.

        Args:
            incidente: Instancia del modelo Incidente
        """
        gravedad = getattr(incidente, 'gravedad', 'MEDIA')
        prioridad_notif = 'ALTA' if gravedad in ['ALTA', 'CRITICA'] else 'MEDIA'

        titulo = f"Nuevo incidente: {incidente.titulo if hasattr(incidente, 'titulo') else 'Reportado'}"
        descripcion_texto = str(incidente.descripcion) if incidente.descripcion else ''

        # Construir informacion de ubicacion
        ubicacion_info = incidente.ubicacion or 'No especificada'
        area_info = ''
        if hasattr(incidente, 'get_area_incidente_display') and incidente.area_incidente:
            area_info = f"\nArea: {incidente.get_area_incidente_display()}"
        lugar_info = ''
        if hasattr(incidente, 'lugar_exacto') and incidente.lugar_exacto:
            lugar_info = f"\nLugar exacto: {incidente.lugar_exacto}"
        persona_info = ''
        if hasattr(incidente, 'persona_afectada') and incidente.persona_afectada:
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

        # Si es critico o alto, notificar a Admin e Instructores
        if gravedad in ['ALTA', 'CRITICA']:
            roles = ['ADMINISTRATIVO', 'INSTRUCTOR']
        else:
            roles = ['ADMINISTRATIVO']

        notificaciones = []
        usuarios = Usuario.objects.filter(rol__in=roles, activo=True)

        for usuario in usuarios:
            notificaciones.append(Notificacion(
                destinatario=usuario,
                titulo=titulo,
                mensaje=mensaje,
                tipo='INCIDENTE',
                prioridad=prioridad_notif,
                url_relacionada=url
            ))

        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)

        return len(notificaciones)

    @staticmethod
    def notificar_alarma_incidente(incidente):
        """
        Genera una alarma/alerta de alta prioridad para Brigada e Instructores
        cuando se reporta un incidente de gravedad ALTA o CRITICA.

        Args:
            incidente: Instancia del modelo Incidente
        """
        gravedad = getattr(incidente, 'gravedad', 'MEDIA')

        ubicacion_info = incidente.ubicacion or 'No especificada'
        area_info = ''
        if hasattr(incidente, 'get_area_incidente_display') and incidente.area_incidente:
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
        usuarios = Usuario.objects.filter(
            rol__in=['BRIGADA', 'INSTRUCTOR'],
            activo=True
        )

        for usuario in usuarios:
            notificaciones.append(Notificacion(
                destinatario=usuario,
                titulo=titulo,
                mensaje=mensaje,
                tipo='INCIDENTE',
                prioridad='ALTA',
                url_relacionada=url
            ))

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
        ubicacion = equipo.edificio.nombre if equipo.edificio else 'No especificada'
        mensaje = (
            f"El equipo '{equipo.nombre}' necesita revision.\n"
            f"Tipo: {equipo.get_tipo_display() if hasattr(equipo, 'get_tipo_display') else equipo.tipo}\n"
            f"Codigo: {equipo.codigo}\n"
            f"Ubicacion: {ubicacion}\n"
            f"Estado actual: {equipo.get_estado_display() if hasattr(equipo, 'get_estado_display') else equipo.estado}"
        )

        url = "/dashboard/brigada/equipos/"

        # Notificar a Brigada
        Notificacion.notificar_usuarios_por_rol(
            rol='BRIGADA',
            titulo=titulo,
            mensaje=mensaje,
            tipo='RECORDATORIO',
            prioridad='MEDIA'
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

        equipos = EquipamientoSeguridad.objects.filter(
            proxima_revision__lte=fecha_limite,
            activo=True
        )

        if not equipos.exists():
            return 0

        titulo = f"{equipos.count()} equipo(s) requieren revision esta semana"
        mensaje = "Los siguientes equipos tienen revision programada proximamente:\n"
        mensaje += "\n".join([f"- {e.nombre} ({e.codigo}) - {e.proxima_revision.strftime('%d/%m/%Y') if e.proxima_revision else 'Sin fecha'}" for e in equipos[:5]])

        if equipos.count() > 5:
            mensaje += f"\n... y {equipos.count() - 5} mas"

        return Notificacion.notificar_usuarios_por_rol(
            rol='BRIGADA',
            titulo=titulo,
            mensaje=mensaje,
            tipo='RECORDATORIO',
            prioridad='MEDIA'
        )

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
        from datetime import datetime, timedelta

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
            rol='VIGILANCIA',
            titulo=titulo,
            mensaje=mensaje,
            tipo='RECORDATORIO',
            prioridad='MEDIA'
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
            activo=True
        )

        count = 0
        for visitante in visitantes_excedidos:
            entrada = datetime.combine(visitante.fecha_visita, visitante.hora_ingreso)
            entrada = timezone.make_aware(entrada) if timezone.is_naive(entrada) else entrada

            if entrada < limite:
                NotificacionService.notificar_visitante_excede_tiempo(
                    visitante,
                    tiempo_limite_horas
                )
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
            prioridad = 'ALTA'
        elif porcentaje_ocupacion >= 95:
            titulo = "⚠️ Aforo crítico (>95%)"
            prioridad = 'ALTA'
        else:
            titulo = f"📊 Alerta de aforo ({int(porcentaje_ocupacion)}%)"
            prioridad = 'MEDIA'

        mensaje = (
            f"El centro se encuentra al {porcentaje_ocupacion:.1f}% de su capacidad.\n"
            f"Personas actuales: {aforo_actual}\n"
            f"Capacidad máxima: {aforo_maximo}\n"
            f"Espacios disponibles: {max(0, aforo_maximo - aforo_actual)}"
        )

        # Notificar a Vigilancia y Administrativos
        notificaciones = []
        usuarios = Usuario.objects.filter(
            rol__in=['VIGILANCIA', 'ADMINISTRATIVO'],
            activo=True
        )

        for usuario in usuarios:
            notificaciones.append(Notificacion(
                destinatario=usuario,
                titulo=titulo,
                mensaje=mensaje,
                tipo='SISTEMA',
                prioridad=prioridad,
                url_relacionada='/acceso/'
            ))

        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)

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
            destinatario=instructor,
            titulo=titulo,
            mensaje=mensaje,
            tipo='ASISTENCIA',
            prioridad='BAJA'
        )

    # ============================================================
    # NOTIFICACIONES GENERALES / DE SISTEMA
    # ============================================================

    @staticmethod
    def notificar_sistema(destinatarios, titulo, mensaje, prioridad='MEDIA'):
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
            usuarios = Usuario.objects.filter(
                rol__in=destinatarios,
                activo=True
            )
        else:
            usuarios = destinatarios

        for usuario in usuarios:
            notificaciones.append(Notificacion(
                destinatario=usuario,
                titulo=titulo,
                mensaje=mensaje,
                tipo='SISTEMA',
                prioridad=prioridad
            ))

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
            f"Se ha programado una capacitación.\n"
            f"Tema: {titulo_capacitacion}\n"
            f"Fecha: {fecha}\n"
            f"Ubicación: {ubicacion}"
        )

        notificaciones = []
        for usuario in destinatarios:
            notificaciones.append(Notificacion(
                destinatario=usuario,
                titulo=titulo,
                mensaje=mensaje,
                tipo='CAPACITACION',
                prioridad='MEDIA'
            ))

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

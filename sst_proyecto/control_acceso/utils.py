# control_acceso/utils.py
import hmac
import hashlib

from django.core.cache import cache
from django.conf import settings
from django.utils import timezone


# ─── QR Token ────────────────────────────────────────────────────────────────


def _firma_qr(user_id: int, fecha_str: str) -> str:
    """HMAC-SHA256 truncado a 16 hex chars."""
    clave = settings.SECRET_KEY.encode()
    mensaje = f"{user_id}:{fecha_str}".encode()
    return hmac.new(clave, mensaje, hashlib.sha256).hexdigest()[:16]


def generar_token_qr(user_id: int) -> str:
    """Devuelve un token válido solo para el día de hoy."""
    fecha = timezone.now().date().strftime("%Y%m%d")
    firma = _firma_qr(user_id, fecha)
    return f"SST-{user_id}-{fecha}-{firma}"


def validar_token_qr(token: str):
    """
    Valida el token QR.
    Retorna (user_id: int, None) si es válido, o (None, mensaje_error) si no.
    """
    try:
        partes = token.strip().split("-")
        if len(partes) != 4 or partes[0] != "SST":
            return None, "Formato de QR inválido."
        _, user_id_str, fecha, firma_recibida = partes
        user_id = int(user_id_str)
    except (ValueError, AttributeError):
        return None, "QR malformado."

    hoy = timezone.now().date().strftime("%Y%m%d")
    if fecha != hoy:
        return None, "QR expirado. El usuario debe regenerarlo."

    firma_esperada = _firma_qr(user_id, fecha)
    if not hmac.compare_digest(firma_recibida, firma_esperada):
        return None, "QR inválido o falsificado."

    return user_id, None


def verificar_aforo_actual():
    """
    Verifica el aforo actual del centro.
    Resultado cacheado 30 segundos para evitar queries en cada petición AJAX.
    """
    from .models import ConfiguracionAforo, RegistroAcceso
    from django.utils import timezone

    cached = cache.get("aforo_actual")
    if cached is not None:
        return cached

    hoy = timezone.now().date()

    # Contar personas actualmente en el centro (solo registros de hoy)
    personas_dentro = RegistroAcceso.objects.filter(
        fecha_hora_egreso__isnull=True, fecha_hora_ingreso__date=hoy
    ).count()

    # Obtener configuración de aforo
    config_aforo = ConfiguracionAforo.objects.filter(activo=True).first()

    if config_aforo:
        aforo_maximo = config_aforo.aforo_maximo
        aforo_minimo = config_aforo.aforo_minimo
        porcentaje = (personas_dentro / aforo_maximo) * 100

        # Determinar nivel de alerta
        if personas_dentro >= aforo_maximo:
            alerta = "CRITICO"
        elif personas_dentro >= aforo_minimo:
            alerta = "ADVERTENCIA"
        else:
            alerta = "NORMAL"

        resultado = {
            "personas_dentro": personas_dentro,
            "aforo_maximo": aforo_maximo,
            "aforo_minimo": aforo_minimo,
            "porcentaje": round(porcentaje, 2),
            "alerta": alerta,
            "mensaje": config_aforo.mensaje_alerta if alerta != "NORMAL" else "",
        }
    else:
        resultado = {
            "personas_dentro": personas_dentro,
            "aforo_maximo": 2000,
            "aforo_minimo": 1800,
            "porcentaje": 0,
            "alerta": "NORMAL",
            "mensaje": "",
        }

    ttl = getattr(settings, "CACHE_TTL_AFORO", 30)
    cache.set("aforo_actual", resultado, ttl)
    return resultado


def obtener_estadisticas_hoy():
    """
    Obtiene estadísticas de acceso del día actual.
    Resultado cacheado 5 minutos para aliviar el dashboard en hora pico.
    """
    from .models import RegistroAcceso
    from usuarios.models import Visitante
    from django.utils import timezone
    from datetime import datetime, time

    cached = cache.get("estadisticas_hoy")
    if cached is not None:
        return cached

    hoy = timezone.now().date()
    inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
    fin_dia = timezone.make_aware(datetime.combine(hoy, time.max))

    ingresos_hoy = RegistroAcceso.objects.filter(fecha_hora_ingreso__range=(inicio_dia, fin_dia)).count()
    personas_dentro = RegistroAcceso.objects.filter(
        fecha_hora_egreso__isnull=True, fecha_hora_ingreso__date=hoy
    ).count()
    visitantes_activos = Visitante.objects.filter(fecha_visita=hoy, hora_salida__isnull=True, activo=True).count()
    aforo_info = verificar_aforo_actual()

    resultado = {
        "ingresos_hoy": ingresos_hoy,
        "personas_dentro": personas_dentro,
        "visitantes_activos": visitantes_activos,
        "aforo": aforo_info,
    }

    ttl = getattr(settings, "CACHE_TTL_ESTADISTICAS", 300)
    cache.set("estadisticas_hoy", resultado, ttl)
    return resultado


def invalidar_cache_acceso():
    """Limpia las claves de caché relacionadas con acceso. Llamar tras registrar ingreso/egreso."""
    cache.delete_many(["aforo_actual", "estadisticas_hoy"])

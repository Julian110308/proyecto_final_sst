from django.utils import timezone
from datetime import timedelta


PENALIZACION_HORAS = 24


def usuario_en_penalizacion(user):
    """
    Retorna (bloqueado: bool, tipo: str, hasta: datetime | None)
    tipo puede ser 'emergencia' o 'incidente'
    """
    desde = timezone.now() - timedelta(hours=PENALIZACION_HORAS)

    # Importaciones locales para evitar importación circular
    from .models import Emergencia
    from reportes.models import Incidente

    emg = (
        Emergencia.objects.filter(
            reportada_por=user,
            estado="FALSA_ALARMA",
            fecha_hora_falsa_alarma__gte=desde,
        )
        .order_by("-fecha_hora_falsa_alarma")
        .first()
    )
    if emg:
        hasta = emg.fecha_hora_falsa_alarma + timedelta(hours=PENALIZACION_HORAS)
        return True, "emergencia", hasta

    inc = (
        Incidente.objects.filter(
            reportado_por=user,
            es_falsa_alarma=True,
            fecha_falsa_alarma__gte=desde,
        )
        .order_by("-fecha_falsa_alarma")
        .first()
    )
    if inc:
        hasta = inc.fecha_falsa_alarma + timedelta(hours=PENALIZACION_HORAS)
        return True, "incidente", hasta

    return False, None, None

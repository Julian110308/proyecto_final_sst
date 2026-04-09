from .models import Emergencia


def emergencia_masiva_activa(request):
    """
    Indica si hay una emergencia masiva activa en este momento.
    Disponible en todos los templates como {{ hay_emergencia_masiva }}.
    """
    if not request.user.is_authenticated:
        return {"hay_emergencia_masiva": False}

    activa = Emergencia.objects.filter(
        tipo__alerta_masiva=True,
        estado__in=["REPORTADA", "EN_ATENCION"],
    ).exists()

    return {"hay_emergencia_masiva": activa}

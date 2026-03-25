"""
Handler de excepciones DRF personalizado.
Garantiza que todas las respuestas de error de la API tengan la misma estructura:
  { "error": "<tipo>", "detail": "<mensaje>", "status": <código> }
"""

import logging

from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def sst_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return None

    view = context.get("view")

    logger.warning(
        "API error %s en %s: %s",
        response.status_code,
        getattr(view, "__class__", "?"),
        exc,
    )

    # Estandarizar la estructura del cuerpo
    original = response.data

    # DRF ya puede devolver {"detail": ...} o {"field": [...]}
    if isinstance(original, dict) and "detail" in original:
        detail = str(original["detail"])
    elif isinstance(original, list):
        detail = "; ".join(str(item) for item in original)
    else:
        # Errores de validación por campo: {"campo": ["error"]}
        parts = []
        for field, errors in original.items():
            if isinstance(errors, list):
                parts.append(f"{field}: {', '.join(str(e) for e in errors)}")
            else:
                parts.append(f"{field}: {errors}")
        detail = "; ".join(parts) if parts else str(original)

    ERROR_LABELS = {
        400: "Solicitud inválida",
        401: "No autenticado",
        403: "Sin permiso",
        404: "No encontrado",
        405: "Método no permitido",
        429: "Demasiadas solicitudes",
        500: "Error interno",
    }

    response.data = {
        "error": ERROR_LABELS.get(response.status_code, "Error"),
        "detail": detail,
        "status": response.status_code,
    }

    return response

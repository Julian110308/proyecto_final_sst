"""
Manejadores de error HTTP personalizados para el proyecto SST.
Devuelven JSON para peticiones de API y HTML para peticiones de navegador.
"""

from django.http import JsonResponse
from django.shortcuts import render


def _is_api_request(request):
    """Determina si la petición viene de un cliente API (fetch/axios) o del navegador."""
    return (
        request.path.startswith("/api/")
        or request.headers.get("Accept", "").startswith("application/json")
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )


def error_404(request, exception=None):
    """Recurso no encontrado."""
    if _is_api_request(request):
        return JsonResponse(
            {"error": "No encontrado", "detail": "El recurso solicitado no existe.", "status": 404},
            status=404,
        )
    return render(request, "errors/404.html", status=404)


def error_500(request):
    """Error interno del servidor."""
    if _is_api_request(request):
        return JsonResponse(
            {"error": "Error interno", "detail": "Ocurrió un error en el servidor. Intente de nuevo.", "status": 500},
            status=500,
        )
    return render(request, "errors/500.html", status=500)

"""
Permisos personalizados basados en roles
Sistema SST - Centro Minero SENA
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from rest_framework.permissions import BasePermission


# ====================================================================
# DECORADORES PARA VISTAS DE DJANGO (HTML)
# ====================================================================


def rol_requerido(*roles_permitidos):
    """
    Decorador para proteger vistas según el rol del usuario

    Uso:
        @rol_requerido('ADMINISTRATIVO', 'INSTRUCTOR')
        def mi_vista(request):
            ...
    """

    def decorador(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Verificar que el usuario esté autenticado
            if not request.user.is_authenticated:
                messages.warning(request, "Debes iniciar sesión para acceder.")
                return redirect("login")

            # Verificar que el usuario tenga uno de los roles permitidos
            if request.user.rol not in roles_permitidos:
                messages.error(
                    request,
                    f"No tienes permiso para acceder a esta sección. Se requiere rol: {', '.join(roles_permitidos)}",
                )
                return redirect("dashboard")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorador


def excluir_visitantes(view_func):
    """
    Decorador para bloquear acceso a visitantes
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Debes iniciar sesión para acceder.")
            return redirect("login")

        if request.user.rol == "VISITANTE":
            messages.error(request, "Los visitantes no tienen acceso a esta sección.")
            return redirect("dashboard")

        return view_func(request, *args, **kwargs)

    return wrapper


# ====================================================================
# CLASES DE PERMISOS PARA REST FRAMEWORK (API)
# ====================================================================


class EsCoordinador(BasePermission):
    """
    Permiso: Solo el Coordinador SST (administrador del sistema)
    """

    message = "Solo el Coordinador SST puede realizar esta acción."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.rol == "COORDINADOR_SST"


class EsAdministrativo(BasePermission):
    """
    Permiso: Solo usuarios con rol ADMINISTRATIVO
    """

    message = "Solo el personal administrativo puede realizar esta acción."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.rol == "ADMINISTRATIVO"


class EsAdministrativoOInstructor(BasePermission):
    """
    Permiso: Usuarios ADMINISTRATIVO, INSTRUCTOR o COORDINADOR_SST
    """

    message = "Se requiere ser administrativo o instructor."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in ["ADMINISTRATIVO", "INSTRUCTOR", "COORDINADOR_SST"]
        )


class EsVigilanciaOAdministrativo(BasePermission):
    """
    Permiso: Usuarios VIGILANCIA, ADMINISTRATIVO o COORDINADOR_SST
    """

    message = "Se requiere ser vigilancia o administrativo."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in ["VIGILANCIA", "ADMINISTRATIVO", "COORDINADOR_SST"]
        )


class EsBrigadaOAdministrativo(BasePermission):
    """
    Permiso: Usuarios BRIGADA, ADMINISTRATIVO, COORDINADOR_SST,
    o cualquier usuario con es_brigada=True
    """

    message = "Se requiere ser miembro de brigada o administrativo."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.rol in ["BRIGADA", "ADMINISTRATIVO", "COORDINADOR_SST"] or request.user.es_brigada


class NoEsVisitante(BasePermission):
    """
    Permiso: Cualquier usuario excepto VISITANTE
    """

    message = "Los visitantes no tienen acceso a esta funcionalidad."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.rol != "VISITANTE"


class PuedeGestionarUsuarios(BasePermission):
    """
    Permiso: ADMINISTRATIVO o COORDINADOR_SST pueden gestionar usuarios
    """

    message = "Solo el personal administrativo puede gestionar usuarios."

    def has_permission(self, request, view):
        if request.method == "GET":
            return request.user and request.user.is_authenticated

        return (
            request.user and request.user.is_authenticated and request.user.rol in ["ADMINISTRATIVO", "COORDINADOR_SST"]
        )

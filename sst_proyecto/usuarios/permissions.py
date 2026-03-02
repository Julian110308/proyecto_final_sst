"""
Permisos personalizados basados en roles
Sistema SST - Centro Minero SENA
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
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
                messages.warning(request, 'Debes iniciar sesión para acceder.')
                return redirect('login')

            # Verificar que el usuario tenga uno de los roles permitidos
            if request.user.rol not in roles_permitidos:
                messages.error(
                    request,
                    f'No tienes permiso para acceder a esta sección. '
                    f'Se requiere rol: {", ".join(roles_permitidos)}'
                )
                return redirect('dashboard')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorador


def solo_administrativo(view_func):
    """
    Decorador para vistas de ADMINISTRATIVO o COORDINADOR_SST
    """
    return rol_requerido('ADMINISTRATIVO', 'COORDINADOR_SST')(view_func)


def excluir_visitantes(view_func):
    """
    Decorador para bloquear acceso a visitantes
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión para acceder.')
            return redirect('login')

        if request.user.rol == 'VISITANTE':
            messages.error(request, 'Los visitantes no tienen acceso a esta sección.')
            return redirect('dashboard')

        return view_func(request, *args, **kwargs)
    return wrapper


# ====================================================================
# CLASES DE PERMISOS PARA REST FRAMEWORK (API)
# ====================================================================

class EsCoordinador(BasePermission):
    """
    Permiso: Solo el Coordinador SST (administrador del sistema)
    """
    message = 'Solo el Coordinador SST puede realizar esta acción.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == 'COORDINADOR_SST'
        )


class EsAdministrativo(BasePermission):
    """
    Permiso: Solo usuarios con rol ADMINISTRATIVO
    """
    message = 'Solo el personal administrativo puede realizar esta acción.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == 'ADMINISTRATIVO'
        )


class EsAdministrativoOInstructor(BasePermission):
    """
    Permiso: Usuarios ADMINISTRATIVO, INSTRUCTOR o COORDINADOR_SST
    """
    message = 'Se requiere ser administrativo o instructor.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in ['ADMINISTRATIVO', 'INSTRUCTOR', 'COORDINADOR_SST']
        )


class EsVigilanciaOAdministrativo(BasePermission):
    """
    Permiso: Usuarios VIGILANCIA, ADMINISTRATIVO o COORDINADOR_SST
    """
    message = 'Se requiere ser vigilancia o administrativo.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in ['VIGILANCIA', 'ADMINISTRATIVO', 'COORDINADOR_SST']
        )


class EsBrigadaOAdministrativo(BasePermission):
    """
    Permiso: Usuarios BRIGADA, ADMINISTRATIVO, COORDINADOR_SST,
    o cualquier usuario con es_brigada=True
    """
    message = 'Se requiere ser miembro de brigada o administrativo.'

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return (
            request.user.rol in ['BRIGADA', 'ADMINISTRATIVO', 'COORDINADOR_SST']
            or request.user.es_brigada
        )


class NoEsVisitante(BasePermission):
    """
    Permiso: Cualquier usuario excepto VISITANTE
    """
    message = 'Los visitantes no tienen acceso a esta funcionalidad.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol != 'VISITANTE'
        )


class PuedeGestionarUsuarios(BasePermission):
    """
    Permiso: ADMINISTRATIVO o COORDINADOR_SST pueden gestionar usuarios
    """
    message = 'Solo el personal administrativo puede gestionar usuarios.'

    def has_permission(self, request, view):
        if request.method == 'GET':
            return request.user and request.user.is_authenticated

        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in ['ADMINISTRATIVO', 'COORDINADOR_SST']
        )


class PuedeVerSoloSusDatos(BasePermission):
    """
    Permiso: Los usuarios solo pueden ver sus propios datos
    Excepto ADMINISTRATIVO y COORDINADOR_SST que pueden ver todo
    """
    message = 'Solo puedes ver tu propia información.'

    def has_object_permission(self, request, view, obj):
        if request.user.rol in ['ADMINISTRATIVO', 'COORDINADOR_SST']:
            return True
        return obj.id == request.user.id


# ====================================================================
# FUNCIONES HELPER
# ====================================================================

def usuario_puede_acceder_modulo(usuario, modulo):
    """
    Verifica si un usuario puede acceder a un módulo específico

    Args:
        usuario: Instancia del Usuario
        modulo: Nombre del módulo ('acceso', 'mapas', 'emergencias', etc.)

    Returns:
        bool: True si tiene acceso, False si no
    """
    PERMISOS_MODULOS = {
        'acceso': ['COORDINADOR_SST', 'ADMINISTRATIVO', 'VIGILANCIA', 'INSTRUCTOR'],
        'mapas': ['COORDINADOR_SST', 'ADMINISTRATIVO', 'INSTRUCTOR', 'VIGILANCIA', 'BRIGADA', 'APRENDIZ'],
        'emergencias': ['COORDINADOR_SST', 'ADMINISTRATIVO', 'BRIGADA', 'VIGILANCIA'],
        'reportes': ['COORDINADOR_SST', 'ADMINISTRATIVO', 'INSTRUCTOR', 'VIGILANCIA', 'BRIGADA', 'APRENDIZ'],
        'usuarios': ['COORDINADOR_SST', 'ADMINISTRATIVO'],
        'visitantes': ['COORDINADOR_SST', 'ADMINISTRATIVO', 'VIGILANCIA'],
    }

    roles_permitidos = PERMISOS_MODULOS.get(modulo, [])
    return usuario.rol in roles_permitidos


def obtener_modulos_disponibles(usuario):
    """
    Obtiene la lista de módulos a los que el usuario tiene acceso

    Args:
        usuario: Instancia del Usuario

    Returns:
        list: Lista de nombres de módulos
    """
    TODOS_MODULOS = ['acceso', 'mapas', 'emergencias', 'reportes', 'usuarios', 'visitantes']

    return [
        modulo for modulo in TODOS_MODULOS
        if usuario_puede_acceder_modulo(usuario, modulo)
    ]

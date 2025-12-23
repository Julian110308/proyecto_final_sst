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
    Decorador simple para vistas exclusivas de ADMINISTRATIVO
    """
    return rol_requerido('ADMINISTRATIVO')(view_func)


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
    Permiso: Usuarios ADMINISTRATIVO o INSTRUCTOR
    """
    message = 'Se requiere ser administrativo o instructor.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in ['ADMINISTRATIVO', 'INSTRUCTOR']
        )


class EsVigilanciaOAdministrativo(BasePermission):
    """
    Permiso: Usuarios VIGILANCIA o ADMINISTRATIVO
    Para control de acceso
    """
    message = 'Se requiere ser vigilancia o administrativo.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in ['VIGILANCIA', 'ADMINISTRATIVO']
        )


class EsBrigadaOAdministrativo(BasePermission):
    """
    Permiso: Usuarios BRIGADA o ADMINISTRATIVO
    Para gestión de emergencias
    """
    message = 'Se requiere ser miembro de brigada o administrativo.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in ['BRIGADA', 'ADMINISTRATIVO']
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
    Permiso: Solo ADMINISTRATIVO puede gestionar usuarios
    """
    message = 'Solo el personal administrativo puede gestionar usuarios.'

    def has_permission(self, request, view):
        # GET permitido para todos (ver perfil)
        if request.method == 'GET':
            return request.user and request.user.is_authenticated

        # POST, PUT, DELETE solo para administrativos
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol == 'ADMINISTRATIVO'
        )


class PuedeVerSoloSusDatos(BasePermission):
    """
    Permiso: Los usuarios solo pueden ver sus propios datos
    Excepto ADMINISTRATIVO que puede ver todo
    """
    message = 'Solo puedes ver tu propia información.'

    def has_object_permission(self, request, view, obj):
        # ADMINISTRATIVO puede ver todo
        if request.user.rol == 'ADMINISTRATIVO':
            return True

        # Los demás solo sus propios datos
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
        'acceso': ['ADMINISTRATIVO', 'VIGILANCIA', 'INSTRUCTOR'],
        'mapas': ['ADMINISTRATIVO', 'INSTRUCTOR', 'VIGILANCIA', 'BRIGADA'],
        'emergencias': ['ADMINISTRATIVO', 'BRIGADA', 'INSTRUCTOR', 'VIGILANCIA'],
        'reportes': ['ADMINISTRATIVO', 'INSTRUCTOR', 'VIGILANCIA', 'BRIGADA', 'APRENDIZ'],
        'usuarios': ['ADMINISTRATIVO'],
        'visitantes': ['ADMINISTRATIVO', 'VIGILANCIA', 'INSTRUCTOR'],
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

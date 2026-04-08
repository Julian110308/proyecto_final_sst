"""
Vista personalizada de login — autenticación por correo electrónico
"""

import logging
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django_ratelimit.decorators import ratelimit
from .models import Usuario

logger = logging.getLogger("usuarios")


@ratelimit(key="ip", rate="10/m", method="POST", block=False)
def custom_login_view(request):
    """Vista de login: el usuario ingresa su correo, se busca el username interno
    y se autentica con él."""

    from .models import ProgramaFormacion

    def _render_login(request):
        programas = list(ProgramaFormacion.objects.filter(activo=True).values_list("nombre", flat=True))
        return render(request, "login.html", {"programas": programas})

    # axes redirige aquí con ?bloqueado=1 cuando supera el límite de intentos fallidos
    if request.GET.get("bloqueado"):
        ip = request.META.get("REMOTE_ADDR", "")
        logger.warning(f"Cuenta bloqueada por intentos fallidos desde IP: {ip}")
        messages.error(
            request,
            "Tu acceso ha sido bloqueado temporalmente por múltiples intentos fallidos. "
            "Espera 15 minutos e intenta de nuevo, o contacta al Coordinador SST.",
        )
        return _render_login(request)

    if getattr(request, "limited", False):
        logger.warning(f"Rate limit excedido en login desde IP: {request.META.get('REMOTE_ADDR')}")
        messages.error(request, "Demasiados intentos de acceso. Espera 1 minuto e intenta de nuevo.")
        return _render_login(request)

    if request.method == "POST":
        email = request.POST.get("username", "").strip()  # el campo HTML sigue llamándose 'username'
        password = request.POST.get("password", "")

        user = None

        # Verificar estado de cuenta ANTES de autenticar.
        # Los roles operativos creados por admin (BRIGADA, COORDINADOR_SST) no pasan
        # por el flujo de aprobación; si quedaron en PENDIENTE se activan automáticamente.
        ROLES_SIN_APROBACION = {"BRIGADA", "COORDINADOR_SST", "APRENDIZ", "VISITANTE"}
        try:
            usuario_obj_check = Usuario.objects.get(email__iexact=email)
            if usuario_obj_check.estado_cuenta == "PENDIENTE":
                if usuario_obj_check.rol not in ROLES_SIN_APROBACION:
                    logger.warning(f"Intento de login con cuenta pendiente: {email}")
                    messages.warning(
                        request,
                        "Tu cuenta está pendiente de aprobación por el Coordinador SST. "
                        "Recibirás acceso una vez sea revisada tu solicitud.",
                    )
                    return _render_login(request)
                else:
                    # Activar automáticamente cuentas operativas que quedaron en PENDIENTE
                    usuario_obj_check.estado_cuenta = "ACTIVO"
                    usuario_obj_check.activo = True
                    usuario_obj_check.is_active = True
                    usuario_obj_check.save(update_fields=["estado_cuenta", "activo", "is_active"])
                    logger.info(f"Cuenta operativa activada automáticamente: {email} (rol={usuario_obj_check.rol})")
            elif usuario_obj_check.estado_cuenta == "BLOQUEADO":
                logger.warning(f"Intento de login con cuenta bloqueada: {email}")
                messages.error(request, "Tu cuenta ha sido bloqueada. Contacta al Coordinador SST.")
                return _render_login(request)
        except Usuario.DoesNotExist:
            pass

        # Buscar el usuario por email y autenticar con su username interno
        try:
            usuario_obj = Usuario.objects.get(email__iexact=email)
            user = authenticate(request, username=usuario_obj.username, password=password)
        except Usuario.DoesNotExist:
            user = None

        if user is not None:
            if user.activo:
                login(request, user)
                logger.info(f"Login exitoso: {user.username} ({user.rol})")
                next_url = request.GET.get("next", "/")
                return redirect(next_url)
            else:
                logger.warning(f"Intento de login con usuario inactivo: {email}")
                messages.error(request, "Tu cuenta está inactiva. Contacta al administrador.")
        else:
            logger.warning(f"Login fallido para: {email}")
            messages.error(request, "Correo o contraseña incorrectos.")

    return _render_login(request)

"""
Vista personalizada de login — autenticación por correo electrónico
"""
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Usuario


def custom_login_view(request):
    """Vista de login: el usuario ingresa su correo, se busca el username interno
    y se autentica con él."""

    if request.method == 'POST':
        email = request.POST.get('username', '').strip()   # el campo HTML sigue llamándose 'username'
        password = request.POST.get('password', '')

        print(f"\n{'='*70}")
        print(f"INTENTO DE LOGIN:")
        print(f"  Email ingresado: '{email}'")
        print(f"  Contraseña: {'*' * len(password)}")

        user = None

        # Buscar el usuario por email y autenticar con su username interno
        try:
            usuario_obj = Usuario.objects.get(email__iexact=email)
            user = authenticate(request, username=usuario_obj.username, password=password)
        except Usuario.DoesNotExist:
            user = None

        # Verificar estado de cuenta antes de autenticar (PENDIENTE no tiene is_active=True)
        try:
            usuario_obj_check = Usuario.objects.get(email__iexact=email)
            if usuario_obj_check.estado_cuenta == 'PENDIENTE':
                print(f"  Error: Cuenta pendiente de aprobación")
                print(f"{'='*70}\n")
                messages.warning(
                    request,
                    'Tu cuenta está pendiente de aprobación por el Coordinador SST. '
                    'Recibirás acceso una vez sea revisada tu solicitud.'
                )
                return render(request, 'login.html')
            elif usuario_obj_check.estado_cuenta == 'BLOQUEADO':
                print(f"  Error: Cuenta bloqueada")
                print(f"{'='*70}\n")
                messages.error(request, 'Tu cuenta ha sido bloqueada. Contacta al Coordinador SST.')
                return render(request, 'login.html')
        except Usuario.DoesNotExist:
            pass

        if user is not None:
            print(f"  Autenticacion: OK — {user.username} ({user.rol})")
            if user.activo:
                login(request, user)
                print(f"  Login completado")
                print(f"{'='*70}\n")
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
            else:
                print(f"  Error: Usuario inactivo")
                print(f"{'='*70}\n")
                messages.error(request, 'Tu cuenta está inactiva. Contacta al administrador.')
        else:
            print(f"  Autenticacion: FALLO — correo o contraseña incorrectos")
            print(f"{'='*70}\n")
            messages.error(request, 'Correo o contraseña incorrectos.')

    return render(request, 'login.html')

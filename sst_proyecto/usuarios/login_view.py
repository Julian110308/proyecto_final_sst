"""
Vista personalizada de login con debugging
"""
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

def custom_login_view(request):
    """Vista de login personalizada con debugging"""

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        print(f"\n{'='*70}")
        print(f"INTENTO DE LOGIN:")
        print(f"  Usuario ingresado: '{username}'")
        print(f"  Contraseña ingresada: {'*' * len(password)}")
        print(f"  POST data keys: {list(request.POST.keys())}")

        # Intentar autenticación
        user = authenticate(request, username=username, password=password)

        if user is not None:
            print(f"  Autenticacion: OK")
            print(f"  Usuario: {user.username} ({user.rol})")
            print(f"  Activo: {user.activo}")

            if user.activo:
                login(request, user)
                print(f"  Login completado")
                print(f"{'='*70}\n")

                # Redirigir al dashboard
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
            else:
                print(f"  Error: Usuario inactivo")
                print(f"{'='*70}\n")
                messages.error(request, 'Tu cuenta esta inactiva.')
        else:
            print(f"  Autenticacion: FALLO")
            print(f"  Razon: Credenciales incorrectas")
            print(f"{'='*70}\n")
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'login.html')

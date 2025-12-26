"""
Script simple para probar login desde shell
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sst_proyecto.settings')
django.setup()

from django.contrib.auth import authenticate
from usuarios.models import Usuario

print("=" * 70)
print("PRUEBA DE LOGIN - Diagnóstico Completo")
print("=" * 70)
print()

# 1. Verificar usuarios
print("1. USUARIOS EN BASE DE DATOS:")
usuarios = Usuario.objects.all()
for u in usuarios:
    print(f"   - {u.username:15} | Activo: {u.activo} | Email: {u.email}")
print()

# 2. Probar autenticación admin
print("2. PRUEBA DE AUTENTICACIÓN:")
username = 'admin'
password = 'admin123'

usuario = authenticate(username=username, password=password)

if usuario:
    print(f"   OK - Usuario '{username}' autenticado correctamente")
    print(f"   - ID: {usuario.id}")
    print(f"   - Rol: {usuario.rol}")
    print(f"   - Activo: {usuario.activo}")
    print(f"   - Email: {usuario.email}")
else:
    print(f"   FALLO - No se pudo autenticar '{username}'")

    # Diagnóstico adicional
    try:
        u = Usuario.objects.get(username=username)
        print(f"   - Usuario existe: SÍ")
        print(f"   - Usuario activo: {u.activo}")
        print(f"   - Hash password: {u.password[:30]}...")

        # Probar verificación directa
        if u.check_password(password):
            print(f"   - check_password(): OK")
        else:
            print(f"   - check_password(): FALLO")
    except Usuario.DoesNotExist:
        print(f"   - Usuario existe: NO")

print()

# 3. Verificar configuración Django
print("3. CONFIGURACIÓN DJANGO:")
from django.conf import settings
print(f"   - AUTH_USER_MODEL: {settings.AUTH_USER_MODEL}")
print(f"   - AUTHENTICATION_BACKENDS: {settings.AUTHENTICATION_BACKENDS}")
print(f"   - DEBUG: {settings.DEBUG}")
print()

print("=" * 70)
print("FIN DEL DIAGNÓSTICO")
print("=" * 70)

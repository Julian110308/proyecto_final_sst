"""
Script para agregar emails a los usuarios existentes
Sistema SST - Centro Minero SENA
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sst_proyecto.settings')
django.setup()

from usuarios.models import Usuario

def agregar_emails():
    """Agrega emails a los usuarios que no tienen"""

    print("\n" + "="*70)
    print("AGREGANDO EMAILS A USUARIOS")
    print("="*70 + "\n")

    usuarios = Usuario.objects.all()
    actualizados = 0

    for usuario in usuarios:
        if not usuario.email or usuario.email == '':
            # Generar email basado en el username
            email = f"{usuario.username}@centrominero.sena.edu.co"
            usuario.email = email
            usuario.save()
            print(f"Email agregado a {usuario.username}: {email}")
            actualizados += 1
        else:
            print(f"{usuario.username} ya tiene email: {usuario.email}")

    print(f"\nTotal usuarios actualizados: {actualizados}")
    print("="*70 + "\n")

    # Mostrar resumen
    print("RESUMEN DE USUARIOS:")
    print("-" * 70)
    for usuario in Usuario.objects.all():
        print(f"- {usuario.username:20} | {usuario.email:40} | {usuario.get_rol_display()}")
    print("-" * 70)

if __name__ == '__main__':
    agregar_emails()

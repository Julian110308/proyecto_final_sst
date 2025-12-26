"""
Script para resetear las contraseñas de los usuarios
Ejecutar: python resetear_passwords.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sst_proyecto.settings')
django.setup()

from usuarios.models import Usuario

def resetear_passwords():
    """Resetea las contraseñas de todos los usuarios usando set_password()"""

    # Contraseñas por usuario
    usuarios_passwords = {
        'admin': 'admin123',
        'dario': 'password123',
        'ruben': 'password123',
        'julian': 'password123',
        'Tenjo': 'password123',
        'kevin': 'password123',
    }

    print("Reseteando contraseñas...")
    print("=" * 70)

    for username, password in usuarios_passwords.items():
        try:
            usuario = Usuario.objects.get(username=username)

            # Usar set_password para hashear correctamente
            usuario.set_password(password)
            usuario.save()

            print(f"OK - {username:15} -> Contraseña: {password}")

            # Verificar que funciona
            from django.contrib.auth import authenticate
            test = authenticate(username=username, password=password)
            if test:
                print(f"     {username:15} -> Autenticación: OK")
            else:
                print(f"     {username:15} -> Autenticación: FALLO")

        except Usuario.DoesNotExist:
            print(f"ERROR - Usuario '{username}' no existe")
        except Exception as e:
            print(f"ERROR - {username}: {str(e)}")

    print("=" * 70)
    print("\nContraseñas reseteadas correctamente!")
    print("\nPuedes iniciar sesión con:")
    print("  - Usuario: admin     | Contraseña: admin123")
    print("  - Usuario: julian    | Contraseña: password123")
    print("  - Usuario: dario     | Contraseña: password123")
    print("  - Usuario: ruben     | Contraseña: password123")
    print("  - Usuario: Tenjo     | Contraseña: password123")
    print("  - Usuario: kevin     | Contraseña: password123")

if __name__ == '__main__':
    resetear_passwords()

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sst_proyecto.settings')
django.setup()

from usuarios.models import Usuario

# Eliminar usuarios existentes (opcional)
print("Creando usuarios...")

# Crear usuarios
usuarios = [
    {
        'username': 'admin',
        'password': 'admin123',
        'email': 'admin@sena.edu.co',
        'numero_documento': '100001',
        'rol': 'ADMINISTRATIVO',
        'is_superuser': True,
        'is_staff': True
    },
    {
        'username': 'vigilancia',
        'password': 'vigilancia123',
        'email': 'vigilancia@sena.edu.co',
        'numero_documento': '100002',
        'rol': 'VIGILANCIA'
    },
    {
        'username': 'instructor',
        'password': 'instructor123',
        'email': 'instructor@sena.edu.co',
        'numero_documento': '100003',
        'rol': 'INSTRUCTOR'
    },
    {
        'username': 'brigada',
        'password': 'brigada123',
        'email': 'brigada@sena.edu.co',
        'numero_documento': '100004',
        'rol': 'BRIGADA'
    },
    {
        'username': 'aprendiz',
        'password': 'aprendiz123',
        'email': 'aprendiz@sena.edu.co',
        'numero_documento': '100005',
        'rol': 'APRENDIZ',
        'ficha': '2558443'
    }
]

for user_data in usuarios:
    username = user_data['username']
    password = user_data.pop('password')
    is_superuser = user_data.pop('is_superuser', False)
    is_staff = user_data.pop('is_staff', False)

    # Crear usuario
    usuario = Usuario(**user_data)
    usuario.set_password(password)
    usuario.is_superuser = is_superuser
    usuario.is_staff = is_staff
    usuario.save()

    print(f"OK: {username} - Contrasena: {password} ({user_data['rol']})")

print("\n=== USUARIOS CREADOS EXITOSAMENTE ===")
print("Puedes iniciar sesion con cualquiera de estos usuarios")

"""
Comando para crear el Coordinador SST del sistema.
Solo debe existir un Coordinador SST.

Uso:
    python manage.py crear_coordinador
"""

from django.core.management.base import BaseCommand
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from getpass import getpass


class Command(BaseCommand):
    help = "Crea el Coordinador SST (administrador del sistema)"

    def handle(self, *args, **options):
        from usuarios.models import Usuario

        self.stdout.write(self.style.WARNING("\n══════════════════════════════════════════"))
        self.stdout.write(self.style.WARNING("  Crear Coordinador SST — Sistema SST"))
        self.stdout.write(self.style.WARNING("══════════════════════════════════════════\n"))

        # Verificar si ya existe uno
        existente = Usuario.objects.filter(rol="COORDINADOR_SST").first()
        if existente:
            self.stdout.write(
                self.style.WARNING(f"Ya existe un Coordinador SST: {existente.get_full_name()} ({existente.email})")
            )
            continuar = input("¿Deseas crear otro de todas formas? (s/N): ").strip().lower()
            if continuar != "s":
                self.stdout.write("Operación cancelada.")
                return

        # Recoger datos
        self.stdout.write("Ingresa los datos del Coordinador SST:\n")

        # Nombre y apellido
        while True:
            first_name = input("Nombre: ").strip()
            last_name = input("Apellido: ").strip()
            if first_name and last_name:
                break
            self.stdout.write(self.style.ERROR("Nombre y apellido son obligatorios."))

        # Correo @sena.edu.co
        while True:
            email = input("Correo (@sena.edu.co): ").strip().lower()
            try:
                validate_email(email)
            except ValidationError:
                self.stdout.write(self.style.ERROR("Correo inválido."))
                continue
            if not email.endswith("@sena.edu.co"):
                self.stdout.write(self.style.ERROR("El Coordinador debe tener correo @sena.edu.co."))
                continue
            if Usuario.objects.filter(email=email).exists():
                self.stdout.write(self.style.ERROR("Ya existe un usuario con ese correo."))
                continue
            break

        # Tipo y número de documento
        tipos = {"1": "CC", "2": "CE", "3": "TI", "4": "PAS"}
        self.stdout.write("Tipo de documento: 1=CC  2=CE  3=TI  4=PAS")
        while True:
            tipo_num = input("Opción (1-4): ").strip()
            if tipo_num in tipos:
                tipo_documento = tipos[tipo_num]
                break
            self.stdout.write(self.style.ERROR("Opción inválida."))

        while True:
            numero_documento = input("Número de documento: ").strip()
            if numero_documento:
                if Usuario.objects.filter(numero_documento=numero_documento).exists():
                    self.stdout.write(self.style.ERROR("Ya existe un usuario con ese documento."))
                    continue
                break
            self.stdout.write(self.style.ERROR("El número de documento es obligatorio."))

        # Contraseña
        while True:
            password = getpass("Contraseña (mín. 8 caracteres): ")
            if len(password) < 8:
                self.stdout.write(self.style.ERROR("La contraseña debe tener al menos 8 caracteres."))
                continue
            confirm = getpass("Confirmar contraseña: ")
            if password != confirm:
                self.stdout.write(self.style.ERROR("Las contraseñas no coinciden."))
                continue
            break

        # Generar username
        base_username = f"{first_name} {last_name}".title()
        username = base_username
        counter = 2
        while Usuario.objects.filter(username=username).exists():
            username = f"{base_username} {counter}"
            counter += 1

        # Crear usuario
        coordinador = Usuario.objects.create_user(
            username=username,
            email=email,
            password=password,
            rol="COORDINADOR_SST",
            estado_cuenta="ACTIVO",
            tipo_documento=tipo_documento,
            numero_documento=numero_documento,
            first_name=first_name,
            last_name=last_name,
            activo=True,
            is_staff=True,
        )

        self.stdout.write(self.style.SUCCESS("\n✔ Coordinador SST creado exitosamente:"))
        self.stdout.write(f"   Nombre:    {coordinador.get_full_name()}")
        self.stdout.write(f"   Correo:    {coordinador.email}")
        self.stdout.write(f"   Documento: {coordinador.tipo_documento} {coordinador.numero_documento}")
        self.stdout.write("   Rol:       COORDINADOR_SST")
        self.stdout.write(self.style.WARNING("\nGuarda estas credenciales en un lugar seguro.\n"))

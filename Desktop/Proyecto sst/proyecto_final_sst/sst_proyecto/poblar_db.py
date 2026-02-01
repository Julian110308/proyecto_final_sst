#!/usr/bin/env python
"""
Script para poblar la base de datos con datos de prueba
Sistema SST - Centro Minero SENA
"""

import os
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sst_proyecto.settings')
django.setup()

from usuarios.models import Usuario, Visitante
from control_acceso.models import Geocerca, RegistroAcceso, ConfiguracionAforo
from django.utils import timezone
from datetime import timedelta

def crear_usuarios():
    """Crea usuarios de prueba para cada rol"""
    print(">> Creando usuarios de prueba...")

    usuarios_data = [
        {
            'username': 'admin',
            'password': 'admin123',
            'email': 'admin@sena.edu.co',
            'first_name': 'Administrador',
            'last_name': 'Sistema',
            'rol': 'ADMINISTRATIVO',
            'tipo_documento': 'CC',
            'numero_documento': '1234567890',
            'telefono': '3001234567',
            'is_staff': True,
            'is_superuser': True
        },
        {
            'username': 'instructor1',
            'password': 'instructor123',
            'email': 'instructor1@sena.edu.co',
            'first_name': 'Carlos',
            'last_name': 'Rodríguez',
            'rol': 'INSTRUCTOR',
            'tipo_documento': 'CC',
            'numero_documento': '9876543210',
            'telefono': '3009876543'
        },
        {
            'username': 'vigilante1',
            'password': 'vigilante123',
            'email': 'vigilante1@sena.edu.co',
            'first_name': 'Pedro',
            'last_name': 'González',
            'rol': 'VIGILANCIA',
            'tipo_documento': 'CC',
            'numero_documento': '5555555555',
            'telefono': '3005555555'
        },
        {
            'username': 'brigada1',
            'password': 'brigada123',
            'email': 'brigada1@sena.edu.co',
            'first_name': 'Laura',
            'last_name': 'Martínez',
            'rol': 'BRIGADA',
            'tipo_documento': 'CC',
            'numero_documento': '7777777777',
            'telefono': '3007777777'
        },
        {
            'username': 'aprendiz1',
            'password': 'aprendiz123',
            'email': 'aprendiz1@misena.edu.co',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'rol': 'APRENDIZ',
            'tipo_documento': 'CC',
            'numero_documento': '1111111111',
            'telefono': '3001111111',
            'ficha': '2735425',
            'programa_formacion': 'Técnico en Sistemas'
        },
        {
            'username': 'aprendiz2',
            'password': 'aprendiz123',
            'email': 'aprendiz2@misena.edu.co',
            'first_name': 'María',
            'last_name': 'García',
            'rol': 'APRENDIZ',
            'tipo_documento': 'CC',
            'numero_documento': '2222222222',
            'telefono': '3002222222',
            'ficha': '2735425',
            'programa_formacion': 'Técnico en Sistemas'
        },
        {
            'username': 'aprendiz3',
            'password': 'aprendiz123',
            'email': 'aprendiz3@misena.edu.co',
            'first_name': 'Diego',
            'last_name': 'López',
            'rol': 'APRENDIZ',
            'tipo_documento': 'CC',
            'numero_documento': '3333333333',
            'telefono': '3003333333',
            'ficha': '2735426',
            'programa_formacion': 'Técnico en Minería'
        },
    ]

    usuarios_creados = []
    for data in usuarios_data:
        # Verificar si ya existe
        if Usuario.objects.filter(username=data['username']).exists():
            usuario = Usuario.objects.get(username=data['username'])
            print(f"   ✓ Usuario '{data['username']}' ya existe")
        else:
            password = data.pop('password')
            is_staff = data.pop('is_staff', False)
            is_superuser = data.pop('is_superuser', False)

            usuario = Usuario.objects.create_user(**data)
            usuario.set_password(password)
            usuario.is_staff = is_staff
            usuario.is_superuser = is_superuser
            usuario.save()

            print(f"   ✅ Creado usuario: {usuario.username} ({usuario.get_rol_display()})")

        usuarios_creados.append(usuario)

    return usuarios_creados


def crear_geocerca():
    """Crea la geocerca del Centro Minero"""
    print("\n🗺️  Creando geocerca del Centro Minero...")

    if Geocerca.objects.exists():
        geocerca = Geocerca.objects.first()
        print(f"   ✓ Geocerca '{geocerca.nombre}' ya existe")
    else:
        geocerca = Geocerca.objects.create(
            nombre='Centro Minero SENA Sogamoso',
            descripcion='Perímetro virtual del Centro Minero SENA en Sogamoso, Boyacá',
            centro_latitud=5.5339,
            centro_longitud=-73.3674,
            radio_metros=200,
            activo=True
        )
        print(f"   ✅ Creada geocerca: {geocerca.nombre}")

    return geocerca


def crear_configuracion_aforo():
    """Crea la configuración de aforo"""
    print("\n👥 Creando configuración de aforo...")

    if ConfiguracionAforo.objects.exists():
        config = ConfiguracionAforo.objects.first()
        print(f"   ✓ Configuración de aforo ya existe")
    else:
        config = ConfiguracionAforo.objects.create(
            aforo_maximo=2000,
            aforo_minimo=1800,
            mensaje_alerta='Se está alcanzando el aforo máximo del centro. Por favor coordinar con vigilancia.',
            activo=True
        )
        print(f"   ✅ Creada configuración de aforo: {config.aforo_maximo} personas")

    return config


def crear_visitantes(usuarios):
    """Crea visitantes de prueba"""
    print("\n👤 Creando visitantes de prueba...")

    # Buscar un instructor para asignar como persona a visitar
    instructor = next((u for u in usuarios if u.rol == 'INSTRUCTOR'), None)
    vigilante = next((u for u in usuarios if u.rol == 'VIGILANCIA'), None)

    if not instructor or not vigilante:
        print("   ⚠️  No hay instructor o vigilante para asignar visitantes")
        return []

    visitantes_data = [
        {
            'nombre_completo': 'Roberto Sánchez',
            'tipo_documento': 'CC',
            'numero_documento': '8888888888',
            'entidad': 'Carbones del Norte',
            'telefono': '3008888888',
            'persona_a_visitar': instructor,
            'motivo_visita': 'Reunión técnica sobre capacitación minera',
            'registrado_por': vigilante
        },
        {
            'nombre_completo': 'Ana Gutiérrez',
            'tipo_documento': 'CE',
            'numero_documento': '9999999999',
            'entidad': 'Universidad Nacional',
            'telefono': '3009999999',
            'persona_a_visitar': instructor,
            'motivo_visita': 'Intercambio académico',
            'registrado_por': vigilante
        }
    ]

    visitantes_creados = []
    for data in visitantes_data:
        visitante, created = Visitante.objects.get_or_create(
            numero_documento=data['numero_documento'],
            defaults=data
        )

        if created:
            print(f"   ✅ Creado visitante: {visitante.nombre_completo}")
        else:
            print(f"   ✓ Visitante '{visitante.nombre_completo}' ya existe")

        visitantes_creados.append(visitante)

    return visitantes_creados


def crear_registros_acceso(usuarios):
    """Crea registros de acceso de prueba"""
    print("\n📊 Creando registros de acceso de prueba...")

    ahora = timezone.now()

    # Crear algunos registros de hoy
    aprendices = [u for u in usuarios if u.rol == 'APRENDIZ']

    # Aprendices que ya ingresaron y salieron
    for i, aprendiz in enumerate(aprendices[:2]):
        hora_ingreso = ahora - timedelta(hours=4 - i, minutes=30)
        hora_egreso = ahora - timedelta(hours=1, minutes=15)

        registro, created = RegistroAcceso.objects.get_or_create(
            usuario=aprendiz,
            fecha_hora_ingreso=hora_ingreso,
            defaults={
                'tipo': 'INGRESO',
                'metodo_ingreso': 'QR',
                'latitud_ingreso': 5.5339,
                'longitud_ingreso': -73.3674,
                'fecha_hora_egreso': hora_egreso,
                'metodo_egreso': 'QR',
                'latitud_egreso': 5.5339,
                'longitud_egreso': -73.3674
            }
        )

        if created:
            print(f"   ✅ Registro completo para: {aprendiz.get_full_name()}")

    # Aprendices que aún están dentro
    if len(aprendices) > 2:
        aprendiz = aprendices[2]
        hora_ingreso = ahora - timedelta(hours=2, minutes=45)

        # Verificar si ya tiene un ingreso activo
        if not RegistroAcceso.objects.filter(usuario=aprendiz, fecha_hora_egreso__isnull=True).exists():
            registro = RegistroAcceso.objects.create(
                usuario=aprendiz,
                tipo='INGRESO',
                fecha_hora_ingreso=hora_ingreso,
                metodo_ingreso='MANUAL',
                latitud_ingreso=5.5339,
                longitud_ingreso=-73.3674
            )
            print(f"   ✅ Registro activo (dentro) para: {aprendiz.get_full_name()}")
        else:
            print(f"   ✓ {aprendiz.get_full_name()} ya tiene un registro activo")

    # Instructor dentro
    instructor = next((u for u in usuarios if u.rol == 'INSTRUCTOR'), None)
    if instructor:
        hora_ingreso = ahora - timedelta(hours=5)

        if not RegistroAcceso.objects.filter(usuario=instructor, fecha_hora_egreso__isnull=True).exists():
            registro = RegistroAcceso.objects.create(
                usuario=instructor,
                tipo='INGRESO',
                fecha_hora_ingreso=hora_ingreso,
                metodo_ingreso='AUTOMATICO',
                latitud_ingreso=5.5339,
                longitud_ingreso=-73.3674
            )
            print(f"   ✅ Registro activo para instructor: {instructor.get_full_name()}")


def main():
    """Función principal"""
    print("=" * 60)
    print("🚀 INICIANDO POBLACIÓN DE BASE DE DATOS")
    print("   Sistema SST - Centro Minero SENA")
    print("=" * 60)

    try:
        # Crear datos
        usuarios = crear_usuarios()
        geocerca = crear_geocerca()
        config_aforo = crear_configuracion_aforo()
        visitantes = crear_visitantes(usuarios)
        crear_registros_acceso(usuarios)

        print("\n" + "=" * 60)
        print("✅ BASE DE DATOS POBLADA EXITOSAMENTE")
        print("=" * 60)
        print("\n📋 CREDENCIALES DE ACCESO:")
        print("\n   👤 Administrador:")
        print("      Usuario: admin")
        print("      Contraseña: admin123")
        print("\n   👨‍🏫 Instructor:")
        print("      Usuario: instructor1")
        print("      Contraseña: instructor123")
        print("\n   👮 Vigilancia:")
        print("      Usuario: vigilante1")
        print("      Contraseña: vigilante123")
        print("\n   🚒 Brigada:")
        print("      Usuario: brigada1")
        print("      Contraseña: brigada123")
        print("\n   🎓 Aprendices:")
        print("      Usuario: aprendiz1, aprendiz2, aprendiz3")
        print("      Contraseña: aprendiz123")
        print("\n" + "=" * 60)
        print("🌐 Inicia el servidor con: python manage.py runserver")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

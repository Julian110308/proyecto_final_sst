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
from mapas.models import EdificioBloque, PuntoEncuentro, EquipamientoSeguridad
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
            centro_latitud=5.7303596,
            centro_longitud=-72.8943613,
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
        print("   ✓ Configuración de aforo ya existe")
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
                'metodo_ingreso': 'MANUAL',
                'latitud_ingreso': 5.7303596,
                'longitud_ingreso': -72.8943613,
                'fecha_hora_egreso': hora_egreso,
                'metodo_egreso': 'MANUAL',
                'latitud_egreso': 5.7303596,
                'longitud_egreso': -72.8943613
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
                latitud_ingreso=5.7303596,
                longitud_ingreso=-72.8943613
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
                latitud_ingreso=5.7303596,
                longitud_ingreso=-72.8943613
            )
            print(f"   ✅ Registro activo para instructor: {instructor.get_full_name()}")


def crear_edificios():
    """Crea edificios/bloques del centro"""
    print("\n🏢 Creando edificios/bloques...")

    edificios_data = [
        {
            'nombre': 'Edificio Administrativo Principal',
            'descripcion': 'Dirección y administración del Centro Nacional Minero',
            'latitud': 5.73036,
            'longitud': -72.89436,
            'tipo': 'ADMINISTRATIVO',
            'piso_minimo': 1,
            'piso_maximo': 2,
            'capacidad': 100,
        },
        {
            'nombre': 'Bloque de Aulas Teóricas',
            'descripcion': 'Aulas para formación teórica en minería',
            'latitud': 5.73070,
            'longitud': -72.89460,
            'tipo': 'AULAS',
            'piso_minimo': 1,
            'piso_maximo': 2,
            'capacidad': 300,
        },
        {
            'nombre': 'Talleres de Minería',
            'descripcion': 'Talleres prácticos de maquinaria y equipos mineros',
            'latitud': 5.73000,
            'longitud': -72.89410,
            'tipo': 'TALLER',
            'piso_minimo': 1,
            'piso_maximo': 1,
            'capacidad': 150,
        },
        {
            'nombre': 'Mina Didáctica Subterránea',
            'descripcion': 'Entrada a la mina didáctica para formación práctica',
            'latitud': 5.72970,
            'longitud': -72.89430,
            'tipo': 'TALLER',
            'piso_minimo': 1,
            'piso_maximo': 1,
            'capacidad': 50,
        },
        {
            'nombre': 'Laboratorios de Geología y Topografía',
            'descripcion': 'Laboratorios especializados en ciencias de la tierra',
            'latitud': 5.73090,
            'longitud': -72.89420,
            'tipo': 'LABORATORIO',
            'piso_minimo': 1,
            'piso_maximo': 1,
            'capacidad': 80,
        },
        {
            'nombre': 'Cafetería y Bienestar',
            'descripcion': 'Zona de alimentación y descanso para aprendices',
            'latitud': 5.73050,
            'longitud': -72.89480,
            'tipo': 'Cafeteria',
            'piso_minimo': 1,
            'piso_maximo': 1,
            'capacidad': 200,
        },
        {
            'nombre': 'Parqueadero Principal',
            'descripcion': 'Parqueadero de vehículos y motos',
            'latitud': 5.73120,
            'longitud': -72.89510,
            'tipo': 'PARQUEADERO',
            'piso_minimo': 1,
            'piso_maximo': 1,
            'capacidad': 100,
        },
    ]

    edificios_creados = []
    for data in edificios_data:
        edificio, created = EdificioBloque.objects.get_or_create(
            nombre=data['nombre'],
            defaults=data
        )
        if created:
            print(f"   ✅ Creado edificio: {edificio.nombre}")
        else:
            print(f"   ✓ Edificio '{edificio.nombre}' ya existe")
        edificios_creados.append(edificio)

    return edificios_creados


def crear_puntos_encuentro():
    """Crea puntos de encuentro para evacuación"""
    print("\n🚩 Creando puntos de encuentro...")

    puntos_data = [
        {
            'nombre': 'Punto Principal - Cancha Deportiva',
            'descripcion': 'Cancha deportiva central - Espacio abierto amplio para evacuación masiva',
            'latitud': 5.73040,
            'longitud': -72.89430,
            'capacidad': 500,
            'tipo_terreno': 'ABIERTO',
            'prioridad': 1,
            'tiene_agua': True,
            'tiene_sombra': False,
            'tiene_baños': True,
        },
        {
            'nombre': 'Punto Secundario - Parqueadero Norte',
            'descripcion': 'Zona de parqueadero norte - Área despejada',
            'latitud': 5.73130,
            'longitud': -72.89510,
            'capacidad': 250,
            'tipo_terreno': 'ABIERTO',
            'prioridad': 2,
            'tiene_agua': False,
            'tiene_sombra': True,
            'tiene_baños': False,
        },
        {
            'nombre': 'Punto Alterno - Entrada Principal',
            'descripcion': 'Zona de acceso principal - Salida rápida del centro',
            'latitud': 5.73150,
            'longitud': -72.89460,
            'capacidad': 200,
            'tipo_terreno': 'ABIERTO',
            'prioridad': 3,
            'tiene_agua': False,
            'tiene_sombra': False,
            'tiene_baños': False,
        },
        {
            'nombre': 'Punto de Evacuación Sur',
            'descripcion': 'Punto sur para evacuación de talleres',
            'latitud': 5.72960,
            'longitud': -72.89410,
            'capacidad': 150,
            'tipo_terreno': 'PARQUE',
            'prioridad': 2,
            'tiene_agua': False,
            'tiene_sombra': True,
            'tiene_baños': False,
        }
    ]

    puntos_creados = []
    for data in puntos_data:
        punto, created = PuntoEncuentro.objects.get_or_create(
            nombre=data['nombre'],
            defaults=data
        )
        if created:
            print(f"   ✅ Creado punto de encuentro: {punto.nombre}")
        else:
            print(f"   ✓ Punto '{punto.nombre}' ya existe")
        puntos_creados.append(punto)

    return puntos_creados


def crear_equipamientos(edificios):
    """Crea equipamientos de seguridad"""
    print("\n🧯 Creando equipamientos de seguridad...")

    ahora = timezone.now()

    # Mapear edificios por nombre para referencia
    edificios_map = {e.nombre: e for e in edificios}

    equipamientos_data = [
        # Extintores
        {
            'nombre': 'Extintor entrada principal',
            'codigo': 'EXT-001',
            'tipo': 'EXTINTOR',
            'descripcion': 'Extintor PQS 20 lbs - Entrada principal edificio administrativo',
            'latitud': 5.73036,
            'longitud': -72.89436,
            'edificio': edificios_map.get('Edificio Administrativo Principal'),
            'piso': 1,
            'estado': 'OPERATIVO',
            'ultima_revision': ahora - timedelta(days=30),
            'proxima_revision': ahora + timedelta(days=150),
        },
        {
            'nombre': 'Extintor pasillo segundo piso',
            'codigo': 'EXT-002',
            'tipo': 'EXTINTOR',
            'descripcion': 'Extintor CO2 10 lbs - Pasillo segundo piso administrativo',
            'latitud': 5.73038,
            'longitud': -72.89438,
            'edificio': edificios_map.get('Edificio Administrativo Principal'),
            'piso': 2,
            'estado': 'OPERATIVO',
            'ultima_revision': ahora - timedelta(days=30),
            'proxima_revision': ahora + timedelta(days=150),
        },
        {
            'nombre': 'Extintor aulas primer piso',
            'codigo': 'EXT-003',
            'tipo': 'EXTINTOR',
            'descripcion': 'Extintor PQS 20 lbs - Pasillo aulas primer piso',
            'latitud': 5.73070,
            'longitud': -72.89460,
            'edificio': edificios_map.get('Bloque de Aulas Teóricas'),
            'piso': 1,
            'estado': 'OPERATIVO',
            'ultima_revision': ahora - timedelta(days=45),
            'proxima_revision': ahora + timedelta(days=135),
        },
        {
            'nombre': 'Extintor entrada mina didáctica',
            'codigo': 'EXT-004',
            'tipo': 'EXTINTOR',
            'descripcion': 'Extintor CO2 20 lbs - Entrada mina didáctica (zona especial)',
            'latitud': 5.72970,
            'longitud': -72.89430,
            'edificio': edificios_map.get('Mina Didáctica Subterránea'),
            'piso': 1,
            'estado': 'OPERATIVO',
            'ultima_revision': ahora - timedelta(days=15),
            'proxima_revision': ahora + timedelta(days=165),
        },
        {
            'nombre': 'Extintor talleres',
            'codigo': 'EXT-005',
            'tipo': 'EXTINTOR',
            'descripcion': 'Extintor PQS 30 lbs - Área de talleres principal',
            'latitud': 5.73000,
            'longitud': -72.89410,
            'edificio': edificios_map.get('Talleres de Minería'),
            'piso': 1,
            'estado': 'MANTENIMIENTO',
            'ultima_revision': ahora - timedelta(days=200),
            'proxima_revision': ahora - timedelta(days=20),  # Vencido
        },
        # Botiquines
        {
            'nombre': 'Botiquín administrativo',
            'codigo': 'BOT-001',
            'tipo': 'BOTIQUIN',
            'descripcion': 'Botiquín tipo A completo - Recepción edificio administrativo',
            'latitud': 5.73036,
            'longitud': -72.89436,
            'edificio': edificios_map.get('Edificio Administrativo Principal'),
            'piso': 1,
            'estado': 'OPERATIVO',
            'ultima_revision': ahora - timedelta(days=20),
            'proxima_revision': ahora + timedelta(days=70),
        },
        {
            'nombre': 'Botiquín aulas',
            'codigo': 'BOT-002',
            'tipo': 'BOTIQUIN',
            'descripcion': 'Botiquín tipo A - Bloque de aulas primer piso',
            'latitud': 5.73070,
            'longitud': -72.89460,
            'edificio': edificios_map.get('Bloque de Aulas Teóricas'),
            'piso': 1,
            'estado': 'OPERATIVO',
            'ultima_revision': ahora - timedelta(days=25),
            'proxima_revision': ahora + timedelta(days=65),
        },
        {
            'nombre': 'Botiquín talleres',
            'codigo': 'BOT-003',
            'tipo': 'BOTIQUIN',
            'descripcion': 'Botiquín tipo B industrial - Talleres de minería',
            'latitud': 5.73000,
            'longitud': -72.89410,
            'edificio': edificios_map.get('Talleres de Minería'),
            'piso': 1,
            'estado': 'OPERATIVO',
            'ultima_revision': ahora - timedelta(days=10),
            'proxima_revision': ahora + timedelta(days=80),
        },
        {
            'nombre': 'Botiquín mina didáctica',
            'codigo': 'BOT-004',
            'tipo': 'BOTIQUIN',
            'descripcion': 'Botiquín tipo B emergencias - Entrada mina didáctica',
            'latitud': 5.72970,
            'longitud': -72.89430,
            'edificio': edificios_map.get('Mina Didáctica Subterránea'),
            'piso': 1,
            'estado': 'OPERATIVO',
            'ultima_revision': ahora - timedelta(days=5),
            'proxima_revision': ahora + timedelta(days=85),
        },
        # Camillas
        {
            'nombre': 'Camilla administrativa',
            'codigo': 'CAM-001',
            'tipo': 'CAMILLA',
            'descripcion': 'Camilla plegable con inmovilizador cervical',
            'latitud': 5.73036,
            'longitud': -72.89436,
            'edificio': edificios_map.get('Edificio Administrativo Principal'),
            'piso': 1,
            'estado': 'OPERATIVO',
            'ultima_revision': ahora - timedelta(days=60),
            'proxima_revision': ahora + timedelta(days=305),
        },
        {
            'nombre': 'Camilla talleres',
            'codigo': 'CAM-002',
            'tipo': 'CAMILLA',
            'descripcion': 'Camilla rígida para rescate en espacios confinados',
            'latitud': 5.73000,
            'longitud': -72.89410,
            'edificio': edificios_map.get('Talleres de Minería'),
            'piso': 1,
            'estado': 'OPERATIVO',
            'ultima_revision': ahora - timedelta(days=45),
            'proxima_revision': ahora + timedelta(days=320),
        },
        # Alarmas
        {
            'nombre': 'Alarma central',
            'codigo': 'ALR-001',
            'tipo': 'ALARMA',
            'descripcion': 'Alarma de emergencia central - Sistema de megafonía',
            'latitud': 5.73040,
            'longitud': -72.89440,
            'edificio': edificios_map.get('Edificio Administrativo Principal'),
            'piso': 1,
            'estado': 'OPERATIVO',
            'ultima_revision': ahora - timedelta(days=30),
            'proxima_revision': ahora + timedelta(days=335),
        },
        {
            'nombre': 'Alarma mina',
            'codigo': 'ALR-002',
            'tipo': 'ALARMA',
            'descripcion': 'Alarma de emergencia mina didáctica - Sistema luminoso y sonoro',
            'latitud': 5.72970,
            'longitud': -72.89430,
            'edificio': edificios_map.get('Mina Didáctica Subterránea'),
            'piso': 1,
            'estado': 'OPERATIVO',
            'ultima_revision': ahora - timedelta(days=15),
            'proxima_revision': ahora + timedelta(days=350),
        },
        # Salidas de emergencia
        {
            'nombre': 'Salida emergencia norte',
            'codigo': 'SAL-001',
            'tipo': 'SALIDA_EMERGENCIA',
            'descripcion': 'Señalización salida de emergencia norte - LED',
            'latitud': 5.73080,
            'longitud': -72.89470,
            'edificio': edificios_map.get('Bloque de Aulas Teóricas'),
            'piso': 1,
            'estado': 'OPERATIVO',
            'ultima_revision': ahora - timedelta(days=60),
            'proxima_revision': ahora + timedelta(days=305),
        },
        {
            'nombre': 'Salida emergencia sur',
            'codigo': 'SAL-002',
            'tipo': 'SALIDA_EMERGENCIA',
            'descripcion': 'Señalización salida de emergencia sur - LED',
            'latitud': 5.73060,
            'longitud': -72.89450,
            'edificio': edificios_map.get('Bloque de Aulas Teóricas'),
            'piso': 1,
            'estado': 'OPERATIVO',
            'ultima_revision': ahora - timedelta(days=60),
            'proxima_revision': ahora + timedelta(days=305),
        },
    ]

    equipamientos_creados = []
    for data in equipamientos_data:
        equipo, created = EquipamientoSeguridad.objects.get_or_create(
            codigo=data['codigo'],
            defaults=data
        )
        if created:
            print(f"   ✅ Creado {equipo.get_tipo_display()}: {equipo.codigo} - {equipo.nombre}")
        else:
            print(f"   ✓ Equipamiento '{equipo.codigo}' ya existe")
        equipamientos_creados.append(equipo)

    return equipamientos_creados


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

        # Crear datos de mapas y equipamientos
        edificios = crear_edificios()
        puntos_encuentro = crear_puntos_encuentro()
        equipamientos = crear_equipamientos(edificios)

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

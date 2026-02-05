#!/usr/bin/env python
"""
Script para corregir las coordenadas de los puntos de seguridad
para que estén dentro de la geocerca del Centro Minero SENA
Geocerca centrada en: 5.7303596, -72.8943613
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sst_proyecto.settings')
django.setup()

from mapas.models import EdificioBloque, PuntoEncuentro, EquipamientoSeguridad

# Coordenadas correctas dentro de la geocerca del Centro Minero
# Geocerca centro: 5.7303596, -72.8943613

def fix_edificios():
    """Actualiza coordenadas de edificios para que estén dentro de la geocerca"""
    print("\n== Corrigiendo EdificioBloque ==")

    # Coordenadas correctas para cada edificio dentro de la geocerca
    coordenadas_edificios = {
        'Edificio Administrativo Principal': (5.73036, -72.89436),
        'Bloque de Aulas': (5.73070, -72.89460),
        'Talleres de Minería': (5.73000, -72.89410),
        'Mina Didáctica': (5.72970, -72.89430),
        'Laboratorios': (5.73090, -72.89420),
        'Cafetería': (5.73050, -72.89480),
        'Parqueadero': (5.73120, -72.89510),
    }

    edificios = EdificioBloque.objects.all()
    for edificio in edificios:
        # Buscar coordenada correcta por nombre parcial
        nueva_coord = None
        for nombre_key, coords in coordenadas_edificios.items():
            if nombre_key.lower() in edificio.nombre.lower():
                nueva_coord = coords
                break

        if nueva_coord:
            old_lat, old_lng = edificio.latitud, edificio.longitud
            edificio.latitud = nueva_coord[0]
            edificio.longitud = nueva_coord[1]
            edificio.save()
            print(f"  OK: {edificio.nombre}: ({old_lat}, {old_lng}) -> ({nueva_coord[0]}, {nueva_coord[1]})")
        else:
            # Asignar al centro de la geocerca si no tiene match
            old_lat, old_lng = edificio.latitud, edificio.longitud
            # Solo actualizar si está fuera del rango de la geocerca
            if abs(edificio.latitud - 5.7303) > 0.003 or abs(edificio.longitud - (-72.8943)) > 0.003:
                edificio.latitud = 5.7303
                edificio.longitud = -72.8943
                edificio.save()
                print(f"  OK (centro): {edificio.nombre}: ({old_lat}, {old_lng}) -> (5.7303, -72.8943)")
            else:
                print(f"  Ya OK: {edificio.nombre}: ({old_lat}, {old_lng})")


def fix_puntos_encuentro():
    """Actualiza coordenadas de puntos de encuentro"""
    print("\n== Corrigiendo PuntoEncuentro ==")

    coordenadas_puntos = {
        'Cancha': (5.73040, -72.89430),
        'Principal': (5.73040, -72.89430),
        'Parqueadero': (5.73130, -72.89510),
        'Secundario': (5.73130, -72.89510),
        'Entrada': (5.73150, -72.89460),
        'Alterno': (5.73150, -72.89460),
        'Sur': (5.72960, -72.89410),
    }

    puntos = PuntoEncuentro.objects.all()
    for punto in puntos:
        nueva_coord = None
        for nombre_key, coords in coordenadas_puntos.items():
            if nombre_key.lower() in punto.nombre.lower():
                nueva_coord = coords
                break

        if nueva_coord:
            old_lat, old_lng = punto.latitud, punto.longitud
            punto.latitud = nueva_coord[0]
            punto.longitud = nueva_coord[1]
            punto.save()
            print(f"  OK: {punto.nombre}: ({old_lat}, {old_lng}) -> ({nueva_coord[0]}, {nueva_coord[1]})")
        else:
            old_lat, old_lng = punto.latitud, punto.longitud
            if abs(punto.latitud - 5.7303) > 0.003 or abs(punto.longitud - (-72.8943)) > 0.003:
                punto.latitud = 5.7304
                punto.longitud = -72.8945
                punto.save()
                print(f"  OK (centro): {punto.nombre}: ({old_lat}, {old_lng}) -> (5.7304, -72.8945)")
            else:
                print(f"  Ya OK: {punto.nombre}: ({old_lat}, {old_lng})")


def fix_equipamiento():
    """Actualiza coordenadas de equipamiento de seguridad"""
    print("\n== Corrigiendo EquipamientoSeguridad ==")

    # Asignar coordenadas según tipo
    coordenadas_por_tipo = {
        'EXTINTOR': [
            (5.73036, -72.89436),  # Entrada admin
            (5.72970, -72.89430),  # Mina didáctica
            (5.73070, -72.89460),  # Aulas
            (5.73000, -72.89410),  # Talleres
            (5.73050, -72.89480),  # Cafetería
        ],
        'BOTIQUIN': [
            (5.73070, -72.89460),  # Aulas
            (5.73000, -72.89410),  # Talleres
            (5.73036, -72.89436),  # Admin
            (5.73090, -72.89420),  # Laboratorios
        ],
        'ALARMA': [
            (5.73036, -72.89436),
            (5.73070, -72.89460),
        ],
        'CAMILLA': [
            (5.73036, -72.89436),
            (5.73000, -72.89410),
        ],
    }

    equipamientos = EquipamientoSeguridad.objects.all()
    contadores = {}

    for equipo in equipamientos:
        tipo = equipo.tipo
        if tipo not in contadores:
            contadores[tipo] = 0

        coords_lista = coordenadas_por_tipo.get(tipo, [(5.7303, -72.8943)])
        idx = contadores[tipo] % len(coords_lista)
        nueva_coord = coords_lista[idx]
        contadores[tipo] += 1

        old_lat, old_lng = equipo.latitud, equipo.longitud
        # Solo actualizar si está fuera del rango
        if abs(equipo.latitud - 5.7303) > 0.003 or abs(equipo.longitud - (-72.8943)) > 0.003:
            equipo.latitud = nueva_coord[0]
            equipo.longitud = nueva_coord[1]
            equipo.save()
            print(f"  OK: {equipo.tipo} {equipo.codigo}: ({old_lat}, {old_lng}) -> ({nueva_coord[0]}, {nueva_coord[1]})")
        else:
            print(f"  Ya OK: {equipo.tipo} {equipo.codigo}: ({old_lat}, {old_lng})")


def fix_geocerca():
    """Verifica que la geocerca tenga las coordenadas correctas"""
    print("\n== Verificando Geocerca ==")
    from control_acceso.models import Geocerca

    geocercas = Geocerca.objects.all()
    for g in geocercas:
        old_lat, old_lng = g.centro_latitud, g.centro_longitud
        if abs(g.centro_latitud - 5.7303596) > 0.001 or abs(g.centro_longitud - (-72.8943613)) > 0.001:
            g.centro_latitud = 5.7303596
            g.centro_longitud = -72.8943613
            g.radio_metros = 200
            g.save()
            print(f"  CORREGIDA: {g.nombre}: ({old_lat}, {old_lng}) -> (5.7303596, -72.8943613)")
        else:
            print(f"  Ya OK: {g.nombre}: ({old_lat}, {old_lng})")


if __name__ == '__main__':
    print("=" * 60)
    print("CORRIGIENDO COORDENADAS DE PUNTOS DE SEGURIDAD")
    print("Centro de geocerca: 5.7303596, -72.8943613")
    print("=" * 60)

    fix_geocerca()
    fix_edificios()
    fix_puntos_encuentro()
    fix_equipamiento()

    print("\n" + "=" * 60)
    print("CORRECCIONES COMPLETADAS")
    print("=" * 60)
    print("\nReinicia el servidor para ver los cambios en el mapa.")

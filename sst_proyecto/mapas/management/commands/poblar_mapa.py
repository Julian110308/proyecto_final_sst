"""
Management command para poblar la base de datos con los datos reales
del Centro Minero SENA: edificaciones, puntos de encuentro y rutas de evacuación.

Uso:
    python manage.py poblar_mapa
    python manage.py poblar_mapa --reset   (borra y recrea todo)
"""
import json
from django.core.management.base import BaseCommand
from mapas.models import EdificioBloque, PuntoEncuentro, RutaEvacuacion


EDIFICACIONES = [
    {'id': 1,  'lat': 5.7308266, 'lng': -72.8944621, 'nombre': 'Edificacion 1',  'tipo': 'AULAS'},
    {'id': 2,  'lat': 5.7306089, 'lng': -72.8944388, 'nombre': 'Edificacion 2',  'tipo': 'AULAS'},
    {'id': 3,  'lat': 5.7307180, 'lng': -72.8943197, 'nombre': 'Edificacion 3',  'tipo': 'AULAS'},
    {'id': 4,  'lat': 5.7305964, 'lng': -72.8943091, 'nombre': 'Edificacion 4',  'tipo': 'AULAS'},
    {'id': 5,  'lat': 5.7307631, 'lng': -72.8941685, 'nombre': 'Edificacion 5',  'tipo': 'TALLER'},
    {'id': 6,  'lat': 5.7306055, 'lng': -72.8941807, 'nombre': 'Edificacion 6',  'tipo': 'TALLER'},
    {'id': 7,  'lat': 5.7308157, 'lng': -72.8947557, 'nombre': 'Edificacion 7',  'tipo': 'LABORATORIO'},
    {'id': 8,  'lat': 5.7304729, 'lng': -72.8946135, 'nombre': 'Edificacion 8',  'tipo': 'LABORATORIO'},
    {'id': 9,  'lat': 5.7306724, 'lng': -72.8948627, 'nombre': 'Edificacion 9',  'tipo': 'LABORATORIO'},
    {'id': 10, 'lat': 5.7306460, 'lng': -72.8947499, 'nombre': 'Edificacion 10', 'tipo': 'LABORATORIO'},
    {'id': 11, 'lat': 5.7303035, 'lng': -72.8948299, 'nombre': 'Edificacion 11', 'tipo': 'ADMINISTRATIVO'},
    {'id': 12, 'lat': 5.7303504, 'lng': -72.8944825, 'nombre': 'Edificacion 12', 'tipo': 'ADMINISTRATIVO'},
    {'id': 13, 'lat': 5.7302012, 'lng': -72.8944738, 'nombre': 'Edificacion 13', 'tipo': 'ADMINISTRATIVO'},
    {'id': 14, 'lat': 5.7300200, 'lng': -72.8947224, 'nombre': 'Edificacion 14', 'tipo': 'TALLER'},
    {'id': 15, 'lat': 5.7296547, 'lng': -72.8947003, 'nombre': 'Edificacion 15', 'tipo': 'TALLER'},
    {'id': 16, 'lat': 5.7304283, 'lng': -72.8938899, 'nombre': 'Edificacion 16', 'tipo': 'AULAS'},
    {'id': 17, 'lat': 5.7303758, 'lng': -72.8936851, 'nombre': 'Edificacion 17', 'tipo': 'AULAS'},
    {'id': 18, 'lat': 5.7300397, 'lng': -72.8942211, 'nombre': 'Edificacion 18', 'tipo': 'CAFETERIA'},
    {'id': 19, 'lat': 5.7299135, 'lng': -72.8937115, 'nombre': 'Edificacion 19', 'tipo': 'MINA'},
    {'id': 20, 'lat': 5.7301815, 'lng': -72.8933961, 'nombre': 'Edificacion 20', 'tipo': 'MINA'},
    {'id': 21, 'lat': 5.7298857, 'lng': -72.8933810, 'nombre': 'Edificacion 21', 'tipo': 'MINA'},
    {'id': 22, 'lat': 5.7297219, 'lng': -72.8935096, 'nombre': 'Edificacion 22', 'tipo': 'BODEGA'},
    {'id': 23, 'lat': 5.7296522, 'lng': -72.8937856, 'nombre': 'Edificacion 23', 'tipo': 'BODEGA'},
    {'id': 24, 'lat': 5.7297075, 'lng': -72.8932150, 'nombre': 'Edificacion 24', 'tipo': 'ZONA_VERDE'},
    {'id': 25, 'lat': 5.7296381, 'lng': -72.8930312, 'nombre': 'Edificacion 25', 'tipo': 'ZONA_VERDE'},
]

PUNTOS_ENCUENTRO = [
    {
        'nombre': 'P1 - Cancha Deportiva',
        'descripcion': 'Punto de encuentro principal en la cancha deportiva del centro',
        'latitud': 5.7310,
        'longitud': -72.8942,
        'capacidad': 200,
        'tipo_terreno': 'ABIERTO',
        'prioridad': 1,
        'tiene_agua': False,
        'tiene_sombra': False,
        'tiene_baños': False,
    },
    {
        'nombre': 'P2 - Parqueadero Trasero',
        'descripcion': 'Punto de encuentro secundario en el parqueadero trasero',
        'latitud': 5.7312,
        'longitud': -72.8951,
        'capacidad': 150,
        'tipo_terreno': 'ABIERTO',
        'prioridad': 2,
        'tiene_agua': False,
        'tiene_sombra': False,
        'tiene_baños': False,
    },
    {
        'nombre': 'P3 - Jardin Central',
        'descripcion': 'Punto de encuentro terciario en el jardín central del campus',
        'latitud': 5.7304,
        'longitud': -72.8950,
        'capacidad': 100,
        'tipo_terreno': 'ABIERTO',
        'prioridad': 3,
        'tiene_agua': False,
        'tiene_sombra': True,
        'tiene_baños': False,
    },
]

RUTAS_EVACUACION = [
    {
        'nombre': 'Ruta Norte - Zona Aulas',
        'descripcion': 'Ruta de evacuación para la zona norte donde se encuentran las aulas principales',
        'waypoints': [
            [5.7308266, -72.8944621],
            [5.7307180, -72.8943197],
            [5.7306089, -72.8944388],
            [5.7305964, -72.8943091],
            [5.7304729, -72.8946135],
            [5.7303035, -72.8948299],
        ],
        'distancia_metros': 180,
        'tiempo_estimado_minutos': 3,
        'prioridad': 1,
        'punto_fin_idx': 0,  # P1 Cancha
    },
    {
        'nombre': 'Ruta Centro - Edificios Centrales',
        'descripcion': 'Ruta de evacuación para los edificios centrales del campus',
        'waypoints': [
            [5.7303504, -72.8944825],
            [5.7304729, -72.8946135],
            [5.7306460, -72.8947499],
            [5.7308157, -72.8947557],
        ],
        'distancia_metros': 120,
        'tiempo_estimado_minutos': 2,
        'prioridad': 1,
        'punto_fin_idx': 1,  # P2 Parqueadero
    },
    {
        'nombre': 'Ruta Sur - Talleres',
        'descripcion': 'Ruta de evacuación para la zona sur donde están los talleres',
        'waypoints': [
            [5.7296547, -72.8947003],
            [5.7300200, -72.8947224],
            [5.7303035, -72.8948299],
            [5.7304729, -72.8946135],
        ],
        'distancia_metros': 250,
        'tiempo_estimado_minutos': 4,
        'prioridad': 2,
        'punto_fin_idx': 0,  # P1 Cancha
    },
    {
        'nombre': 'Ruta Este - Laboratorios',
        'descripcion': 'Ruta de evacuación para la zona de laboratorios',
        'waypoints': [
            [5.7304283, -72.8938899],
            [5.7303758, -72.8936851],
            [5.7300397, -72.8942211],
            [5.7302012, -72.8944738],
            [5.7303504, -72.8944825],
        ],
        'distancia_metros': 220,
        'tiempo_estimado_minutos': 4,
        'prioridad': 2,
        'punto_fin_idx': 2,  # P3 Jardín
    },
    {
        'nombre': 'Ruta Sureste - Zona Baja',
        'descripcion': 'Ruta de evacuación para la zona baja del campus',
        'waypoints': [
            [5.7296381, -72.8930312],
            [5.7297075, -72.8932150],
            [5.7298857, -72.8933810],
            [5.7301815, -72.8933961],
            [5.7303758, -72.8936851],
            [5.7304283, -72.8938899],
        ],
        'distancia_metros': 350,
        'tiempo_estimado_minutos': 6,
        'prioridad': 3,
        'punto_fin_idx': 2,  # P3 Jardín
    },
    {
        'nombre': 'Ruta Suroeste - Mina Didactica',
        'descripcion': 'Ruta de evacuación desde la mina didáctica',
        'waypoints': [
            [5.7297219, -72.8935096],
            [5.7296522, -72.8937856],
            [5.7299135, -72.8937115],
            [5.7300397, -72.8942211],
            [5.7302012, -72.8944738],
        ],
        'distancia_metros': 280,
        'tiempo_estimado_minutos': 5,
        'prioridad': 2,
        'punto_fin_idx': 2,  # P3 Jardín
    },
]


class Command(BaseCommand):
    help = 'Pobla la base de datos con las edificaciones reales del Centro Minero SENA'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Elimina todos los datos existentes antes de crear los nuevos',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('Eliminando datos existentes del mapa...'))
            RutaEvacuacion.objects.all().delete()
            PuntoEncuentro.objects.all().delete()
            EdificioBloque.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Datos eliminados.'))

        # 1. Crear edificaciones
        self.stdout.write('Creando edificaciones del Centro Minero...')
        edificios_creados = 0
        for edif in EDIFICACIONES:
            obj, created = EdificioBloque.objects.get_or_create(
                nombre=edif['nombre'],
                defaults={
                    'descripcion': f'Edificacion {edif["id"]} del Centro Minero SENA',
                    'latitud': edif['lat'],
                    'longitud': edif['lng'],
                    'tipo': edif['tipo'],
                    'activo': True,
                }
            )
            if created:
                edificios_creados += 1
        self.stdout.write(self.style.SUCCESS(
            f'  {edificios_creados} edificaciones creadas ({len(EDIFICACIONES) - edificios_creados} ya existian)'
        ))

        # 2. Crear puntos de encuentro
        self.stdout.write('Creando puntos de encuentro...')
        puntos_objs = []
        puntos_creados = 0
        for pe in PUNTOS_ENCUENTRO:
            obj, created = PuntoEncuentro.objects.get_or_create(
                nombre=pe['nombre'],
                defaults={
                    'descripcion': pe['descripcion'],
                    'latitud': pe['latitud'],
                    'longitud': pe['longitud'],
                    'capacidad': pe['capacidad'],
                    'tipo_terreno': pe['tipo_terreno'],
                    'prioridad': pe['prioridad'],
                    'tiene_agua': pe['tiene_agua'],
                    'tiene_sombra': pe['tiene_sombra'],
                    'tiene_baños': pe['tiene_baños'],
                    'activo': True,
                }
            )
            puntos_objs.append(obj)
            if created:
                puntos_creados += 1
        self.stdout.write(self.style.SUCCESS(
            f'  {puntos_creados} puntos de encuentro creados ({len(PUNTOS_ENCUENTRO) - puntos_creados} ya existian)'
        ))

        # 3. Crear rutas de evacuación
        self.stdout.write('Creando rutas de evacuacion...')
        rutas_creadas = 0
        for ruta in RUTAS_EVACUACION:
            punto_fin = puntos_objs[ruta['punto_fin_idx']] if puntos_objs else None
            # Calcular inicio desde el primer waypoint
            inicio_lat = ruta['waypoints'][0][0]
            inicio_lng = ruta['waypoints'][0][1]

            obj, created = RutaEvacuacion.objects.get_or_create(
                nombre=ruta['nombre'],
                defaults={
                    'descripcion': ruta['descripcion'],
                    'inicio_latitud': inicio_lat,
                    'inicio_longitud': inicio_lng,
                    'punto_fin': punto_fin,
                    'distancia_metros': ruta['distancia_metros'],
                    'tiempo_estimado_minutos': ruta['tiempo_estimado_minutos'],
                    'waypoints': json.dumps(ruta['waypoints']),
                    'prioridad': ruta['prioridad'],
                    'activa': True,
                }
            )
            if created:
                rutas_creadas += 1
        self.stdout.write(self.style.SUCCESS(
            f'  {rutas_creadas} rutas de evacuacion creadas ({len(RUTAS_EVACUACION) - rutas_creadas} ya existian)'
        ))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            'Mapa del Centro Minero SENA poblado correctamente.'
        ))
        self.stdout.write(self.style.SUCCESS(
            'Accede a /mapas/ para ver el mapa interactivo o /mapas/plano/ para el plano.'
        ))

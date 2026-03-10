"""
Management command para poblar la base de datos con los datos reales
del Centro Minero SENA: edificaciones, puntos de encuentro y rutas de evacuación.

Uso:
    python manage.py poblar_mapa
    python manage.py poblar_mapa --reset   (borra y recrea todo)
"""
from django.core.management.base import BaseCommand
from mapas.models import EdificioBloque, PuntoEncuentro


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
        'latitud': 5.730056,
        'longitud': -72.894250,
        'capacidad': 200,
        'tipo_terreno': 'ABIERTO',
        'prioridad': 1,
        'tiene_agua': False,
        'tiene_sombra': False,
        'tiene_baños': False,
    },
    {
        'nombre': 'P2 - Zona Verde',
        'descripcion': 'Punto de encuentro secundario en la zona verde del centro',
        'latitud': 5.731083,
        'longitud': -72.895028,
        'capacidad': 150,
        'tipo_terreno': 'ABIERTO',
        'prioridad': 2,
        'tiene_agua': False,
        'tiene_sombra': False,
        'tiene_baños': False,
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
            if created:
                puntos_creados += 1
        self.stdout.write(self.style.SUCCESS(
            f'  {puntos_creados} puntos de encuentro creados ({len(PUNTOS_ENCUENTRO) - puntos_creados} ya existian)'
        ))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            'Mapa del Centro Minero SENA poblado correctamente.'
        ))
        self.stdout.write(self.style.SUCCESS(
            'Accede a /mapas/ para ver el mapa interactivo o /mapas/plano/ para el plano.'
        ))

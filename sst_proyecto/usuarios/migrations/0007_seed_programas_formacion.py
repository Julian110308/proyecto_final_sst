from django.db import migrations

PROGRAMAS_INICIALES = [
    "Analisis de Carbones y Minerales",
    "Analisis y Desarrollo de Software",
    "Ambiental",
    "Construccion de Infraestructura Vial",
    "Control de Movilidad Transporte y Seguridad",
    "Levantamiento Topografico y Georeferenciacion",
    "Mantenimiento de Equipo Pesado para Infraestructura y Transporte",
    "Mantenimiento e Instalacion de Sistemas Solares Fotovoltaicos",
    "Maquinaria Pesada",
    "Perforacion y Voladura",
    "Prevencion y Control Ambiental",
    "Procesos de la Industria Quimica",
    "Programacion de Software",
    "Promotoria en Manejo Ambiental",
    "Quimica",
    "Quimica Aplicada a la Industria",
    "Retroexcavadoras",
    "Seguridad y Salud en el Trabajo",
    "Supervision de Procesos Mineros",
    "Supervision en Sistemas de Agua y Saneamiento",
]


def seed_programas(apps, schema_editor):
    ProgramaFormacion = apps.get_model("usuarios", "ProgramaFormacion")
    for nombre in PROGRAMAS_INICIALES:
        ProgramaFormacion.objects.get_or_create(nombre=nombre)


def unseed_programas(apps, schema_editor):
    ProgramaFormacion = apps.get_model("usuarios", "ProgramaFormacion")
    ProgramaFormacion.objects.filter(nombre__in=PROGRAMAS_INICIALES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0006_add_programa_formacion_model"),
    ]

    operations = [
        migrations.RunPython(seed_programas, unseed_programas),
    ]

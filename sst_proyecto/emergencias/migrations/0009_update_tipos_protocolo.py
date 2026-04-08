from django.db import migrations

# Tipos sistémicos: solo coordinador/admin los activa, alertan a TODOS
TIPOS_PROTOCOLO = ["Sismo", "Incendio", "Derrame Quimico"]

# Tipos nuevos a crear si no existen
TIPOS_NUEVOS = [
    {
        "nombre": "Deslizamiento",
        "descripcion": "Deslizamiento de tierra o derrumbe en el centro.",
        "color": "#8B4513",
        "icono": "landslide",
        "prioridad": 1,
        "protocolo": "Evacuar zona afectada. Alejarse de taludes y estructuras inestables. Activar protocolo de evacuación general.",
        "tiempo_respuesta_minutos": 3,
        "solo_autorizado": True,
        "alerta_masiva": True,
    },
]


def update_tipos(apps, schema_editor):
    TipoEmergencia = apps.get_model("emergencias", "TipoEmergencia")

    # Marcar tipos existentes como protocolo
    TipoEmergencia.objects.filter(nombre__in=TIPOS_PROTOCOLO).update(
        solo_autorizado=True, alerta_masiva=True
    )

    # Crear tipos nuevos si no existen
    for datos in TIPOS_NUEVOS:
        TipoEmergencia.objects.get_or_create(
            nombre=datos["nombre"],
            defaults=datos,
        )


def revert_tipos(apps, schema_editor):
    TipoEmergencia = apps.get_model("emergencias", "TipoEmergencia")
    TipoEmergencia.objects.filter(nombre__in=TIPOS_PROTOCOLO).update(
        solo_autorizado=False, alerta_masiva=False
    )
    TipoEmergencia.objects.filter(nombre__in=[t["nombre"] for t in TIPOS_NUEVOS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("emergencias", "0008_seed_tipos_emergencia_flags"),
    ]

    operations = [
        migrations.RunPython(update_tipos, revert_tipos),
    ]

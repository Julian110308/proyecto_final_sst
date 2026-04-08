from django.db import migrations

# Tipos que solo personal autorizado puede reportar Y que disparan alerta a todos los usuarios
TIPOS_MASIVOS = ["Sismo"]

# Tipos que solo personal autorizado puede reportar (sin alerta masiva)
TIPOS_SOLO_AUTORIZADO = ["Derrame Quimico"]


def set_flags(apps, schema_editor):
    TipoEmergencia = apps.get_model("emergencias", "TipoEmergencia")
    TipoEmergencia.objects.filter(nombre__in=TIPOS_MASIVOS).update(
        solo_autorizado=True, alerta_masiva=True
    )
    TipoEmergencia.objects.filter(nombre__in=TIPOS_SOLO_AUTORIZADO).update(
        solo_autorizado=True, alerta_masiva=False
    )


def unset_flags(apps, schema_editor):
    TipoEmergencia = apps.get_model("emergencias", "TipoEmergencia")
    TipoEmergencia.objects.filter(nombre__in=TIPOS_MASIVOS + TIPOS_SOLO_AUTORIZADO).update(
        solo_autorizado=False, alerta_masiva=False
    )


class Migration(migrations.Migration):

    dependencies = [
        ("emergencias", "0007_add_solo_autorizado_alerta_masiva"),
    ]

    operations = [
        migrations.RunPython(set_flags, unset_flags),
    ]

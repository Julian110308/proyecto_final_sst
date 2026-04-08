from django.db import migrations

# Solo los desastres naturales son de activación restringida a Brigada
# Incendio y Derrame Químico los puede reportar cualquier usuario
TIPOS_TODOS_PUEDEN_REPORTAR = ["Incendio", "Derrame Quimico"]
TIPOS_SOLO_BRIGADA = ["Sismo", "Deslizamiento"]


def fix_flags(apps, schema_editor):
    TipoEmergencia = apps.get_model("emergencias", "TipoEmergencia")

    # Incendio y Derrame: cualquier usuario puede reportarlos
    TipoEmergencia.objects.filter(nombre__in=TIPOS_TODOS_PUEDEN_REPORTAR).update(
        solo_autorizado=False, alerta_masiva=False
    )

    # Sismo y Deslizamiento: solo Brigada, notifican a todos
    TipoEmergencia.objects.filter(nombre__in=TIPOS_SOLO_BRIGADA).update(
        solo_autorizado=True, alerta_masiva=True
    )


def revert_flags(apps, schema_editor):
    TipoEmergencia = apps.get_model("emergencias", "TipoEmergencia")
    TipoEmergencia.objects.filter(nombre__in=TIPOS_TODOS_PUEDEN_REPORTAR).update(
        solo_autorizado=True, alerta_masiva=True
    )


class Migration(migrations.Migration):

    dependencies = [
        ("emergencias", "0009_update_tipos_protocolo"),
    ]

    operations = [
        migrations.RunPython(fix_flags, revert_flags),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("control_acceso", "0009_add_qr_metodo_deteccion"),
    ]

    operations = [
        # Eliminar campos GPS de RegistroAcceso
        migrations.RemoveField(
            model_name="registroacceso",
            name="latitud_ingreso",
        ),
        migrations.RemoveField(
            model_name="registroacceso",
            name="longitud_ingreso",
        ),
        migrations.RemoveField(
            model_name="registroacceso",
            name="latitud_egreso",
        ),
        migrations.RemoveField(
            model_name="registroacceso",
            name="longitud_egreso",
        ),
        # Actualizar choices del método de detección
        migrations.AlterField(
            model_name="registroacceso",
            name="metodo_ingreso",
            field=models.CharField(
                choices=[("MANUAL", "Detección manual"), ("QR", "Código QR")],
                default="MANUAL",
                max_length=15,
            ),
        ),
        migrations.AlterField(
            model_name="registroacceso",
            name="metodo_egreso",
            field=models.CharField(
                choices=[("MANUAL", "Detección manual"), ("QR", "Código QR")],
                max_length=15,
                null=True,
                blank=True,
            ),
        ),
        # Eliminar modelo Geocerca
        migrations.DeleteModel(
            name="Geocerca",
        ),
    ]

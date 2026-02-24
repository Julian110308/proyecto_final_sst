from django.core.validators import MinValueValidator
from django.db import migrations, models


def actualizar_radio_geocercas(apps, schema_editor):
    """Actualiza geocercas con radio <= 200m (valor por defecto anterior) a 400m."""
    Geocerca = apps.get_model('control_acceso', 'Geocerca')
    Geocerca.objects.filter(radio_metros__lte=200).update(radio_metros=400)


class Migration(migrations.Migration):

    dependencies = [
        ('control_acceso', '0005_alter_registroacceso_metodo_egreso_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='geocerca',
            name='radio_metros',
            field=models.IntegerField(
                default=400,
                validators=[MinValueValidator(1)],
                help_text='Radio en metros (mínimo 1 metro)',
            ),
        ),
        migrations.RunPython(actualizar_radio_geocercas, migrations.RunPython.noop),
    ]

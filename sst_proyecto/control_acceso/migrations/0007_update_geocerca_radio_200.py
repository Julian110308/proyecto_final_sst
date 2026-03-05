from django.core.validators import MinValueValidator
from django.db import migrations, models


def reducir_radio_a_200(apps, schema_editor):
    Geocerca = apps.get_model('control_acceso', 'Geocerca')
    Geocerca.objects.all().update(radio_metros=200)


class Migration(migrations.Migration):

    dependencies = [
        ('control_acceso', '0006_update_geocerca_radio_default'),
    ]

    operations = [
        migrations.AlterField(
            model_name='geocerca',
            name='radio_metros',
            field=models.IntegerField(
                default=200,
                validators=[MinValueValidator(1)],
                help_text='Radio en metros (mínimo 1 metro)',
            ),
        ),
        migrations.RunPython(reducir_radio_a_200, migrations.RunPython.noop),
    ]

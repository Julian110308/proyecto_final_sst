from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0003_add_push_subscripcion'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='fichas_asignadas',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Números de ficha separados por coma (solo instructores)',
                verbose_name='Fichas asignadas',
            ),
        ),
    ]

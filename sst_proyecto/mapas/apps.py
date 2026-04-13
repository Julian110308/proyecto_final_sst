from django.apps import AppConfig


class MapasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mapas"

    def ready(self):
        import sys

        # No iniciar el scheduler en comandos de management ni en tests
        if "runserver" not in sys.argv and "daphne" not in sys.argv[0]:
            return
        from mapas.scheduler import iniciar_scheduler

        iniciar_scheduler()

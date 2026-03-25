from django.apps import AppConfig


class EmergenciasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "emergencias"

    def ready(self):
        from auditlog.registry import auditlog
        from .models import BrigadaEmergencia, Emergencia

        auditlog.register(Emergencia)
        auditlog.register(BrigadaEmergencia)

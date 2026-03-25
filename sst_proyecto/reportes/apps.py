from django.apps import AppConfig


class ReportesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reportes"

    def ready(self):
        from auditlog.registry import auditlog
        from .models import Incidente

        auditlog.register(Incidente)

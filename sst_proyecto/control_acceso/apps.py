from django.apps import AppConfig


class ControlAccesoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "control_acceso"

    def ready(self):
        from auditlog.registry import auditlog
        from .models import ConfiguracionAforo, Geocerca, RegistroAcceso

        auditlog.register(RegistroAcceso)
        auditlog.register(ConfiguracionAforo)
        auditlog.register(Geocerca)

        import control_acceso.signals  # noqa: F401

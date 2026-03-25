from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "usuarios"

    def ready(self):
        from auditlog.registry import auditlog
        from .models import Usuario

        # Excluir campos de sesión que cambian en cada login (no aportan trazabilidad)
        auditlog.register(Usuario, exclude_fields=["last_login", "password"])

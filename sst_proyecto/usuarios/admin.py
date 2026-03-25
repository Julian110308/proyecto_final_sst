from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from auditlog.admin import LogEntryAdmin
from auditlog.models import LogEntry
from .models import Usuario, Visitante


# Personalizar el admin de auditoría ya registrado por django-auditlog
admin.site.unregister(LogEntry)


@admin.register(LogEntry)
class AuditoriaAdmin(LogEntryAdmin):
    """Registro de auditoría: quién cambió qué y cuándo en modelos críticos."""

    list_display = ["timestamp", "actor", "action", "content_type", "object_repr"]
    list_filter = ["action", "content_type", "timestamp"]
    search_fields = ["actor__username", "object_repr", "changes"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ["username", "first_name", "last_name", "rol", "numero_documento", "activo"]
    list_filter = ["rol", "activo", "is_staff"]
    search_fields = ["username", "first_name", "last_name", "numero_documento"]

    fieldsets = UserAdmin.fieldsets + (
        (
            "Información Adicional",
            {
                "fields": (
                    "rol",
                    "tipo_documento",
                    "numero_documento",
                    "telefono",
                    "telefono_emergencia",
                    "contacto_emergencia",
                    "foto",
                )
            },
        ),
        ("Información Académica", {"fields": ("ficha", "programa_formacion")}),
        ("Control", {"fields": ("activo",)}),
    )


@admin.register(Visitante)
class VisitanteAdmin(admin.ModelAdmin):
    list_display = ["nombre_completo", "numero_documento", "persona_a_visitar", "fecha_visita", "activo"]
    list_filter = ["fecha_visita", "activo"]
    search_fields = ["nombre_completo", "numero_documento"]

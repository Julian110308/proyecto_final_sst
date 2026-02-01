from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Visitante

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'rol', 'numero_documento', 'activo']
    list_filter = ['rol', 'activo', 'is_staff']
    search_fields = ['username', 'first_name', 'last_name', 'numero_documento']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': (
                'rol', 'tipo_documento', 'numero_documento',
                'telefono', 'telefono_emergencia', 'contacto_emergencia', 'foto'
            )
        }),
        ('Información Académica', {
            'fields': ('ficha', 'programa_formacion')
        }),
        ('Control', {
            'fields': ('activo',)
        }),
    )

@admin.register(Visitante)
class VisitanteAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'numero_documento', 'persona_a_visitar', 'fecha_visita', 'activo']
    list_filter = ['fecha_visita', 'activo']
    search_fields = ['nombre_completo', 'numero_documento']
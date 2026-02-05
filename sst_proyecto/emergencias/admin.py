from django.contrib import admin
from .models import (
    TipoEmergencia,
    Emergencia,
    BrigadaEmergencia,
    NotificacionEmergencia,
    ContactoExterno,
)

@admin.register(TipoEmergencia)
class TipoEmergenciaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'prioridad', 'tiempo_respuesta_minutos', 'activo']
    list_filter = ['prioridad', 'activo']
    search_fields = ['nombre']

@admin.register(Emergencia)
class EmergenciaAdmin(admin.ModelAdmin):
    list_display = [
        'tipo', 'reportada_por', 'estado',
        'fecha_hora_reporte', 'personas_afectadas'
    ]
    list_filter = ['estado', 'tipo', 'fecha_hora_reporte']
    search_fields = ['descripcion']
    readonly_fields = ['fecha_hora_reporte']

@admin.register(BrigadaEmergencia)
class BrigadaEmergenciaAdmin(admin.ModelAdmin):
    list_display = [
        'usuario', 'especializacion', 'nivel_certificacion',
        'activo', 'disponible'
    ]
    list_filter = ['especializacion', 'nivel_certificacion', 'activo']

@admin.register(ContactoExterno)
class ContactoExternoAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'entidad', 'tipo', 'telefono_principal', 'activo'
    ]
    list_filter = ['tipo', 'activo']
    search_fields = ['nombre', 'entidad']

@admin.register(NotificacionEmergencia)
class NotificacionEmergenciaAdmin(admin.ModelAdmin):
    list_display = ['emergencia', 'destinatario', 'tipo_notificacion', 'fecha_envio', 'leida']
    list_filter = ['tipo_notificacion', 'leida', 'fecha_envio']
    readonly_fields = ['fecha_envio']
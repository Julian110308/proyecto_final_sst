from django.contrib import admin
from .models import ConfiguracionReporte, ReporteGenerado, Incidente

@admin.register(ConfiguracionReporte)
class ConfiguracionReporteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_reporte', 'frecuencia', 'activo', 'ultima_generacion']
    list_filter = ['tipo_reporte', 'frecuencia', 'activo']
    search_fields = ['nombre']
    filter_horizontal = ['destinatarios']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es nuevo
            obj.generado_por = request.user
        super().save_model(request, obj, form, change)

@admin.register(ReporteGenerado)
class ReporteGeneradoAdmin(admin.ModelAdmin):
    list_display = ['configuracion', 'fecha_generacion', 'periodo_inicio', 'periodo_fin', 'generado_por']
    list_filter = ['fecha_generacion', 'configuracion__tipo_reporte']
    readonly_fields = ['fecha_generacion']
    search_fields = ['configuracion__nombre']
    
    def has_add_permission(self, request):
        return False  # No permitir agregar manualmente


# Admin SIMPLE para Incidentes
@admin.register(Incidente)
class IncidenteAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'gravedad', 'estado', 'reportado_por', 'fecha_reporte']
    list_filter = ['tipo', 'gravedad', 'estado', 'fecha_reporte']
    search_fields = ['titulo', 'descripcion', 'ubicacion']
    readonly_fields = ['fecha_reporte']

    fieldsets = (
        ('Información Básica', {
            'fields': ('titulo', 'descripcion', 'tipo', 'gravedad', 'estado')
        }),
        ('Ubicación y Fecha', {
            'fields': ('ubicacion', 'fecha_incidente', 'fecha_reporte')
        }),
        ('Responsables', {
            'fields': ('reportado_por', 'asignado_a')
        }),
        ('Evidencia y Acciones', {
            'fields': ('foto', 'acciones_tomadas', 'fecha_resolucion')
        }),
    )
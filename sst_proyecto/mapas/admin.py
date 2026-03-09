from django.contrib import admin
from .models import EdificioBloque, PuntoEncuentro, EquipamientoSeguridad, RutaEvacuacion


@admin.register(PuntoEncuentro)
class PuntoEncuentroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'prioridad', 'latitud', 'longitud', 'capacidad', 'activo')
    list_editable = ('latitud', 'longitud', 'activo')
    list_display_links = ('nombre',)
    ordering = ('prioridad',)
    search_fields = ('nombre', 'descripcion')
    list_filter = ('activo', 'tipo_terreno')
    fields = ('nombre', 'descripcion', 'latitud', 'longitud', 'capacidad',
              'tipo_terreno', 'prioridad', 'tiene_agua', 'tiene_sombra', 'tiene_baños', 'activo')


@admin.register(EquipamientoSeguridad)
class EquipamientoSeguridadAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'tipo', 'estado', 'latitud', 'longitud', 'activo')
    list_editable = ('latitud', 'longitud')
    list_display_links = ('codigo',)
    ordering = ('tipo', 'codigo')
    search_fields = ('codigo', 'descripcion')
    list_filter = ('tipo', 'estado', 'activo')


@admin.register(EdificioBloque)
class EdificioBloqueAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'latitud', 'longitud', 'activo')
    list_editable = ('latitud', 'longitud')
    list_display_links = ('nombre',)
    ordering = ('nombre',)
    list_filter = ('tipo', 'activo')

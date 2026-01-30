# Formulario SIMPLE para reportar incidentes
from django import forms
from .models import Incidente

class IncidenteForm(forms.ModelForm):
    """
    Formulario básico para reportar un incidente
    Solo los campos esenciales para el usuario
    """

    class Meta:
        model = Incidente
        fields = ['titulo', 'descripcion', 'tipo', 'gravedad', 'ubicacion', 'fecha_incidente', 'foto']

        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Goteo en techo del taller'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe qué pasó, cómo pasó, consecuencias...'
            }),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'gravedad': forms.Select(attrs={'class': 'form-select'}),
            'ubicacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Taller de mecánica, Bloque A piso 2'
            }),
            'fecha_incidente': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'foto': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

        labels = {
            'titulo': 'Título del Incidente',
            'descripcion': 'Descripción Detallada',
            'tipo': 'Tipo de Incidente',
            'gravedad': 'Nivel de Gravedad',
            'ubicacion': 'Ubicación',
            'fecha_incidente': 'Fecha y Hora del Incidente',
            'foto': 'Foto (Evidencia)'
        }

        help_texts = {
            'titulo': 'Breve resumen del incidente',
            'descripcion': 'Explica qué ocurrió con el mayor detalle posible',
            'foto': 'Opcional: Adjunta una foto si es posible'
        }

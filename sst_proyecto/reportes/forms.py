# Formulario SIMPLE para reportar incidentes
from django import forms
from django.core.validators import FileExtensionValidator
from django.utils.html import strip_tags
import re
from .models import Incidente


def sanitizar_texto(texto):
    """
    Sanitiza texto para prevenir XSS y otros ataques.
    - Elimina tags HTML
    - Elimina caracteres de control
    - Limita longitud excesiva
    """
    if not texto:
        return texto

    # Eliminar tags HTML
    texto = strip_tags(texto)

    # Eliminar caracteres de control (excepto saltos de línea y tabs)
    texto = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', texto)

    return texto.strip()


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
                'placeholder': 'Ej: Goteo en techo del taller',
                'maxlength': '200'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe qué pasó, cómo pasó, consecuencias...',
                'maxlength': '2000'
            }),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'gravedad': forms.Select(attrs={'class': 'form-select'}),
            'ubicacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Taller de mecánica, Bloque A piso 2',
                'maxlength': '200'
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
            'titulo': 'Breve resumen del incidente (máx. 200 caracteres)',
            'descripcion': 'Explica qué ocurrió con el mayor detalle posible',
            'foto': 'Opcional: Adjunta una foto (JPG, PNG, máx. 5MB)'
        }

    def clean_titulo(self):
        """Sanitiza y valida el título"""
        titulo = self.cleaned_data.get('titulo', '')
        titulo = sanitizar_texto(titulo)

        if len(titulo) < 5:
            raise forms.ValidationError('El título debe tener al menos 5 caracteres.')

        if len(titulo) > 200:
            raise forms.ValidationError('El título no puede exceder 200 caracteres.')

        return titulo

    def clean_descripcion(self):
        """Sanitiza y valida la descripción"""
        descripcion = self.cleaned_data.get('descripcion', '')
        descripcion = sanitizar_texto(descripcion)

        if len(descripcion) < 10:
            raise forms.ValidationError('La descripción debe tener al menos 10 caracteres.')

        if len(descripcion) > 2000:
            raise forms.ValidationError('La descripción no puede exceder 2000 caracteres.')

        return descripcion

    def clean_ubicacion(self):
        """Sanitiza y valida la ubicación"""
        ubicacion = self.cleaned_data.get('ubicacion', '')
        if ubicacion:
            ubicacion = sanitizar_texto(ubicacion)
            if len(ubicacion) > 200:
                raise forms.ValidationError('La ubicación no puede exceder 200 caracteres.')
        return ubicacion

    def clean_foto(self):
        """Valida el archivo de foto"""
        foto = self.cleaned_data.get('foto')

        if foto:
            # Validar tamaño (máx 5MB)
            if foto.size > 5 * 1024 * 1024:
                raise forms.ValidationError('La imagen no puede superar 5MB.')

            # Validar extensión
            ext = foto.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                raise forms.ValidationError('Solo se permiten imágenes (JPG, PNG, GIF, WEBP).')

            # Validar tipo MIME
            content_type = foto.content_type
            if content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                raise forms.ValidationError('El archivo no es una imagen válida.')

        return foto

    def clean_fecha_incidente(self):
        """Valida la fecha del incidente"""
        from django.utils import timezone

        fecha = self.cleaned_data.get('fecha_incidente')

        if fecha:
            # No puede ser en el futuro
            if fecha > timezone.now():
                raise forms.ValidationError('La fecha del incidente no puede ser en el futuro.')

            # No puede ser muy antigua (más de 1 año)
            hace_un_año = timezone.now() - timezone.timedelta(days=365)
            if fecha < hace_un_año:
                raise forms.ValidationError('La fecha del incidente no puede ser hace más de 1 año.')

        return fecha

# Formulario para reportar incidentes
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
    Formulario completo para reportar un incidente.
    Incluye fecha/hora/lugar, testigos, persona afectada,
    area, riesgos, version del accidente y foto obligatoria.
    """

    class Meta:
        model = Incidente
        fields = [
            'titulo', 'tipo', 'gravedad',
            'fecha_incidente', 'lugar_exacto', 'area_incidente', 'ubicacion',
            'latitud', 'longitud',
            'persona_afectada', 'documento_afectado', 'rol_afectado',
            'descripcion', 'version_accidente',
            'riesgos_identificados',
            'testigos',
            'foto',
        ]

        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Caida en taller de soldadura',
                'maxlength': '200'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe brevemente que paso...',
                'maxlength': '2000'
            }),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'gravedad': forms.Select(attrs={'class': 'form-select'}),
            'area_incidente': forms.Select(attrs={'class': 'form-select'}),
            'ubicacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Bloque A, Piso 2',
                'maxlength': '200'
            }),
            'lugar_exacto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Junto a la fresadora #3, esquina noreste del taller',
                'maxlength': '300'
            }),
            'fecha_incidente': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'persona_afectada': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo de la persona afectada',
                'maxlength': '200'
            }),
            'documento_afectado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numero de documento',
                'maxlength': '20'
            }),
            'rol_afectado': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('', 'Seleccione...'),
                ('APRENDIZ', 'Aprendiz'),
                ('INSTRUCTOR', 'Instructor'),
                ('ADMINISTRATIVO', 'Administrativo'),
                ('VIGILANCIA', 'Vigilancia'),
                ('BRIGADA', 'Brigada'),
                ('VISITANTE', 'Visitante'),
                ('OTRO', 'Otro'),
            ]),
            'version_accidente': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Relato detallado: como ocurrio el accidente, que estaba haciendo la persona, condiciones del area...',
                'maxlength': '3000'
            }),
            'riesgos_identificados': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ej: Piso mojado, cables expuestos, falta de señalizacion, maquinaria sin proteccion...',
                'maxlength': '2000'
            }),
            'testigos': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Nombre completo y documento de cada testigo (uno por linea)',
                'maxlength': '1000'
            }),
            'foto': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'latitud': forms.HiddenInput(),
            'longitud': forms.HiddenInput(),
        }

        labels = {
            'titulo': 'Titulo del Incidente',
            'descripcion': 'Descripcion del Incidente',
            'tipo': 'Tipo de Incidente',
            'gravedad': 'Nivel de Gravedad',
            'area_incidente': 'Area del Incidente',
            'ubicacion': 'Ubicacion General',
            'lugar_exacto': 'Lugar Exacto',
            'fecha_incidente': 'Fecha y Hora del Incidente',
            'persona_afectada': 'Nombre de la Persona Afectada',
            'documento_afectado': 'Documento de la Persona Afectada',
            'rol_afectado': 'Rol de la Persona Afectada',
            'version_accidente': 'Version del Accidente',
            'riesgos_identificados': 'Riesgos Identificados en el Area',
            'testigos': 'Testigos del Incidente',
            'foto': 'Foto de Evidencia (Obligatoria)',
        }

        help_texts = {
            'titulo': 'Breve resumen del incidente (max. 200 caracteres)',
            'descripcion': 'Explica que ocurrio con el mayor detalle posible',
            'foto': 'Adjunta una foto del lugar o la situacion (JPG, PNG, max. 5MB)',
            'testigos': 'Incluye nombre y documento de cada testigo presente',
            'version_accidente': 'Relato detallado del accidente segun los involucrados',
            'riesgos_identificados': 'Identifica los posibles riesgos presentes en el area',
        }

    def clean_titulo(self):
        titulo = self.cleaned_data.get('titulo', '')
        titulo = sanitizar_texto(titulo)
        if len(titulo) < 5:
            raise forms.ValidationError('El titulo debe tener al menos 5 caracteres.')
        if len(titulo) > 200:
            raise forms.ValidationError('El titulo no puede exceder 200 caracteres.')
        return titulo

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get('descripcion', '')
        descripcion = sanitizar_texto(descripcion)
        if len(descripcion) < 10:
            raise forms.ValidationError('La descripcion debe tener al menos 10 caracteres.')
        if len(descripcion) > 2000:
            raise forms.ValidationError('La descripcion no puede exceder 2000 caracteres.')
        return descripcion

    def clean_ubicacion(self):
        ubicacion = self.cleaned_data.get('ubicacion', '')
        if ubicacion:
            ubicacion = sanitizar_texto(ubicacion)
            if len(ubicacion) > 200:
                raise forms.ValidationError('La ubicacion no puede exceder 200 caracteres.')
        return ubicacion

    def clean_lugar_exacto(self):
        lugar = self.cleaned_data.get('lugar_exacto', '')
        if lugar:
            lugar = sanitizar_texto(lugar)
            if len(lugar) > 300:
                raise forms.ValidationError('El lugar exacto no puede exceder 300 caracteres.')
        return lugar

    def clean_testigos(self):
        testigos = self.cleaned_data.get('testigos', '')
        if testigos:
            testigos = sanitizar_texto(testigos)
            if len(testigos) > 1000:
                raise forms.ValidationError('La informacion de testigos no puede exceder 1000 caracteres.')
        return testigos

    def clean_persona_afectada(self):
        persona = self.cleaned_data.get('persona_afectada', '')
        if persona:
            persona = sanitizar_texto(persona)
            if len(persona) > 200:
                raise forms.ValidationError('El nombre no puede exceder 200 caracteres.')
        return persona

    def clean_version_accidente(self):
        version = self.cleaned_data.get('version_accidente', '')
        if version:
            version = sanitizar_texto(version)
            if len(version) > 3000:
                raise forms.ValidationError('La version del accidente no puede exceder 3000 caracteres.')
        return version

    def clean_riesgos_identificados(self):
        riesgos = self.cleaned_data.get('riesgos_identificados', '')
        if riesgos:
            riesgos = sanitizar_texto(riesgos)
            if len(riesgos) > 2000:
                raise forms.ValidationError('Los riesgos identificados no pueden exceder 2000 caracteres.')
        return riesgos

    def clean_foto(self):
        foto = self.cleaned_data.get('foto')

        if not foto:
            raise forms.ValidationError('La foto de evidencia es obligatoria. Adjunta una imagen del incidente.')

        # Validar tamaño (max 5MB)
        if foto.size > 5 * 1024 * 1024:
            raise forms.ValidationError('La imagen no puede superar 5MB.')

        # Validar extensión
        ext = foto.name.split('.')[-1].lower()
        if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            raise forms.ValidationError('Solo se permiten imagenes (JPG, PNG, GIF, WEBP).')

        # Validar tipo MIME
        content_type = foto.content_type
        if content_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
            raise forms.ValidationError('El archivo no es una imagen valida.')

        return foto

    def clean_fecha_incidente(self):
        from django.utils import timezone

        fecha = self.cleaned_data.get('fecha_incidente')

        if fecha:
            if fecha > timezone.now():
                raise forms.ValidationError('La fecha del incidente no puede ser en el futuro.')
            hace_un_año = timezone.now() - timezone.timedelta(days=365)
            if fecha < hace_un_año:
                raise forms.ValidationError('La fecha del incidente no puede ser hace mas de 1 año.')

        return fecha

# Formulario para reportar incidentes
from django import forms
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
    texto = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", texto)

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
            "titulo",
            "tipo",
            "gravedad",
            "fecha_incidente",
            "lugar_exacto",
            "area_incidente",
            "ubicacion",
            "latitud",
            "longitud",
            "personas_afectadas",
            "descripcion",
            "riesgos_identificados",
            "testigos",
            "foto",
        ]

        widgets = {
            "titulo": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej: Caida en taller de soldadura", "maxlength": "200"}
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Describe brevemente que paso...",
                    "maxlength": "2000",
                }
            ),
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "gravedad": forms.Select(attrs={"class": "form-select"}),
            "area_incidente": forms.Select(attrs={"class": "form-select"}),
            "ubicacion": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej: Bloque A, Piso 2", "maxlength": "200"}
            ),
            "lugar_exacto": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej: Junto a la fresadora #3, esquina noreste del taller",
                    "maxlength": "300",
                }
            ),
            "fecha_incidente": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "personas_afectadas": forms.HiddenInput(),
            "riesgos_identificados": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Ej: Piso mojado, cables expuestos, falta de señalizacion, maquinaria sin proteccion...",
                    "maxlength": "2000",
                }
            ),
            "foto": forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "latitud": forms.HiddenInput(),
            "longitud": forms.HiddenInput(),
            "testigos": forms.HiddenInput(),
        }

        labels = {
            "titulo": "Titulo del Incidente",
            "descripcion": "Descripcion del Incidente",
            "tipo": "Tipo de Incidente",
            "gravedad": "Nivel de Gravedad",
            "area_incidente": "Area del Incidente",
            "ubicacion": "Ubicacion General",
            "lugar_exacto": "Lugar Exacto",
            "fecha_incidente": "Fecha y Hora del Incidente",
            "personas_afectadas": "Personas Afectadas",
            "riesgos_identificados": "Riesgos Identificados en el Area",
            "testigos": "Testigos del Incidente",
            "foto": "Foto de Evidencia (Obligatoria)",
        }

        help_texts = {
            "titulo": "Breve resumen del incidente (max. 200 caracteres)",
            "descripcion": "Explica que ocurrio con el mayor detalle posible",
            "foto": "Adjunta una foto del lugar o la situacion (JPG, PNG, max. 5MB)",
            "testigos": "Incluye nombre y documento de cada testigo presente",
            "riesgos_identificados": "Identifica los posibles riesgos presentes en el area",
        }

    def clean_titulo(self):
        titulo = self.cleaned_data.get("titulo", "")
        titulo = sanitizar_texto(titulo)
        if len(titulo) < 5:
            raise forms.ValidationError("El titulo debe tener al menos 5 caracteres.")
        if len(titulo) > 200:
            raise forms.ValidationError("El titulo no puede exceder 200 caracteres.")
        return titulo

    def clean_descripcion(self):
        descripcion = self.cleaned_data.get("descripcion", "")
        descripcion = sanitizar_texto(descripcion)
        if len(descripcion) < 10:
            raise forms.ValidationError("La descripcion debe tener al menos 10 caracteres.")
        if len(descripcion) > 2000:
            raise forms.ValidationError("La descripcion no puede exceder 2000 caracteres.")
        return descripcion

    def clean_ubicacion(self):
        ubicacion = self.cleaned_data.get("ubicacion", "")
        if ubicacion:
            ubicacion = sanitizar_texto(ubicacion)
            if len(ubicacion) > 200:
                raise forms.ValidationError("La ubicacion no puede exceder 200 caracteres.")
        return ubicacion

    def clean_lugar_exacto(self):
        lugar = self.cleaned_data.get("lugar_exacto", "")
        if lugar:
            lugar = sanitizar_texto(lugar)
            if len(lugar) > 300:
                raise forms.ValidationError("El lugar exacto no puede exceder 300 caracteres.")
        return lugar

    def clean_testigos(self):
        import json as _json

        testigos_raw = self.cleaned_data.get("testigos", "")
        if not testigos_raw:
            return ""
        try:
            lista = _json.loads(testigos_raw)
        except (ValueError, TypeError):
            raise forms.ValidationError("Formato de testigos inválido.")
        if not isinstance(lista, list):
            raise forms.ValidationError("Formato de testigos inválido.")

        TIPOS_DOC = {"CC", "TI", "CE", "PAS"}
        ROLES = {"APRENDIZ", "INSTRUCTOR", "COORDINADOR_SST", "VIGILANCIA", "BRIGADA", "VISITANTE", "OTRO"}
        REGLAS_DOC = {
            "CC": {"min": 8, "max": 10, "solo_numeros": True},
            "TI": {"min": 8, "max": 10, "solo_numeros": True},
            "CE": {"min": 6, "max": 12, "solo_numeros": False},
            "PAS": {"min": 5, "max": 20, "solo_numeros": False},
        }

        resultado = []
        for i, t in enumerate(lista, 1):
            if not isinstance(t, dict):
                raise forms.ValidationError(f"Testigo #{i}: formato inválido.")
            nombre = sanitizar_texto(t.get("nombre", "").strip())
            tipo_doc = t.get("tipo_doc", "CC").strip().upper()
            num_doc = t.get("numero_doc", "").strip()
            rol = t.get("rol", "OTRO").strip().upper()

            if not nombre:
                raise forms.ValidationError(f"Testigo #{i}: el nombre es obligatorio.")
            if len(nombre) > 200:
                raise forms.ValidationError(f"Testigo #{i}: el nombre no puede exceder 200 caracteres.")
            if tipo_doc not in TIPOS_DOC:
                raise forms.ValidationError(f"Testigo #{i}: tipo de documento inválido.")
            if num_doc:
                regla = REGLAS_DOC[tipo_doc]
                if regla["solo_numeros"] and not num_doc.isdigit():
                    raise forms.ValidationError(f"Testigo #{i}: el documento solo puede contener dígitos.")
                if not num_doc.isalnum():
                    raise forms.ValidationError(f"Testigo #{i}: el documento solo puede contener letras y números.")
                if len(num_doc) < regla["min"] or len(num_doc) > regla["max"]:
                    raise forms.ValidationError(
                        f"Testigo #{i}: el documento debe tener entre {regla['min']} y {regla['max']} caracteres."
                    )
            if rol not in ROLES:
                rol = "OTRO"
            resultado.append({"nombre": nombre, "tipo_doc": tipo_doc, "numero_doc": num_doc, "rol": rol})

        return _json.dumps(resultado, ensure_ascii=False)

    def clean_personas_afectadas(self):
        import json as _json

        raw = self.cleaned_data.get("personas_afectadas", "")
        if not raw:
            return ""
        try:
            lista = _json.loads(raw)
        except (ValueError, TypeError):
            raise forms.ValidationError("Formato de personas afectadas inválido.")
        if not isinstance(lista, list):
            raise forms.ValidationError("Formato de personas afectadas inválido.")

        TIPOS_DOC = {"CC", "TI", "CE", "PAS"}
        ROLES = {"APRENDIZ", "INSTRUCTOR", "COORDINADOR_SST", "VIGILANCIA", "BRIGADA", "VISITANTE", "OTRO"}
        REGLAS_DOC = {
            "CC": {"min": 8, "max": 10, "solo_numeros": True},
            "TI": {"min": 8, "max": 10, "solo_numeros": True},
            "CE": {"min": 6, "max": 12, "solo_numeros": False},
            "PAS": {"min": 5, "max": 20, "solo_numeros": False},
        }
        resultado = []
        for i, p in enumerate(lista, 1):
            if not isinstance(p, dict):
                raise forms.ValidationError(f"Persona #{i}: formato inválido.")
            nombre = sanitizar_texto(p.get("nombre", "").strip())
            tipo_doc = p.get("tipo_doc", "CC").strip().upper()
            num_doc = p.get("numero_doc", "").strip()
            rol = p.get("rol", "OTRO").strip().upper()
            if not nombre:
                raise forms.ValidationError(f"Persona afectada #{i}: el nombre es obligatorio.")
            if len(nombre) > 200:
                raise forms.ValidationError(f"Persona afectada #{i}: el nombre no puede exceder 200 caracteres.")
            if tipo_doc not in TIPOS_DOC:
                raise forms.ValidationError(f"Persona afectada #{i}: tipo de documento inválido.")
            if num_doc:
                regla = REGLAS_DOC[tipo_doc]
                if regla["solo_numeros"] and not num_doc.isdigit():
                    raise forms.ValidationError(f"Persona afectada #{i}: el documento solo puede contener dígitos.")
                if not num_doc.isalnum():
                    raise forms.ValidationError(
                        f"Persona afectada #{i}: el documento solo puede contener letras y números."
                    )
                if len(num_doc) < regla["min"] or len(num_doc) > regla["max"]:
                    raise forms.ValidationError(
                        f"Persona afectada #{i}: el documento debe tener entre {regla['min']} y {regla['max']} caracteres."
                    )
            if rol not in ROLES:
                rol = "OTRO"
            resultado.append({"nombre": nombre, "tipo_doc": tipo_doc, "numero_doc": num_doc, "rol": rol})
        return _json.dumps(resultado, ensure_ascii=False)

    def clean_riesgos_identificados(self):
        riesgos = self.cleaned_data.get("riesgos_identificados", "")
        if riesgos:
            riesgos = sanitizar_texto(riesgos)
            if len(riesgos) > 2000:
                raise forms.ValidationError("Los riesgos identificados no pueden exceder 2000 caracteres.")
        return riesgos

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")

        if not foto:
            raise forms.ValidationError("La foto de evidencia es obligatoria. Adjunta una imagen del incidente.")

        # Validar tamaño (max 5MB)
        if foto.size > 5 * 1024 * 1024:
            raise forms.ValidationError("La imagen no puede superar 5MB.")

        # Validar extensión
        ext = foto.name.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
            raise forms.ValidationError("Solo se permiten imagenes (JPG, PNG, GIF, WEBP).")

        # Validar tipo MIME
        content_type = foto.content_type
        if content_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
            raise forms.ValidationError("El archivo no es una imagen valida.")

        return foto

    def clean_fecha_incidente(self):
        from django.utils import timezone

        fecha = self.cleaned_data.get("fecha_incidente")

        if fecha:
            if fecha > timezone.now():
                raise forms.ValidationError("La fecha del incidente no puede ser en el futuro.")
            hace_un_año = timezone.now() - timezone.timedelta(days=365)
            if fecha < hace_un_año:
                raise forms.ValidationError("La fecha del incidente no puede ser hace mas de 1 año.")

        return fecha

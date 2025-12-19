# control_acceso/utils.py
import qrcode
import io
import base64
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont


def generar_qr_usuario(usuario):
    """
    Genera un código QR único para un usuario
    Retorna la imagen del QR en base64
    """
    # Crear datos del QR con información del usuario
    datos_qr = f"SST-USUARIO-{usuario.id}-{usuario.numero_documento}"

    # Configurar el QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    qr.add_data(datos_qr)
    qr.make(fit=True)

    # Crear la imagen
    img = qr.make_image(fill_color="black", back_color="white")

    # Agregar información adicional (nombre del usuario)
    img_pil = img.convert('RGB')
    width, height = img_pil.size

    # Crear una nueva imagen con espacio para el texto
    new_height = height + 80
    final_img = Image.new('RGB', (width, new_height), 'white')
    final_img.paste(img_pil, (0, 0))

    # Agregar texto
    draw = ImageDraw.Draw(final_img)

    # Información del usuario
    texto_nombre = usuario.get_full_name() or usuario.username
    texto_documento = f"Doc: {usuario.numero_documento}"
    texto_rol = usuario.get_rol_display()

    # Calcular posición central para el texto
    text_y = height + 10

    # Dibujar los textos (sin fuente personalizada para evitar problemas)
    draw.text((width//2, text_y), texto_nombre, fill='black', anchor='mt')
    draw.text((width//2, text_y + 25), texto_documento, fill='gray', anchor='mt')
    draw.text((width//2, text_y + 45), texto_rol, fill='green', anchor='mt')

    # Convertir a bytes
    buffer = io.BytesIO()
    final_img.save(buffer, format='PNG')
    buffer.seek(0)

    # Convertir a base64 para mostrar en HTML
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return img_base64


def generar_qr_visitante(visitante):
    """
    Genera un código QR único para un visitante
    Retorna la imagen del QR en base64
    """
    # Crear datos del QR
    datos_qr = f"SST-VISITANTE-{visitante.id}-{visitante.numero_documento}"

    # Configurar el QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    qr.add_data(datos_qr)
    qr.make(fit=True)

    # Crear la imagen
    img = qr.make_image(fill_color="black", back_color="white")

    # Agregar información adicional
    img_pil = img.convert('RGB')
    width, height = img_pil.size

    # Crear una nueva imagen con espacio para el texto
    new_height = height + 80
    final_img = Image.new('RGB', (width, new_height), 'white')
    final_img.paste(img_pil, (0, 0))

    # Agregar texto
    draw = ImageDraw.Draw(final_img)

    texto_nombre = visitante.nombre_completo
    texto_documento = f"Doc: {visitante.numero_documento}"
    texto_tipo = "VISITANTE"

    text_y = height + 10

    draw.text((width//2, text_y), texto_nombre, fill='black', anchor='mt')
    draw.text((width//2, text_y + 25), texto_documento, fill='gray', anchor='mt')
    draw.text((width//2, text_y + 45), texto_tipo, fill='orange', anchor='mt')

    # Convertir a bytes
    buffer = io.BytesIO()
    final_img.save(buffer, format='PNG')
    buffer.seek(0)

    # Convertir a base64
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return img_base64


def decodificar_qr(codigo_qr):
    """
    Decodifica un código QR y retorna el tipo y ID
    Retorna: (tipo, id) donde tipo puede ser 'USUARIO' o 'VISITANTE'
    """
    try:
        partes = codigo_qr.split('-')
        if len(partes) >= 4:
            prefijo = partes[0]  # SST
            tipo = partes[1]     # USUARIO o VISITANTE
            id_persona = partes[2]  # ID

            if prefijo == 'SST':
                return (tipo, int(id_persona))

        return (None, None)
    except (ValueError, IndexError):
        return (None, None)


def verificar_aforo_actual():
    """
    Verifica el aforo actual del centro
    Retorna: (personas_dentro, aforo_maximo, porcentaje, alerta)
    """
    from .models import RegistroAcceso, ConfiguracionAforo

    # Contar personas actualmente en el centro
    personas_dentro = RegistroAcceso.objects.filter(
        fecha_hora_egreso__isnull=True
    ).count()

    # Obtener configuración de aforo
    config_aforo = ConfiguracionAforo.objects.filter(activo=True).first()

    if config_aforo:
        aforo_maximo = config_aforo.aforo_maximo
        aforo_minimo = config_aforo.aforo_minimo
        porcentaje = (personas_dentro / aforo_maximo) * 100

        # Determinar nivel de alerta
        if personas_dentro >= aforo_maximo:
            alerta = 'CRITICO'
        elif personas_dentro >= aforo_minimo:
            alerta = 'ADVERTENCIA'
        else:
            alerta = 'NORMAL'

        return {
            'personas_dentro': personas_dentro,
            'aforo_maximo': aforo_maximo,
            'aforo_minimo': aforo_minimo,
            'porcentaje': round(porcentaje, 2),
            'alerta': alerta,
            'mensaje': config_aforo.mensaje_alerta if alerta != 'NORMAL' else ''
        }
    else:
        return {
            'personas_dentro': personas_dentro,
            'aforo_maximo': 2000,
            'aforo_minimo': 1800,
            'porcentaje': 0,
            'alerta': 'NORMAL',
            'mensaje': ''
        }


def obtener_estadisticas_hoy():
    """
    Obtiene estadísticas de acceso del día actual
    """
    from .models import RegistroAcceso
    from usuarios.models import Visitante
    from django.utils import timezone
    from datetime import datetime, time

    hoy = timezone.now().date()
    inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
    fin_dia = timezone.make_aware(datetime.combine(hoy, time.max))

    # Ingresos de hoy
    ingresos_hoy = RegistroAcceso.objects.filter(
        fecha_hora_ingreso__range=(inicio_dia, fin_dia)
    ).count()

    # Personas actualmente en el centro
    personas_dentro = RegistroAcceso.objects.filter(
        fecha_hora_egreso__isnull=True
    ).count()

    # Visitantes activos
    visitantes_activos = Visitante.objects.filter(
        fecha_visita=hoy,
        hora_salida__isnull=True,
        activo=True
    ).count()

    # Información de aforo
    aforo_info = verificar_aforo_actual()

    return {
        'ingresos_hoy': ingresos_hoy,
        'personas_dentro': personas_dentro,
        'visitantes_activos': visitantes_activos,
        'aforo': aforo_info
    }

"""
Utilidades de validación y seguridad
Sistema SST - Centro Minero SENA
"""

import re
import logging
from django.utils.html import strip_tags
from django.utils import timezone
from functools import wraps

# Logger para auditoría
audit_logger = logging.getLogger('auditoria')


# ============================================================
# FUNCIONES DE SANITIZACIÓN
# ============================================================

def sanitizar_texto(texto, max_length=None):
    """
    Sanitiza texto para prevenir XSS y otros ataques.

    Args:
        texto: String a sanitizar
        max_length: Longitud máxima permitida (opcional)

    Returns:
        String sanitizado
    """
    if not texto:
        return texto

    # Eliminar tags HTML
    texto = strip_tags(str(texto))

    # Eliminar caracteres de control (excepto saltos de línea y tabs)
    texto = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', texto)

    # Eliminar espacios múltiples
    texto = re.sub(r' +', ' ', texto)

    # Trim
    texto = texto.strip()

    # Truncar si excede longitud máxima
    if max_length and len(texto) > max_length:
        texto = texto[:max_length]

    return texto


def sanitizar_nombre(nombre):
    """
    Sanitiza nombres de personas.
    Solo permite letras, espacios, tildes y guiones.
    """
    if not nombre:
        return nombre

    nombre = sanitizar_texto(nombre, max_length=100)

    # Solo permitir caracteres válidos para nombres
    nombre = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-]', '', nombre)

    return nombre.title()


def sanitizar_numero_documento(documento):
    """
    Sanitiza números de documento.
    Solo permite números y letras (para casos como pasaportes).
    """
    if not documento:
        return documento

    documento = str(documento).strip()

    # Solo permitir alfanuméricos
    documento = re.sub(r'[^a-zA-Z0-9]', '', documento)

    return documento.upper()


def sanitizar_telefono(telefono):
    """
    Sanitiza números de teléfono.
    Solo permite números, espacios, guiones y el signo +.
    """
    if not telefono:
        return telefono

    telefono = str(telefono).strip()

    # Solo permitir caracteres válidos para teléfonos
    telefono = re.sub(r'[^0-9\s\-\+]', '', telefono)

    # Eliminar espacios múltiples
    telefono = re.sub(r'\s+', ' ', telefono)

    return telefono


def validar_email(email):
    """
    Valida formato de email.

    Returns:
        True si es válido, False si no
    """
    if not email:
        return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, str(email)))


# ============================================================
# LOGGING DE AUDITORÍA
# ============================================================

def log_accion_usuario(usuario, accion, detalle=None, ip=None, exito=True):
    """
    Registra una acción de usuario para auditoría.

    Args:
        usuario: Instancia del usuario o username
        accion: Tipo de acción (LOGIN, LOGOUT, CREATE, UPDATE, DELETE, etc.)
        detalle: Detalles adicionales
        ip: Dirección IP del cliente
        exito: Si la acción fue exitosa
    """
    username = getattr(usuario, 'username', str(usuario))
    rol = getattr(usuario, 'rol', 'N/A')

    mensaje = f"[{accion}] Usuario: {username} | Rol: {rol}"

    if detalle:
        mensaje += f" | Detalle: {detalle}"

    if ip:
        mensaje += f" | IP: {ip}"

    mensaje += f" | Exito: {exito}"

    if exito:
        audit_logger.info(mensaje)
    else:
        audit_logger.warning(mensaje)


def obtener_ip_cliente(request):
    """
    Obtiene la IP del cliente desde el request.
    Considera headers de proxy como X-Forwarded-For.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'N/A')

    return ip


def auditar_vista(accion):
    """
    Decorador para auditar acciones en vistas.

    Uso:
        @auditar_vista('CREAR_INCIDENTE')
        def crear_incidente(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            ip = obtener_ip_cliente(request)
            usuario = request.user if request.user.is_authenticated else 'Anónimo'

            try:
                response = view_func(request, *args, **kwargs)
                log_accion_usuario(
                    usuario=usuario,
                    accion=accion,
                    ip=ip,
                    exito=True
                )
                return response
            except Exception as e:
                log_accion_usuario(
                    usuario=usuario,
                    accion=accion,
                    detalle=f"Error: {str(e)}",
                    ip=ip,
                    exito=False
                )
                raise

        return wrapper
    return decorator


# ============================================================
# VALIDADORES PARA MODELOS
# ============================================================

def validar_coordenadas(latitud, longitud):
    """
    Valida que las coordenadas sean válidas.

    Returns:
        (True, None) si son válidas
        (False, mensaje_error) si no lo son
    """
    try:
        lat = float(latitud)
        lon = float(longitud)

        if not (-90 <= lat <= 90):
            return False, "Latitud debe estar entre -90 y 90"

        if not (-180 <= lon <= 180):
            return False, "Longitud debe estar entre -180 y 180"

        return True, None

    except (ValueError, TypeError):
        return False, "Coordenadas inválidas"


def validar_imagen(archivo, max_size_mb=5):
    """
    Valida un archivo de imagen.

    Args:
        archivo: Archivo subido
        max_size_mb: Tamaño máximo en MB

    Returns:
        (True, None) si es válida
        (False, mensaje_error) si no lo es
    """
    if not archivo:
        return True, None

    # Validar tamaño
    max_size = max_size_mb * 1024 * 1024
    if archivo.size > max_size:
        return False, f"El archivo excede el tamaño máximo de {max_size_mb}MB"

    # Validar extensión
    ext = archivo.name.split('.')[-1].lower()
    extensiones_permitidas = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    if ext not in extensiones_permitidas:
        return False, f"Extensión no permitida. Use: {', '.join(extensiones_permitidas)}"

    # Validar tipo MIME
    tipos_permitidos = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    content_type = getattr(archivo, 'content_type', None)
    if content_type and content_type not in tipos_permitidos:
        return False, "El archivo no es una imagen válida"

    return True, None


# ============================================================
# ACCIONES DE AUDITORÍA PREDEFINIDAS
# ============================================================

class AccionAuditoria:
    """Constantes para tipos de acciones de auditoría"""
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    LOGIN_FALLIDO = 'LOGIN_FALLIDO'
    REGISTRO = 'REGISTRO'

    # Emergencias
    EMERGENCIA_CREAR = 'EMERGENCIA_CREAR'
    EMERGENCIA_ATENDER = 'EMERGENCIA_ATENDER'
    EMERGENCIA_RESOLVER = 'EMERGENCIA_RESOLVER'

    # Incidentes
    INCIDENTE_CREAR = 'INCIDENTE_CREAR'
    INCIDENTE_ACTUALIZAR = 'INCIDENTE_ACTUALIZAR'

    # Control de acceso
    ACCESO_REGISTRAR = 'ACCESO_REGISTRAR'
    ACCESO_EGRESO = 'ACCESO_EGRESO'

    # Usuarios
    USUARIO_CREAR = 'USUARIO_CREAR'
    USUARIO_MODIFICAR = 'USUARIO_MODIFICAR'
    USUARIO_ELIMINAR = 'USUARIO_ELIMINAR'

    # Visitantes
    VISITANTE_REGISTRAR = 'VISITANTE_REGISTRAR'
    VISITANTE_SALIDA = 'VISITANTE_SALIDA'

    # Equipamiento
    EQUIPO_ACTUALIZAR = 'EQUIPO_ACTUALIZAR'

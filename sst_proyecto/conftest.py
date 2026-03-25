"""
Fixtures globales para la suite de tests del sistema SST.
"""

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from django.test import override_settings


# Desactiva rate-limiting y axes durante toda la suite de tests
pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture(autouse=True)
def disable_rate_limiting(settings):
    """Desactiva django-ratelimit, django-axes, usa caché en memoria y añade testserver a ALLOWED_HOSTS."""
    settings.RATELIMIT_ENABLE = False
    settings.AXES_ENABLED = False
    settings.ALLOWED_HOSTS = ["*"]
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
    # Usar InMemoryChannelLayer en tests (sin Redis real)
    settings.CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        }
    }


# ---------------------------------------------------------------------------
# Factories importadas aquí para que pytest-django las resuelva sin imports
# circulares cuando se usan desde múltiples apps.
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client():
    return APIClient()


def _make_user(rol, **kwargs):
    """Helper interno: crea un usuario con el rol dado."""
    from usuarios.tests.factories import UsuarioFactory

    return UsuarioFactory(rol=rol, **kwargs)


def _auth_client(user):
    """Devuelve un APIClient con token del usuario."""
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


# --- Fixtures de usuario por rol -------------------------------------------


@pytest.fixture
def aprendiz(db):
    return _make_user("APRENDIZ", ficha="2850325", programa_formacion="Analisis y Desarrollo de Software")


@pytest.fixture
def instructor(db):
    return _make_user("INSTRUCTOR")


@pytest.fixture
def administrativo(db):
    return _make_user("ADMINISTRATIVO")


@pytest.fixture
def vigilancia(db):
    return _make_user("VIGILANCIA")


@pytest.fixture
def brigada(db):
    return _make_user("BRIGADA")


@pytest.fixture
def visitante(db):
    return _make_user("VISITANTE")


@pytest.fixture
def coordinador(db):
    return _make_user("COORDINADOR_SST")


# --- Fixtures de cliente autenticado ----------------------------------------


@pytest.fixture
def client_aprendiz(aprendiz):
    return _auth_client(aprendiz)


@pytest.fixture
def client_instructor(instructor):
    return _auth_client(instructor)


@pytest.fixture
def client_administrativo(administrativo):
    return _auth_client(administrativo)


@pytest.fixture
def client_vigilancia(vigilancia):
    return _auth_client(vigilancia)


@pytest.fixture
def client_brigada(brigada):
    return _auth_client(brigada)


@pytest.fixture
def client_visitante(visitante):
    return _auth_client(visitante)


@pytest.fixture
def client_coordinador(coordinador):
    return _auth_client(coordinador)


# --- Fixtures de datos de dominio -------------------------------------------


@pytest.fixture
def tipo_emergencia(db):
    from emergencias.tests.factories import TipoEmergenciaFactory

    return TipoEmergenciaFactory()


@pytest.fixture
def django_client_aprendiz(aprendiz):
    """Django test Client (session-based) autenticado como aprendiz."""
    from django.test import Client

    c = Client()
    c.force_login(aprendiz)
    return c


@pytest.fixture
def django_client_administrativo(administrativo):
    from django.test import Client

    c = Client()
    c.force_login(administrativo)
    return c


@pytest.fixture
def django_client_brigada(brigada):
    from django.test import Client

    c = Client()
    c.force_login(brigada)
    return c


@pytest.fixture
def django_client_coordinador(coordinador):
    from django.test import Client

    c = Client()
    c.force_login(coordinador)
    return c


@pytest.fixture
def django_client_vigilancia(vigilancia):
    from django.test import Client

    c = Client()
    c.force_login(vigilancia)
    return c


@pytest.fixture
def geocerca(db):
    from control_acceso.models import Geocerca

    return Geocerca.objects.create(
        nombre="Centro Minero SENA",
        centro_latitud=5.7303596,
        centro_longitud=-72.8943613,
        radio_metros=200,
        activo=True,
    )

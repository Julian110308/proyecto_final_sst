"""
Tests para las vistas de dashboard y páginas internas (template views).
Cubren urls.py: dashboard_view, mi_perfil_view, mis_alertas_view, etc.
"""

import pytest


DASHBOARD_URL = "/"
PERFIL_URL = "/perfil/"
ALERTAS_URL = "/alertas/"
ASISTENCIA_URL = "/aprendiz/mis-accesos/"
MIS_APRENDICES_URL = "/instructor/mis-aprendices/"
GESTION_USUARIOS_URL = "/administrativo/usuarios/"


# ---------------------------------------------------------------------------
# Dashboard por rol
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_dashboard_aprendiz(django_client_aprendiz):
    response = django_client_aprendiz.get(DASHBOARD_URL)
    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_administrativo(django_client_administrativo):
    response = django_client_administrativo.get(DASHBOARD_URL)
    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_brigada(django_client_brigada):
    response = django_client_brigada.get(DASHBOARD_URL)
    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_coordinador(django_client_coordinador):
    response = django_client_coordinador.get(DASHBOARD_URL)
    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_vigilancia(django_client_vigilancia):
    response = django_client_vigilancia.get(DASHBOARD_URL)
    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_sin_login_redirige():
    from django.test import Client

    response = Client().get(DASHBOARD_URL)
    assert response.status_code == 302


# ---------------------------------------------------------------------------
# Perfil
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_perfil_get(django_client_aprendiz):
    response = django_client_aprendiz.get(PERFIL_URL)
    assert response.status_code == 200


@pytest.mark.django_db
def test_perfil_get_instructor(django_client_vigilancia):
    response = django_client_vigilancia.get(PERFIL_URL)
    assert response.status_code == 200


@pytest.mark.django_db
def test_perfil_post_actualiza_datos(django_client_aprendiz, aprendiz):
    response = django_client_aprendiz.post(
        PERFIL_URL,
        {
            "first_name": "Juan",
            "last_name": "Actualizado",
            "email": aprendiz.email,
            "telefono": "3001234567",
            "telefono_emergencia": "",
            "contacto_emergencia": "",
        },
    )
    assert response.status_code == 302
    aprendiz.refresh_from_db()
    assert aprendiz.first_name == "Juan"


# ---------------------------------------------------------------------------
# Mis alertas
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_alertas_get(django_client_aprendiz):
    response = django_client_aprendiz.get(ALERTAS_URL)
    assert response.status_code == 200


@pytest.mark.django_db
def test_alertas_requiere_login():
    from django.test import Client

    response = Client().get(ALERTAS_URL)
    assert response.status_code == 302


# ---------------------------------------------------------------------------
# Mi asistencia (solo APRENDIZ)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_asistencia_aprendiz(django_client_aprendiz):
    response = django_client_aprendiz.get(ASISTENCIA_URL)
    assert response.status_code == 200


@pytest.mark.django_db
def test_asistencia_admin_redirigido(django_client_administrativo):
    """Un no-APRENDIZ no puede acceder a mis-accesos."""
    response = django_client_administrativo.get(ASISTENCIA_URL)
    assert response.status_code == 302


# ---------------------------------------------------------------------------
# Mis aprendices (solo INSTRUCTOR)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_mis_aprendices_instructor(instructor):
    from django.test import Client

    c = Client()
    c.force_login(instructor)
    response = c.get(MIS_APRENDICES_URL)
    assert response.status_code == 200


@pytest.mark.django_db
def test_mis_aprendices_aprendiz_redirigido(django_client_aprendiz):
    response = django_client_aprendiz.get(MIS_APRENDICES_URL)
    assert response.status_code == 302


# ---------------------------------------------------------------------------
# Gestión usuarios (solo ADMINISTRATIVO)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_gestion_usuarios_admin(django_client_administrativo):
    response = django_client_administrativo.get(GESTION_USUARIOS_URL)
    assert response.status_code == 200


@pytest.mark.django_db
def test_gestion_usuarios_aprendiz_redirigido(django_client_aprendiz):
    response = django_client_aprendiz.get(GESTION_USUARIOS_URL)
    assert response.status_code == 302

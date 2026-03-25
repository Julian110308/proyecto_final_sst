"""
Tests 2.3: Generación de reportes — smoke tests de PDF y permisos.
"""

import pytest
from django.utils import timezone
from datetime import timedelta
from control_acceso.models import RegistroAcceso, ConfiguracionAforo


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rango_fechas():
    hoy = timezone.now().date()
    return hoy - timedelta(days=7), hoy


# ---------------------------------------------------------------------------
# Smoke tests: los endpoints de reporte no lanzan 500
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_reporte_aforo_json_no_lanza_error(client_administrativo):
    inicio, fin = _rango_fechas()
    url = f"/reportes/api/aforo/?fecha_inicio={inicio}&fecha_fin={fin}"
    response = client_administrativo.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_reporte_incidentes_json_no_lanza_error(client_administrativo):
    inicio, fin = _rango_fechas()
    url = f"/reportes/api/incidentes/?fecha_inicio={inicio}&fecha_fin={fin}"
    response = client_administrativo.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_reporte_asistencia_json_no_lanza_error(client_instructor):
    inicio, fin = _rango_fechas()
    url = f"/reportes/api/asistencia/?ficha=2850325&fecha_inicio={inicio}&fecha_fin={fin}"
    response = client_instructor.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_reporte_pdf_aforo_devuelve_pdf(client_administrativo):
    inicio, fin = _rango_fechas()
    url = f"/reportes/api/aforo/?fecha_inicio={inicio}&fecha_fin={fin}&formato=pdf"
    response = client_administrativo.get(url)
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"


# ---------------------------------------------------------------------------
# Control de permisos en reportes
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_visitante_no_puede_generar_reporte_aforo(client_visitante):
    inicio, fin = _rango_fechas()
    url = f"/reportes/api/aforo/?fecha_inicio={inicio}&fecha_fin={fin}"
    response = client_visitante.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_aprendiz_no_puede_generar_reporte_aforo(client_aprendiz):
    inicio, fin = _rango_fechas()
    url = f"/reportes/api/aforo/?fecha_inicio={inicio}&fecha_fin={fin}"
    response = client_aprendiz.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_aprendiz_puede_ver_su_asistencia(client_aprendiz):
    response = client_aprendiz.get("/reportes/api/mi_asistencia/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_instructor_no_puede_ver_mi_asistencia(client_instructor):
    response = client_instructor.get("/reportes/api/mi_asistencia/")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Aforo al 90% genera notificación automática
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_aforo_critico_genera_notificacion(client_vigilancia, vigilancia, administrativo, geocerca):
    from usuarios.models import Notificacion

    ConfiguracionAforo.objects.create(aforo_maximo=10, aforo_minimo=7, activo=True)

    # Crear 7 registros de ingreso (70%) → ADVERTENCIA, sin bloqueo de aforo
    from usuarios.tests.factories import UsuarioFactory

    for _ in range(7):
        u = UsuarioFactory()
        RegistroAcceso.objects.create(
            usuario=u,
            tipo="INGRESO",
            latitud_ingreso=geocerca.centro_latitud,
            longitud_ingreso=geocerca.centro_longitud,
            metodo_ingreso="MANUAL",
        )

    # El octavo ingreso (80%) → ADVERTENCIA → dispara la notificación
    nuevo_usuario = UsuarioFactory()
    url = "/api/acceso/registros/registrar_ingreso/"
    payload = {
        "usuario_id": nuevo_usuario.id,
        "latitud": geocerca.centro_latitud,
        "longitud": geocerca.centro_longitud,
        "metodo": "MANUAL",
    }
    response = client_vigilancia.post(url, payload, format="json")
    assert response.status_code == 201

    assert Notificacion.objects.filter(tipo="SISTEMA").exists()

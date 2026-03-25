"""
Tests de cobertura adicional para emergencias/views.py
"""

import pytest
from emergencias.models import Emergencia
from emergencias.tests.factories import EmergenciaFactory


LIST_URL = "/api/emergencias/emergencias/"


# ---------------------------------------------------------------------------
# Listar y ver emergencias
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_listar_emergencias_autenticado(client_aprendiz, tipo_emergencia):
    EmergenciaFactory(tipo=tipo_emergencia)
    response = client_aprendiz.get(LIST_URL)
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.django_db
def test_ver_detalle_emergencia(client_brigada, tipo_emergencia):
    em = EmergenciaFactory(tipo=tipo_emergencia)
    response = client_brigada.get(f"{LIST_URL}{em.id}/")
    assert response.status_code == 200
    assert response.json()["id"] == em.id


@pytest.mark.django_db
def test_sin_autenticacion_no_puede_listar(api_client, tipo_emergencia):
    EmergenciaFactory(tipo=tipo_emergencia)
    response = api_client.get(LIST_URL)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Crear emergencia (acción create estándar)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_crear_emergencia_aprendiz(client_aprendiz, tipo_emergencia):
    payload = {
        "tipo": tipo_emergencia.id,
        "latitud": 5.7303596,
        "longitud": -72.8943613,
        "descripcion": "Incidente en taller",
    }
    response = client_aprendiz.post(LIST_URL, payload, format="json")
    assert response.status_code == 201
    assert Emergencia.objects.filter(estado="REPORTADA").exists()


# ---------------------------------------------------------------------------
# Atender emergencia
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_brigada_puede_atender_emergencia(client_brigada, tipo_emergencia):
    em = EmergenciaFactory(tipo=tipo_emergencia, estado="REPORTADA")
    response = client_brigada.post(f"{LIST_URL}{em.id}/atender/", {}, format="json")
    assert response.status_code == 200
    em.refresh_from_db()
    assert em.estado == "EN_ATENCION"


@pytest.mark.django_db
def test_aprendiz_no_puede_atender_emergencia(client_aprendiz, tipo_emergencia):
    em = EmergenciaFactory(tipo=tipo_emergencia)
    response = client_aprendiz.post(f"{LIST_URL}{em.id}/atender/", {}, format="json")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Resolver emergencia
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_brigada_puede_resolver_emergencia(client_brigada, tipo_emergencia):
    em = EmergenciaFactory(tipo=tipo_emergencia, estado="EN_ATENCION")
    response = client_brigada.post(
        f"{LIST_URL}{em.id}/resolver/", {"acciones_tomadas": "Se controló el fuego"}, format="json"
    )
    assert response.status_code == 200
    em.refresh_from_db()
    assert em.estado in ("RESUELTA", "CONTROLADA")


@pytest.mark.django_db
def test_visitante_no_puede_resolver_emergencia(client_visitante, tipo_emergencia):
    em = EmergenciaFactory(tipo=tipo_emergencia, estado="EN_ATENCION")
    response = client_visitante.post(f"{LIST_URL}{em.id}/resolver/", {"acciones_tomadas": "Test"}, format="json")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Marcar falsa alarma
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_brigada_puede_marcar_falsa_alarma(client_brigada, tipo_emergencia):
    em = EmergenciaFactory(tipo=tipo_emergencia, estado="REPORTADA")
    payload = {"motivo": "Fue solo una prueba"}
    response = client_brigada.post(f"{LIST_URL}{em.id}/marcar-falsa-alarma/", payload, format="json")
    assert response.status_code == 200
    em.refresh_from_db()
    assert em.estado == "FALSA_ALARMA"


# ---------------------------------------------------------------------------
# Tipos de emergencia
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_listar_tipos_emergencia(client_aprendiz, tipo_emergencia):
    response = client_aprendiz.get("/api/emergencias/tipos/")
    assert response.status_code == 200
    assert len(response.json()) >= 1

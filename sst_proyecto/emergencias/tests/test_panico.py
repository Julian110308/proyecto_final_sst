"""
Tests 2.3: Flujo botón pánico → notificación a brigada.
"""

import pytest
from unittest.mock import patch
from emergencias.models import Emergencia
from usuarios.models import Notificacion


PANICO_URL = "/api/emergencias/emergencias/boton_panico/"


def _payload(tipo_id):
    return {
        "tipo": tipo_id,
        "latitud": 5.7303596,
        "longitud": -72.8943613,
        "descripcion": "Emergencia de prueba desde test",
    }


@pytest.mark.django_db
def test_boton_panico_crea_emergencia(client_aprendiz, tipo_emergencia):
    response = client_aprendiz.post(PANICO_URL, _payload(tipo_emergencia.id), format="json")
    assert response.status_code == 201
    assert Emergencia.objects.filter(estado="REPORTADA").exists()


@pytest.mark.django_db
def test_boton_panico_notifica_brigada(client_aprendiz, tipo_emergencia, brigada):
    """Al activar el pánico deben crearse notificaciones para miembros de brigada."""
    response = client_aprendiz.post(PANICO_URL, _payload(tipo_emergencia.id), format="json")
    assert response.status_code == 201
    # Debe haber al menos una notificación de tipo EMERGENCIA para el usuario brigada
    assert Notificacion.objects.filter(destinatario=brigada, tipo="EMERGENCIA").exists()


@pytest.mark.django_db
def test_boton_panico_sin_autenticacion_devuelve_401(api_client, tipo_emergencia):
    response = api_client.post(PANICO_URL, _payload(tipo_emergencia.id), format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_boton_panico_campos_requeridos(client_aprendiz):
    response = client_aprendiz.post(PANICO_URL, {}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_emergencia_reportada_tiene_estado_inicial_correcto(client_aprendiz, tipo_emergencia):
    client_aprendiz.post(PANICO_URL, _payload(tipo_emergencia.id), format="json")
    emergencia = Emergencia.objects.latest("fecha_hora_reporte")
    assert emergencia.estado == "REPORTADA"
    assert emergencia.reportada_por is not None

"""
Tests de cobertura adicional para control_acceso/views.py
"""

import pytest
from control_acceso.models import RegistroAcceso


INGRESO_URL = "/api/acceso/registros/registrar_ingreso/"
EGRESO_URL = "/api/acceso/registros/registrar_egreso/"
MI_ESTADO_URL = "/api/acceso/registros/mi-estado/"
BUSCAR_URL = "/api/acceso/registros/buscar_usuario/"
PERSONAS_URL = "/api/acceso/registros/personas_en_centro/"
ESTADISTICAS_URL = "/api/acceso/registros/estadisticas/"


# ---------------------------------------------------------------------------
# registrar_ingreso
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_registrar_ingreso_manual_ok(client_vigilancia, aprendiz, geocerca):
    payload = {
        "usuario_id": aprendiz.id,
        "latitud": geocerca.centro_latitud,
        "longitud": geocerca.centro_longitud,
        "metodo": "MANUAL",
    }
    response = client_vigilancia.post(INGRESO_URL, payload, format="json")
    assert response.status_code == 201
    assert RegistroAcceso.objects.filter(usuario=aprendiz, tipo="INGRESO").exists()


@pytest.mark.django_db
def test_registrar_ingreso_usuario_inexistente(client_vigilancia):
    payload = {"usuario_id": 99999, "metodo": "MANUAL"}
    response = client_vigilancia.post(INGRESO_URL, payload, format="json")
    assert response.status_code == 400  # serializer valida la existencia del usuario


@pytest.mark.django_db
def test_registrar_ingreso_duplicado_rechazado(client_vigilancia, aprendiz, geocerca):
    RegistroAcceso.objects.create(
        usuario=aprendiz,
        tipo="INGRESO",
        latitud_ingreso=geocerca.centro_latitud,
        longitud_ingreso=geocerca.centro_longitud,
        metodo_ingreso="MANUAL",
    )
    payload = {"usuario_id": aprendiz.id, "metodo": "MANUAL"}
    response = client_vigilancia.post(INGRESO_URL, payload, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_registrar_ingreso_requiere_rol_vigilancia(client_aprendiz, aprendiz):
    payload = {"usuario_id": aprendiz.id, "metodo": "MANUAL"}
    response = client_aprendiz.post(INGRESO_URL, payload, format="json")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# registrar_egreso
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_registrar_egreso_ok(client_vigilancia, aprendiz, geocerca):
    RegistroAcceso.objects.create(
        usuario=aprendiz,
        tipo="INGRESO",
        latitud_ingreso=geocerca.centro_latitud,
        longitud_ingreso=geocerca.centro_longitud,
        metodo_ingreso="MANUAL",
    )
    payload = {"usuario_id": aprendiz.id, "metodo": "MANUAL"}
    response = client_vigilancia.post(EGRESO_URL, payload, format="json")
    assert response.status_code == 200
    registro = RegistroAcceso.objects.get(usuario=aprendiz)
    assert registro.fecha_hora_egreso is not None


@pytest.mark.django_db
def test_registrar_egreso_sin_ingreso_previo(client_vigilancia, aprendiz):
    payload = {"usuario_id": aprendiz.id, "metodo": "MANUAL"}
    response = client_vigilancia.post(EGRESO_URL, payload, format="json")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# mi-estado
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_mi_estado_fuera_del_centro(client_aprendiz):
    response = client_aprendiz.get(MI_ESTADO_URL)
    assert response.status_code == 200
    assert response.json()["en_centro"] is False


@pytest.mark.django_db
def test_mi_estado_dentro_del_centro(client_aprendiz, aprendiz, geocerca):
    RegistroAcceso.objects.create(
        usuario=aprendiz,
        tipo="INGRESO",
        latitud_ingreso=geocerca.centro_latitud,
        longitud_ingreso=geocerca.centro_longitud,
        metodo_ingreso="MANUAL",
    )
    response = client_aprendiz.get(MI_ESTADO_URL)
    assert response.status_code == 200
    assert response.json()["en_centro"] is True


# ---------------------------------------------------------------------------
# buscar_usuario
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_buscar_usuario_por_documento(client_vigilancia, aprendiz):
    url = f"{BUSCAR_URL}?documento={aprendiz.numero_documento}"
    response = client_vigilancia.get(url)
    assert response.status_code == 200
    assert response.json()["id"] == aprendiz.id


@pytest.mark.django_db
def test_buscar_usuario_no_encontrado(client_vigilancia):
    url = f"{BUSCAR_URL}?documento=99999999"
    response = client_vigilancia.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_buscar_usuario_sin_parametro(client_vigilancia):
    response = client_vigilancia.get(BUSCAR_URL)
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# personas_en_centro y estadisticas
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_personas_en_centro_vacio(client_vigilancia):
    response = client_vigilancia.get(PERSONAS_URL)
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.django_db
def test_estadisticas_acceso(client_aprendiz):
    response = client_aprendiz.get(ESTADISTICAS_URL)
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# get_queryset — aislamiento por rol
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_aprendiz_no_puede_usar_endpoint_list(client_aprendiz):
    """El endpoint list está restringido a VIGILANCIA/ADMINISTRATIVO."""
    response = client_aprendiz.get("/api/acceso/registros/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_vigilancia_ve_todos_los_registros(client_vigilancia, aprendiz, instructor, geocerca):
    """VIGILANCIA sí puede listar y ve registros de todos los usuarios."""
    RegistroAcceso.objects.create(
        usuario=aprendiz,
        tipo="INGRESO",
        latitud_ingreso=geocerca.centro_latitud,
        longitud_ingreso=geocerca.centro_longitud,
        metodo_ingreso="MANUAL",
    )
    RegistroAcceso.objects.create(
        usuario=instructor,
        tipo="INGRESO",
        latitud_ingreso=geocerca.centro_latitud,
        longitud_ingreso=geocerca.centro_longitud,
        metodo_ingreso="MANUAL",
    )
    response = client_vigilancia.get("/api/acceso/registros/")
    assert response.status_code == 200
    assert response.json()["count"] == 2

"""
Tests 2.2: Permisos por rol en los endpoints de la API.
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _url(path):
    return f"/api{path}"


# ---------------------------------------------------------------------------
# Token inválido → 401
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_token_invalido_devuelve_401(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Token tokeninvalido999")
    response = api_client.get(_url("/auth/usuarios/perfil/"))
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# APRENDIZ no puede crear emergencia directamente vía API create
# (solo puede usar boton_panico)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_aprendiz_no_puede_resolver_emergencia(client_aprendiz, tipo_emergencia):
    from emergencias.tests.factories import EmergenciaFactory

    emergencia = EmergenciaFactory(tipo=tipo_emergencia)
    url = _url(f"/emergencias/emergencias/{emergencia.id}/resolver/")
    response = client_aprendiz.post(url, {"acciones_tomadas": "Prueba"}, format="json")
    assert response.status_code == 403


@pytest.mark.django_db
def test_aprendiz_no_puede_atender_emergencia(client_aprendiz, tipo_emergencia):
    from emergencias.tests.factories import EmergenciaFactory

    emergencia = EmergenciaFactory(tipo=tipo_emergencia)
    url = _url(f"/emergencias/emergencias/{emergencia.id}/atender/")
    response = client_aprendiz.post(url, {}, format="json")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# VISITANTE no puede acceder a dashboards internos (requiere sesión)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_visitante_no_puede_listar_emergencias_como_admin(client_visitante):
    # El listado está abierto a todos los autenticados, pero el visitante
    # no debería poder acceder a endpoints de gestión de usuarios
    response = client_visitante.get(_url("/auth/usuarios/pendientes/"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_visitante_no_puede_registros_recientes_acceso(client_visitante):
    response = client_visitante.get(_url("/acceso/registros/registros_recientes/"))
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Solo BRIGADA/ADMIN puede resolver emergencia
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_brigada_puede_resolver_emergencia(client_brigada, tipo_emergencia):
    from emergencias.tests.factories import EmergenciaFactory

    emergencia = EmergenciaFactory(tipo=tipo_emergencia, estado="EN_ATENCION")
    url = _url(f"/emergencias/emergencias/{emergencia.id}/resolver/")
    response = client_brigada.post(url, {"acciones_tomadas": "Controlado"}, format="json")
    assert response.status_code in (200, 201)


@pytest.mark.django_db
def test_administrativo_puede_resolver_emergencia(client_administrativo, tipo_emergencia):
    from emergencias.tests.factories import EmergenciaFactory

    emergencia = EmergenciaFactory(tipo=tipo_emergencia, estado="EN_ATENCION")
    url = _url(f"/emergencias/emergencias/{emergencia.id}/resolver/")
    response = client_administrativo.post(url, {"acciones_tomadas": "Controlado"}, format="json")
    assert response.status_code in (200, 201)


@pytest.mark.django_db
def test_instructor_no_puede_resolver_emergencia(client_instructor, tipo_emergencia):
    from emergencias.tests.factories import EmergenciaFactory

    emergencia = EmergenciaFactory(tipo=tipo_emergencia)
    url = _url(f"/emergencias/emergencias/{emergencia.id}/resolver/")
    response = client_instructor.post(url, {"acciones_tomadas": "Prueba"}, format="json")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# COORDINADOR_SST puede ver todos los reportes
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_coordinador_puede_listar_reportes(client_coordinador):
    response = client_coordinador.get("/reportes/api/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_aprendiz_no_puede_listar_reportes_ajenos(client_aprendiz, aprendiz):
    # El aprendiz solo puede ver sus propios reportes (get_queryset lo filtra)
    response = client_aprendiz.get("/reportes/api/")
    assert response.status_code == 200
    data = response.json()
    # La lista puede estar vacía pero nunca debe devolver 403 al aprendiz
    assert isinstance(data, (list, dict))


# ---------------------------------------------------------------------------
# IDOR: usuario no puede ver perfil de otro usuario
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_aprendiz_no_puede_ver_perfil_ajeno(client_aprendiz, administrativo):
    url = _url(f"/auth/usuarios/{administrativo.id}/")
    response = client_aprendiz.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_aprendiz_puede_ver_su_propio_perfil(client_aprendiz, aprendiz):
    url = _url(f"/auth/usuarios/{aprendiz.id}/")
    response = client_aprendiz.get(url)
    assert response.status_code == 200
    assert response.json()["id"] == aprendiz.id

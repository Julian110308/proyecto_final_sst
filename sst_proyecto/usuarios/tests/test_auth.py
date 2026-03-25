"""
Tests de cobertura adicional para usuarios/views.py — login, registro, perfil.
"""

import pytest
from rest_framework.authtoken.models import Token
from usuarios.models import Usuario


LOGIN_URL = "/api/auth/usuarios/login/"
REGISTRO_URL = "/api/auth/usuarios/"
PERFIL_URL = "/api/auth/usuarios/perfil/"
LOGOUT_URL = "/api/auth/usuarios/logout/"


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_login_exitoso(api_client, aprendiz):
    aprendiz.set_password("testpass123")
    aprendiz.save()
    payload = {"username": aprendiz.email, "password": "testpass123"}
    response = api_client.post(LOGIN_URL, payload, format="json")
    assert response.status_code == 200
    assert "token" in response.json()


@pytest.mark.django_db
def test_login_credenciales_incorrectas(api_client, aprendiz):
    payload = {"username": aprendiz.email, "password": "wrongpass"}
    response = api_client.post(LOGIN_URL, payload, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_login_cuenta_bloqueada(api_client, aprendiz):
    aprendiz.estado_cuenta = "BLOQUEADO"
    aprendiz.save()
    aprendiz.set_password("testpass123")
    aprendiz.save()
    payload = {"username": aprendiz.email, "password": "testpass123"}
    response = api_client.post(LOGIN_URL, payload, format="json")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_logout_invalida_token(client_aprendiz, aprendiz):
    response = client_aprendiz.post(LOGOUT_URL)
    assert response.status_code == 200
    assert not Token.objects.filter(user=aprendiz).exists()


# ---------------------------------------------------------------------------
# Perfil
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_perfil_retorna_datos_usuario(client_aprendiz, aprendiz):
    response = client_aprendiz.get(PERFIL_URL)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == aprendiz.id
    assert data["rol"] == "APRENDIZ"


@pytest.mark.django_db
def test_perfil_sin_autenticacion_devuelve_401(api_client):
    response = api_client.get(PERFIL_URL)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Registro de usuarios
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_registro_aprendiz_exitoso(api_client):
    payload = {
        "email": "nuevo@soy.sena.edu.co",
        "password": "Sena1234!",
        "password2": "Sena1234!",
        "first_name": "Juan",
        "last_name": "Perez",
        "tipo_documento": "CC",
        "numero_documento": "12345001",
        "ficha": "2860001",
        "programa_formacion": "Analisis y Desarrollo de Software",
    }
    response = api_client.post(REGISTRO_URL, payload, format="json")
    assert response.status_code == 201
    assert Usuario.objects.filter(email=payload["email"]).exists()


@pytest.mark.django_db
def test_registro_contraseñas_no_coinciden(api_client):
    payload = {
        "email": "otro@soy.sena.edu.co",
        "password": "Sena1234!",
        "password2": "Diferente!",
        "first_name": "Ana",
        "last_name": "Lopez",
        "tipo_documento": "CC",
        "numero_documento": "99999002",
    }
    response = api_client.post(REGISTRO_URL, payload, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_registro_email_duplicado(api_client, aprendiz):
    payload = {
        "email": aprendiz.email,
        "password": "Sena1234!",
        "password2": "Sena1234!",
        "first_name": "Maria",
        "last_name": "Gomez",
        "tipo_documento": "CC",
        "numero_documento": "88888003",
    }
    response = api_client.post(REGISTRO_URL, payload, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_registro_dominio_invalido(api_client):
    payload = {
        "email": "usuario@hotmail.com",
        "password": "Sena1234!",
        "password2": "Sena1234!",
        "first_name": "Carlos",
        "last_name": "Ruiz",
        "tipo_documento": "CC",
        "numero_documento": "77777004",
    }
    response = api_client.post(REGISTRO_URL, payload, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_registro_instructor_queda_pendiente(api_client):
    payload = {
        "email": "instructor@sena.edu.co",
        "password": "Sena1234!",
        "password2": "Sena1234!",
        "first_name": "Luis",
        "last_name": "Torres",
        "tipo_documento": "CC",
        "numero_documento": "66666005",
        "rol_solicitado": "INSTRUCTOR",
    }
    response = api_client.post(REGISTRO_URL, payload, format="json")
    assert response.status_code == 201
    assert response.json()["estado_cuenta"] == "PENDIENTE"
    assert response.json()["token"] is None


# ---------------------------------------------------------------------------
# Verificar email
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_verificar_email_existente(api_client, aprendiz):
    response = api_client.get(f"/api/auth/usuarios/verificar_email/?email={aprendiz.email}")
    assert response.status_code == 200
    assert response.json()["exists"] is True


@pytest.mark.django_db
def test_verificar_email_no_existente(api_client):
    response = api_client.get("/api/auth/usuarios/verificar_email/?email=noexiste@soy.sena.edu.co")
    assert response.status_code == 200
    assert response.json()["exists"] is False


# ---------------------------------------------------------------------------
# Acciones de COORDINADOR_SST: pendientes, aprobar, rechazar, toggle_brigada
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_coordinador_lista_pendientes(client_coordinador, aprendiz):
    aprendiz.estado_cuenta = "PENDIENTE"
    aprendiz.save()
    response = client_coordinador.get("/api/auth/usuarios/pendientes/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.django_db
def test_no_coordinador_no_puede_ver_pendientes(client_aprendiz):
    response = client_aprendiz.get("/api/auth/usuarios/pendientes/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_coordinador_aprueba_usuario_pendiente(client_coordinador, instructor):
    instructor.estado_cuenta = "PENDIENTE"
    instructor.save()
    response = client_coordinador.post(
        f"/api/auth/usuarios/{instructor.id}/aprobar/",
        {"rol": "INSTRUCTOR"},
        format="json",
    )
    assert response.status_code == 200
    instructor.refresh_from_db()
    assert instructor.estado_cuenta == "ACTIVO"


@pytest.mark.django_db
def test_coordinador_rechaza_usuario_pendiente(client_coordinador, instructor):
    instructor.estado_cuenta = "PENDIENTE"
    instructor.save()
    response = client_coordinador.post(f"/api/auth/usuarios/{instructor.id}/rechazar/")
    assert response.status_code == 200
    instructor.refresh_from_db()
    assert instructor.estado_cuenta == "BLOQUEADO"


@pytest.mark.django_db
def test_coordinador_toggle_brigada(client_coordinador, aprendiz):
    aprendiz.es_brigada = False
    aprendiz.save()
    response = client_coordinador.patch(f"/api/auth/usuarios/{aprendiz.id}/brigada/")
    assert response.status_code == 200
    assert response.json()["es_brigada"] is True


# ---------------------------------------------------------------------------
# EstadisticasViewSet
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_estadisticas_dashboard(client_aprendiz):
    response = client_aprendiz.get("/api/auth/estadisticas/dashboard/")
    assert response.status_code == 200
    data = response.json()
    assert "acceso" in data
    assert "emergencias" in data


@pytest.mark.django_db
def test_estadisticas_acceso(client_administrativo):
    response = client_administrativo.get("/api/auth/estadisticas/acceso/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_estadisticas_emergencias(client_brigada):
    response = client_brigada.get("/api/auth/estadisticas/emergencias/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_estadisticas_incidentes(client_aprendiz):
    response = client_aprendiz.get("/api/auth/estadisticas/incidentes/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_estadisticas_no_leidas(client_aprendiz, aprendiz):
    from usuarios.tests.factories import NotificacionFactory

    NotificacionFactory.create_batch(2, destinatario=aprendiz, leida=False)
    response = client_aprendiz.get("/api/auth/notificaciones/no_leidas/")
    assert response.status_code == 200
    assert response.json()["count"] == 2

"""
Tests para usuarios/login_view.py — vista de login HTML (session-based).
"""

import pytest
from django.test import Client


LOGIN_URL = "/accounts/login/"


@pytest.mark.django_db
def test_login_get_muestra_formulario():
    response = Client().get(LOGIN_URL)
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_post_credenciales_correctas(aprendiz):
    aprendiz.set_password("TestPass123!")
    aprendiz.save()
    c = Client()
    response = c.post(LOGIN_URL, {"username": aprendiz.email, "password": "TestPass123!"})
    assert response.status_code == 302  # redirige tras login exitoso


@pytest.mark.django_db
def test_login_post_password_incorrecta(aprendiz):
    aprendiz.set_password("TestPass123!")
    aprendiz.save()
    c = Client()
    response = c.post(LOGIN_URL, {"username": aprendiz.email, "password": "wrongpassword"})
    assert response.status_code == 200
    assert "Correo o contraseña incorrectos" in response.content.decode()


@pytest.mark.django_db
def test_login_post_email_no_existe():
    c = Client()
    response = c.post(LOGIN_URL, {"username": "noexiste@sena.edu.co", "password": "cualquiera"})
    assert response.status_code == 200
    assert "Correo o contraseña incorrectos" in response.content.decode()


@pytest.mark.django_db
def test_login_post_cuenta_pendiente(aprendiz):
    aprendiz.estado_cuenta = "PENDIENTE"
    aprendiz.save()
    c = Client()
    response = c.post(LOGIN_URL, {"username": aprendiz.email, "password": "cualquiera"})
    assert response.status_code == 200
    assert "pendiente" in response.content.decode().lower()


@pytest.mark.django_db
def test_login_post_cuenta_bloqueada(aprendiz):
    aprendiz.set_password("TestPass123!")
    aprendiz.estado_cuenta = "BLOQUEADO"
    aprendiz.save()
    c = Client()
    response = c.post(LOGIN_URL, {"username": aprendiz.email, "password": "TestPass123!"})
    assert response.status_code == 200
    assert "bloqueada" in response.content.decode().lower()


@pytest.mark.django_db
def test_login_post_usuario_inactivo(aprendiz):
    aprendiz.set_password("TestPass123!")
    aprendiz.activo = False
    aprendiz.save()
    c = Client()
    response = c.post(LOGIN_URL, {"username": aprendiz.email, "password": "TestPass123!"})
    assert response.status_code == 200

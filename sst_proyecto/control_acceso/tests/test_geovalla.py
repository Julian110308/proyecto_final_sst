"""
Tests 2.3: Geocerca — Haversine y auto-registro.
"""

import pytest
from mapas.services import calcular_distancia
from control_acceso.models import Geocerca, RegistroAcceso


# ---------------------------------------------------------------------------
# Tests unitarios de la fórmula Haversine (sin DB)
# ---------------------------------------------------------------------------


def test_haversine_mismo_punto_es_cero():
    distancia = calcular_distancia(5.7303596, -72.8943613, 5.7303596, -72.8943613)
    assert distancia == 0.0


def test_haversine_distancia_conocida():
    """Bogotá → Medellín ≈ 238 km (tolerancia ±10 km)."""
    lat1, lon1 = 4.7110, -74.0721  # Bogotá
    lat2, lon2 = 6.2442, -75.5812  # Medellín
    distancia_km = calcular_distancia(lat1, lon1, lat2, lon2) / 1000
    assert 230 <= distancia_km <= 248


def test_haversine_distancia_corta():
    """100 metros al norte del centro → debe ser ≈ 111 m (tolerancia ±5 m)."""
    lat_centro = 5.7303596
    lon_centro = -72.8943613
    # ~0.0009 grados de lat ≈ 100 m
    lat_norte = lat_centro + 0.0009
    distancia = calcular_distancia(lat_centro, lon_centro, lat_norte, lon_centro)
    assert 95 <= distancia <= 115


# ---------------------------------------------------------------------------
# Tests de Geocerca.punto_esta_dentro
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_punto_dentro_geocerca(geocerca):
    # El centro mismo debe estar dentro
    assert geocerca.punto_esta_dentro(geocerca.centro_latitud, geocerca.centro_longitud) is True


@pytest.mark.django_db
def test_punto_fuera_geocerca(geocerca):
    # 1 km al norte → fuera del radio de 200 m
    lat_fuera = geocerca.centro_latitud + 0.01
    assert geocerca.punto_esta_dentro(lat_fuera, geocerca.centro_longitud) is False


@pytest.mark.django_db
def test_verificar_ubicacion_usuario_dentro(geocerca):
    resultado = Geocerca.verificar_ubicacion_usuario(geocerca.centro_latitud, geocerca.centro_longitud)
    assert resultado is not None


@pytest.mark.django_db
def test_verificar_ubicacion_usuario_fuera(geocerca):
    lat_fuera = geocerca.centro_latitud + 0.02
    resultado = Geocerca.verificar_ubicacion_usuario(lat_fuera, geocerca.centro_longitud)
    assert resultado is None


# ---------------------------------------------------------------------------
# Tests del endpoint auto-registro
# ---------------------------------------------------------------------------

AUTO_URL = "/api/acceso/registros/auto-registro/"


@pytest.mark.django_db
def test_auto_registro_dentro_crea_ingreso(client_aprendiz, geocerca):
    payload = {
        "latitud": geocerca.centro_latitud,
        "longitud": geocerca.centro_longitud,
    }
    response = client_aprendiz.post(AUTO_URL, payload, format="json")
    assert response.status_code == 200
    data = response.json()
    assert data["estado"] == "DENTRO"
    assert data["accion"] == "INGRESO"
    assert RegistroAcceso.objects.count() == 1


@pytest.mark.django_db
def test_auto_registro_fuera_no_crea_registro(client_aprendiz, geocerca):
    lat_fuera = geocerca.centro_latitud + 0.02
    payload = {"latitud": lat_fuera, "longitud": geocerca.centro_longitud}
    response = client_aprendiz.post(AUTO_URL, payload, format="json")
    assert response.status_code == 200
    assert response.json()["estado"] == "FUERA"
    assert RegistroAcceso.objects.count() == 0


@pytest.mark.django_db
def test_auto_registro_sin_coordenadas_devuelve_400(client_aprendiz, geocerca):
    response = client_aprendiz.post(AUTO_URL, {}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_auto_registro_sin_autenticacion_devuelve_401(api_client):
    response = api_client.post(AUTO_URL, {"latitud": 5.73, "longitud": -72.89}, format="json")
    assert response.status_code == 401

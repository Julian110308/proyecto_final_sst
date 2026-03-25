"""
Tests para reportes/views_incidentes.py — vistas de template de incidentes.
"""

import io
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from reportes.models import Incidente


LIST_URL = "/reportes/incidentes/"
NEW_URL = "/reportes/incidentes/nuevo/"


def _fake_image():
    """Crea una imagen PNG 1×1 válida para pasar clean_foto."""
    from PIL import Image

    buf = io.BytesIO()
    img = Image.new("RGB", (1, 1), color=(255, 0, 0))
    img.save(buf, format="PNG")
    buf.seek(0)
    return SimpleUploadedFile("test.png", buf.read(), content_type="image/png")


def _post_incidente_payload(extra=None):
    from django.utils import timezone

    payload = {
        "titulo": "Incidente de prueba completo",
        "descripcion": "Descripcion detallada del incidente ocurrido en el centro",
        "tipo": "OTRO",
        "gravedad": "MEDIA",
        "area_incidente": "OTRO",
        "fecha_incidente": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        "foto": _fake_image(),
    }
    if extra:
        payload.update(extra)
    return payload


def _crear_incidente(usuario, gravedad="MEDIA", estado="REPORTADO"):
    return Incidente.objects.create(
        titulo="Incidente de prueba",
        descripcion="Descripción de prueba",
        tipo="OTRO",
        gravedad=gravedad,
        estado=estado,
        area_incidente="OTRO",
        reportado_por=usuario,
    )


# ---------------------------------------------------------------------------
# listar_incidentes
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_listar_incidentes_aprendiz_ve_solo_los_suyos(django_client_aprendiz, aprendiz, administrativo):
    _crear_incidente(aprendiz)
    _crear_incidente(administrativo)
    response = django_client_aprendiz.get(LIST_URL)
    assert response.status_code == 200
    # Solo 1 incidente propio en el contexto
    assert response.context["total"] == 1


@pytest.mark.django_db
def test_listar_incidentes_admin_ve_todos(django_client_administrativo, aprendiz, administrativo):
    _crear_incidente(aprendiz)
    _crear_incidente(administrativo)
    response = django_client_administrativo.get(LIST_URL)
    assert response.status_code == 200
    assert response.context["total"] == 2


@pytest.mark.django_db
def test_listar_incidentes_con_filtro_estado(django_client_aprendiz, aprendiz):
    _crear_incidente(aprendiz, estado="REPORTADO")
    _crear_incidente(aprendiz, estado="RESUELTO")
    response = django_client_aprendiz.get(LIST_URL + "?estado=REPORTADO")
    assert response.status_code == 200
    assert response.context["total"] == 1


@pytest.mark.django_db
def test_listar_incidentes_con_filtro_q(django_client_aprendiz, aprendiz):
    Incidente.objects.create(
        titulo="Caída en escalera",
        descripcion="desc",
        tipo="OTRO",
        gravedad="MEDIA",
        estado="REPORTADO",
        area_incidente="OTRO",
        reportado_por=aprendiz,
    )
    Incidente.objects.create(
        titulo="Fuego en taller",
        descripcion="desc",
        tipo="OTRO",
        gravedad="MEDIA",
        estado="REPORTADO",
        area_incidente="OTRO",
        reportado_por=aprendiz,
    )
    response = django_client_aprendiz.get(LIST_URL + "?q=escalera")
    assert response.status_code == 200
    assert response.context["total"] == 1


@pytest.mark.django_db
def test_listar_incidentes_requiere_login(client):
    response = client.get(LIST_URL)
    assert response.status_code == 302  # redirige a login


# ---------------------------------------------------------------------------
# crear_incidente
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_crear_incidente_get_muestra_form(django_client_aprendiz):
    response = django_client_aprendiz.get(NEW_URL)
    assert response.status_code == 200
    assert "form" in response.context


@pytest.mark.django_db
def test_crear_incidente_post_exitoso(django_client_aprendiz, aprendiz):
    payload = {
        "titulo": "Nuevo incidente prueba",
        "descripcion": "Descripción detallada del incidente ocurrido",
        "tipo": "OTRO",
        "gravedad": "MEDIA",
        "area_incidente": "OTRO",
        "fecha_incidente": "2026-03-13 10:00:00",
        "foto": _fake_image(),
    }
    response = django_client_aprendiz.post(NEW_URL, payload)
    assert response.status_code == 302  # redirige tras crear
    assert Incidente.objects.filter(titulo="Nuevo incidente prueba", reportado_por=aprendiz).exists()


@pytest.mark.django_db
def test_crear_incidente_critico_notifica(django_client_administrativo, administrativo):
    payload = {
        "titulo": "Incidente crítico grave",
        "descripcion": "Descripción detallada del incidente crítico ocurrido",
        "tipo": "ACCIDENTE",
        "gravedad": "CRITICA",
        "area_incidente": "TALLER",
        "fecha_incidente": "2026-03-13 10:00:00",
        "foto": _fake_image(),
    }
    response = django_client_administrativo.post(NEW_URL, payload)
    assert response.status_code == 302
    assert Incidente.objects.filter(gravedad="CRITICA").exists()


# ---------------------------------------------------------------------------
# detalle_incidente
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_detalle_incidente_propietario(django_client_aprendiz, aprendiz):
    inc = _crear_incidente(aprendiz)
    response = django_client_aprendiz.get(f"/reportes/incidentes/{inc.pk}/")
    assert response.status_code == 200
    assert response.context["incidente"].pk == inc.pk


@pytest.mark.django_db
def test_detalle_incidente_admin_ve_cualquiera(django_client_administrativo, aprendiz):
    inc = _crear_incidente(aprendiz)
    response = django_client_administrativo.get(f"/reportes/incidentes/{inc.pk}/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_detalle_incidente_otro_aprendiz_redirige(django_client_aprendiz, administrativo):
    """Un aprendiz no puede ver incidente de otro usuario."""
    inc = _crear_incidente(administrativo)
    response = django_client_aprendiz.get(f"/reportes/incidentes/{inc.pk}/")
    assert response.status_code == 302


# ---------------------------------------------------------------------------
# actualizar_incidente
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_actualizar_incidente_get_admin(django_client_administrativo, aprendiz):
    inc = _crear_incidente(aprendiz)
    response = django_client_administrativo.get(f"/reportes/incidentes/{inc.pk}/actualizar/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_actualizar_incidente_post_cambia_estado(django_client_administrativo, aprendiz):
    inc = _crear_incidente(aprendiz)
    response = django_client_administrativo.post(
        f"/reportes/incidentes/{inc.pk}/actualizar/",
        {"estado": "EN_REVISION"},
    )
    assert response.status_code == 302
    inc.refresh_from_db()
    assert inc.estado == "EN_REVISION"


@pytest.mark.django_db
def test_actualizar_incidente_aprendiz_es_redirigido(django_client_aprendiz, aprendiz):
    inc = _crear_incidente(aprendiz)
    response = django_client_aprendiz.get(f"/reportes/incidentes/{inc.pk}/actualizar/")
    assert response.status_code == 302


@pytest.mark.django_db
def test_actualizar_incidente_marcar_resuelto(django_client_administrativo, aprendiz):
    inc = _crear_incidente(aprendiz)
    response = django_client_administrativo.post(
        f"/reportes/incidentes/{inc.pk}/actualizar/",
        {"estado": "RESUELTO", "marcar_resuelto": "1"},
    )
    assert response.status_code == 302
    inc.refresh_from_db()
    assert inc.fecha_resolucion is not None

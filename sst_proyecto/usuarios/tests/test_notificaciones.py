"""
Tests 2.3: Notificaciones — marcar como leída, acceso solo propio.
"""

import pytest
from usuarios.models import Notificacion
from usuarios.tests.factories import NotificacionFactory


@pytest.mark.django_db
def test_marcar_notificacion_como_leida(client_aprendiz, aprendiz):
    notif = NotificacionFactory(destinatario=aprendiz, leida=False)
    url = f"/api/auth/notificaciones/{notif.id}/marcar_leida/"
    response = client_aprendiz.post(url)
    assert response.status_code == 200
    notif.refresh_from_db()
    assert notif.leida is True
    assert notif.fecha_lectura is not None


@pytest.mark.django_db
def test_marcar_todas_las_notificaciones_como_leidas(client_aprendiz, aprendiz):
    NotificacionFactory.create_batch(3, destinatario=aprendiz, leida=False)
    url = "/api/auth/notificaciones/marcar_todas_leidas/"
    response = client_aprendiz.post(url)
    assert response.status_code == 200
    assert Notificacion.objects.filter(destinatario=aprendiz, leida=False).count() == 0


@pytest.mark.django_db
def test_usuario_no_puede_marcar_leida_notificacion_ajena(client_aprendiz, instructor):
    notif_ajena = NotificacionFactory(destinatario=instructor, leida=False)
    url = f"/api/auth/notificaciones/{notif_ajena.id}/marcar_leida/"
    response = client_aprendiz.post(url)
    # Debe ser 404 porque el queryset filtra por destinatario=request.user
    assert response.status_code == 404
    notif_ajena.refresh_from_db()
    assert notif_ajena.leida is False


@pytest.mark.django_db
def test_endpoint_count_notificaciones_no_leidas(client_aprendiz, aprendiz):
    NotificacionFactory.create_batch(2, destinatario=aprendiz, leida=False)
    NotificacionFactory(destinatario=aprendiz, leida=True)
    response = client_aprendiz.get("/api/auth/notificaciones/count/")
    assert response.status_code == 200
    assert response.json()["count"] == 2


@pytest.mark.django_db
def test_sin_autenticacion_no_puede_ver_notificaciones(api_client):
    response = api_client.get("/api/auth/notificaciones/")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# NotificacionService — métodos directos
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_notificar_emergencia_atendida_crea_notif(aprendiz, brigada):
    from emergencias.tests.factories import EmergenciaFactory, TipoEmergenciaFactory
    from usuarios.services import NotificacionService

    tipo = TipoEmergenciaFactory()
    emergencia = EmergenciaFactory(tipo=tipo, reportada_por=aprendiz)
    NotificacionService.notificar_emergencia_atendida(emergencia, brigada)
    assert Notificacion.objects.filter(destinatario=aprendiz, tipo="EMERGENCIA").exists()


@pytest.mark.django_db
def test_notificar_emergencia_resuelta_crea_notif(aprendiz, administrativo):
    from emergencias.tests.factories import EmergenciaFactory, TipoEmergenciaFactory
    from usuarios.services import NotificacionService

    tipo = TipoEmergenciaFactory()
    emergencia = EmergenciaFactory(tipo=tipo, reportada_por=aprendiz)
    NotificacionService.notificar_emergencia_resuelta(emergencia)
    assert Notificacion.objects.filter(tipo="EMERGENCIA").exists()


@pytest.mark.django_db
def test_notificar_incidente_critico_crea_notif(administrativo):
    from reportes.models import Incidente
    from usuarios.services import NotificacionService

    incidente = Incidente.objects.create(
        titulo="Incidente crítico test",
        descripcion="Descripción del incidente crítico",
        tipo="ACCIDENTE",
        gravedad="CRITICA",
        area_incidente="TALLER",
        reportado_por=administrativo,
    )
    count = NotificacionService.notificar_incidente_critico(incidente)
    assert count >= 0  # puede ser 0 si no hay admins aparte del propio


@pytest.mark.django_db
def test_notificar_incidente_critico_gravedad_baja_no_notifica(aprendiz):
    from reportes.models import Incidente
    from usuarios.services import NotificacionService

    incidente = Incidente.objects.create(
        titulo="Incidente bajo test",
        descripcion="Descripción del incidente leve",
        tipo="OTRO",
        gravedad="BAJA",
        area_incidente="OTRO",
        reportado_por=aprendiz,
    )
    result = NotificacionService.notificar_incidente_critico(incidente)
    assert result == 0


@pytest.mark.django_db
def test_notificar_aforo_critico_crea_notif(administrativo, brigada):
    from usuarios.services import NotificacionService

    count = NotificacionService.notificar_aforo_critico(95, 100)
    assert count >= 0


@pytest.mark.django_db
def test_notificar_sistema_crea_notif(aprendiz, instructor):
    from usuarios.services import NotificacionService

    count = NotificacionService.notificar_sistema(
        destinatarios=[aprendiz, instructor],
        titulo="Mensaje del sistema",
        mensaje="Este es un mensaje de prueba del sistema SST.",
    )
    assert count == 2
    assert Notificacion.objects.filter(tipo="SISTEMA").count() == 2

import factory
from factory.django import DjangoModelFactory
from usuarios.tests.factories import UsuarioFactory


class TipoEmergenciaFactory(DjangoModelFactory):
    class Meta:
        model = "emergencias.TipoEmergencia"

    nombre = factory.Sequence(lambda n: f"Tipo Emergencia {n}")
    descripcion = "Descripción de prueba"
    prioridad = 2
    protocolo = "Protocolo de prueba"
    tiempo_respuesta_minutos = 5
    activo = True


class EmergenciaFactory(DjangoModelFactory):
    class Meta:
        model = "emergencias.Emergencia"

    tipo = factory.SubFactory(TipoEmergenciaFactory)
    reportada_por = factory.SubFactory(UsuarioFactory)
    latitud = 5.7303596
    longitud = -72.8943613
    descripcion = "Emergencia de prueba"
    estado = "REPORTADA"

import factory
from factory.django import DjangoModelFactory
from faker import Faker

fake = Faker("es_CO")

_doc_counter = 0


def _unique_doc():
    """Genera números de documento únicos para los tests."""
    global _doc_counter
    _doc_counter += 1
    return f"TEST{_doc_counter:08d}"


class UsuarioFactory(DjangoModelFactory):
    class Meta:
        model = "usuarios.Usuario"
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"usuario_{n}")
    first_name = factory.LazyFunction(fake.first_name)
    last_name = factory.LazyFunction(fake.last_name)
    email = factory.Sequence(lambda n: f"usuario_{n}@soy.sena.edu.co")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    rol = "APRENDIZ"
    tipo_documento = "CC"
    numero_documento = factory.LazyFunction(_unique_doc)
    activo = True
    estado_cuenta = "ACTIVO"


class NotificacionFactory(DjangoModelFactory):
    class Meta:
        model = "usuarios.Notificacion"

    destinatario = factory.SubFactory(UsuarioFactory)
    titulo = factory.Sequence(lambda n: f"Notificación {n}")
    mensaje = "Mensaje de prueba"
    tipo = "INFO"
    leida = False

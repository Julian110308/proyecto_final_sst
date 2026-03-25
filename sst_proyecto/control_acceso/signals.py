from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import invalidar_cache_acceso


@receiver(post_save, sender="control_acceso.RegistroAcceso")
def invalidar_cache_al_registrar_acceso(sender, instance, **kwargs):
    """Cuando se registra un ingreso o egreso, invalida el caché de aforo y estadísticas."""
    invalidar_cache_acceso()

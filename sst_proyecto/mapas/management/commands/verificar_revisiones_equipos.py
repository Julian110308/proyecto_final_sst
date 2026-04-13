"""
Comando para verificar equipos con revision pendiente y notificar a la Brigada.

Uso manual:
    cd sst_proyecto
    python manage.py verificar_revisiones_equipos

Programar en Windows Task Scheduler (una vez al dia, por ejemplo a las 7:00 AM):
    1. Abrir "Programador de tareas" en Windows
    2. Crear tarea basica > Diariamente > a las 07:00
    3. Accion: Iniciar un programa
       Programa: C:\\ruta\\al\\entorno\\Scripts\\python.exe
       Argumentos: manage.py verificar_revisiones_equipos
       Iniciar en: C:\\ruta\\al\\proyecto\\sst_proyecto
"""

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Verifica equipos con revision pendiente y notifica a la Brigada"

    def handle(self, *args, **options):
        from usuarios.services import NotificacionService

        self.stdout.write(f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] Verificando revisiones de equipos...")

        try:
            total = NotificacionService.notificar_revision_hoy()
            if total:
                self.stdout.write(self.style.SUCCESS(f"{total} notificacion(es) enviadas a la brigada."))
            else:
                self.stdout.write(
                    self.style.WARNING("No hay equipos con revision pendiente para hoy (o ya fueron notificados).")
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al verificar revisiones: {e}"))

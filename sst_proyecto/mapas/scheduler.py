from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore


def verificar_revisiones_equipos():
    """Verifica equipos con revision pendiente y notifica a la Brigada."""
    from usuarios.services import NotificacionService

    total = NotificacionService.notificar_revision_hoy()
    if total:
        print(f"[Scheduler] {total} notificacion(es) de revision enviadas a la brigada.")
    else:
        print("[Scheduler] Sin equipos pendientes de revision para hoy.")


def desactivar_cuentas_visitantes():
    """Desactiva todas las cuentas de visitantes al finalizar el día."""
    from usuarios.models import Usuario

    total = Usuario.objects.filter(rol="VISITANTE", activo=True).update(activo=False, is_active=False)
    if total:
        print(f"[Scheduler] {total} cuenta(s) de visitante desactivadas al finalizar el día.")


def iniciar_scheduler():
    scheduler = BackgroundScheduler(timezone="America/Bogota")
    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
        verificar_revisiones_equipos,
        trigger=CronTrigger(hour=7, minute=0),
        id="verificar_revisiones_equipos",
        name="Notificar revisiones de equipos a la Brigada",
        jobstore="default",
        replace_existing=True,
    )

    scheduler.add_job(
        desactivar_cuentas_visitantes,
        trigger=CronTrigger(hour=23, minute=59),
        id="desactivar_cuentas_visitantes",
        name="Desactivar cuentas de visitantes al finalizar el día",
        jobstore="default",
        replace_existing=True,
    )

    scheduler.start()
    print(
        "[Scheduler] Iniciado — revisiones de equipos a las 7:00 AM, cuentas de visitantes se desactivan a las 11:59 PM."
    )

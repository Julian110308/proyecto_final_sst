"""
Tareas de Celery para generación de reportes programados.

Configurar en celery.py:
    from celery.schedules import crontab

    app.conf.beat_schedule = {
        'generar-reportes-diarios': {
            'task': 'reportes.tasks.generar_reportes_programados',
            'schedule': crontab(hour=6, minute=0),  # 6:00 AM todos los días
        },
    }
"""

from celery import shared_task
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generar_reportes_programados(self):
    """
    Genera todos los reportes que están configurados como activos
    según su frecuencia.
    """
    from reportes.models import ConfiguracionReporte, ReporteGenerado
    from reportes.services import (
        ReporteAforoService,
        ReporteIncidentesService,
        ReporteAsistenciaService,
        ReporteSeguridadService
    )
    from reportes.pdf_generator import PDFReporteGenerator
    from usuarios.models import Usuario

    logger.info('Iniciando generación de reportes programados')

    configuraciones = ConfiguracionReporte.objects.filter(activo=True)
    reportes_generados = 0
    errores = []

    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)

    for config in configuraciones:
        try:
            # Verificar si es momento de generar
            if not debe_generar_reporte(config):
                continue

            logger.info(f'Generando reporte: {config.nombre}')

            # Generar según tipo
            periodo_inicio = datetime.combine(fecha_inicio, datetime.min.time())
            periodo_fin = datetime.combine(fecha_fin, datetime.max.time())

            if config.tipo_reporte == 'AFORO':
                datos = ReporteAforoService.generar_reporte(periodo_inicio, periodo_fin)
                buffer = PDFReporteGenerator.generar_reporte_aforo(datos)
            elif config.tipo_reporte == 'INCIDENTES':
                datos = ReporteIncidentesService.generar_reporte(periodo_inicio, periodo_fin)
                buffer = PDFReporteGenerator.generar_reporte_incidentes(datos)
            elif config.tipo_reporte == 'SEGURIDAD':
                datos = ReporteSeguridadService.generar_reporte(periodo_inicio, periodo_fin)
                buffer = PDFReporteGenerator.generar_reporte_seguridad(datos)
            else:
                logger.warning(f'Tipo de reporte no soportado: {config.tipo_reporte}')
                continue

            # Guardar en BD
            usuario = Usuario.objects.filter(is_superuser=True).first()
            if not usuario:
                usuario = Usuario.objects.filter(rol='ADMINISTRATIVO').first()

            if usuario:
                ReporteGenerado.objects.create(
                    configuracion=config,
                    periodo_inicio=periodo_inicio,
                    periodo_fin=periodo_fin,
                    datos_json=datos,
                    generado_por=usuario
                )

            # Actualizar última generación
            config.ultima_generacion = timezone.now()
            config.save()

            # Enviar por email si hay destinatarios
            if config.destinatarios.exists():
                enviar_reporte_email.delay(
                    config.id,
                    buffer.getvalue(),
                    f'reporte_{config.tipo_reporte.lower()}_{fecha_inicio}_{fecha_fin}.pdf'
                )

            reportes_generados += 1
            logger.info(f'Reporte generado exitosamente: {config.nombre}')

        except Exception as e:
            error_msg = f'Error generando {config.nombre}: {str(e)}'
            logger.error(error_msg)
            errores.append(error_msg)

    resultado = {
        'reportes_generados': reportes_generados,
        'errores': errores,
        'timestamp': timezone.now().isoformat()
    }

    logger.info(f'Generación completada: {reportes_generados} reportes, {len(errores)} errores')
    return resultado


@shared_task
def enviar_reporte_email(config_id, pdf_bytes, filename):
    """
    Envía un reporte por email a los destinatarios configurados.
    """
    from reportes.models import ConfiguracionReporte

    try:
        config = ConfiguracionReporte.objects.get(id=config_id)
        destinatarios = config.destinatarios.all()

        if not destinatarios.exists():
            logger.info(f'No hay destinatarios para {config.nombre}')
            return

        emails = [d.email for d in destinatarios if d.email]

        if not emails:
            logger.warning(f'Los destinatarios de {config.nombre} no tienen email')
            return

        subject = f'[SST] Reporte Automático: {config.nombre}'
        body = f"""
Reporte generado automáticamente por el Sistema SST.

Nombre: {config.nombre}
Tipo: {config.get_tipo_reporte_display()}
Frecuencia: {config.get_frecuencia_display()}
Fecha de generación: {timezone.now().strftime('%d/%m/%Y %H:%M')}

El archivo adjunto contiene los datos del reporte.

---
Sistema SST - Centro Minero SENA
Este es un correo automático, no responda a este mensaje.
        """

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=emails
        )

        email.attach(filename, pdf_bytes, 'application/pdf')
        email.send()

        logger.info(f'Email enviado para {config.nombre} a {len(emails)} destinatarios')

    except ConfiguracionReporte.DoesNotExist:
        logger.error(f'Configuración de reporte no encontrada: {config_id}')
    except Exception as e:
        logger.error(f'Error enviando email: {str(e)}')


@shared_task
def generar_reporte_individual(tipo, formato, fecha_inicio_str, fecha_fin_str, ficha=None, usuario_id=None):
    """
    Genera un reporte individual de forma asíncrona.
    Útil para reportes grandes que tardan en generarse.
    """
    from reportes.models import ConfiguracionReporte, ReporteGenerado
    from reportes.services import (
        ReporteAforoService,
        ReporteIncidentesService,
        ReporteAsistenciaService,
        ReporteSeguridadService
    )
    from reportes.pdf_generator import PDFReporteGenerator
    from reportes.excel_generator import ExcelReporteGenerator
    from reportes.csv_generator import CSVReporteGenerator
    from usuarios.models import Usuario

    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d')

        periodo_inicio = datetime.combine(fecha_inicio, datetime.min.time())
        periodo_fin = datetime.combine(fecha_fin, datetime.max.time())

        # Generar datos
        if tipo == 'aforo':
            datos = ReporteAforoService.generar_reporte(periodo_inicio, periodo_fin)
        elif tipo == 'incidentes':
            datos = ReporteIncidentesService.generar_reporte(periodo_inicio, periodo_fin)
        elif tipo == 'asistencia':
            if not ficha:
                return {'error': 'Se requiere ficha para reporte de asistencia'}
            datos = ReporteAsistenciaService.generar_reporte(ficha, periodo_inicio, periodo_fin)
        elif tipo == 'seguridad':
            datos = ReporteSeguridadService.generar_reporte(periodo_inicio, periodo_fin)
        else:
            return {'error': f'Tipo de reporte no válido: {tipo}'}

        # Generar archivo
        if formato == 'pdf':
            generator = PDFReporteGenerator
        elif formato == 'excel':
            generator = ExcelReporteGenerator
        elif formato == 'csv':
            generator = CSVReporteGenerator
        else:
            return {'error': f'Formato no válido: {formato}'}

        generator_method = getattr(generator, f'generar_reporte_{tipo}')
        buffer = generator_method(datos)

        # Guardar en BD
        config, _ = ConfiguracionReporte.objects.get_or_create(
            nombre=f'Reporte {tipo.title()} Async',
            tipo_reporte=tipo.upper(),
            defaults={'frecuencia': 'DIARIO', 'activo': False}
        )

        usuario = None
        if usuario_id:
            usuario = Usuario.objects.filter(id=usuario_id).first()
        if not usuario:
            usuario = Usuario.objects.filter(is_superuser=True).first()

        if usuario:
            reporte = ReporteGenerado.objects.create(
                configuracion=config,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                datos_json=datos,
                generado_por=usuario
            )

            return {
                'success': True,
                'reporte_id': reporte.id,
                'tipo': tipo,
                'formato': formato
            }

        return {'success': True, 'tipo': tipo, 'formato': formato}

    except Exception as e:
        logger.error(f'Error generando reporte async: {str(e)}')
        return {'error': str(e)}


def debe_generar_reporte(config):
    """
    Verifica si es momento de generar el reporte según la frecuencia configurada.
    """
    if not config.ultima_generacion:
        return True

    ahora = timezone.now()
    ultima = config.ultima_generacion

    if config.frecuencia == 'DIARIO':
        return (ahora - ultima).days >= 1
    elif config.frecuencia == 'SEMANAL':
        return (ahora - ultima).days >= 7
    elif config.frecuencia == 'MENSUAL':
        return (ahora - ultima).days >= 30

    return True

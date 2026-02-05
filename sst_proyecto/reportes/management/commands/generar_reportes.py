"""
Comando de Django para generar reportes programados.

Uso:
    python manage.py generar_reportes
    python manage.py generar_reportes --tipo aforo --formato pdf
    python manage.py generar_reportes --todos --enviar-email

Este comando puede ser ejecutado mediante cron o Celery para automatizar
la generación de reportes.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from datetime import datetime, timedelta
import os

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


class Command(BaseCommand):
    help = 'Genera reportes programados según la configuración en ConfiguracionReporte'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tipo',
            type=str,
            choices=['aforo', 'incidentes', 'asistencia', 'seguridad'],
            help='Tipo de reporte a generar'
        )
        parser.add_argument(
            '--formato',
            type=str,
            default='pdf',
            choices=['pdf', 'excel', 'csv'],
            help='Formato del reporte (default: pdf)'
        )
        parser.add_argument(
            '--fecha-inicio',
            type=str,
            help='Fecha de inicio (YYYY-MM-DD). Default: hace 30 días'
        )
        parser.add_argument(
            '--fecha-fin',
            type=str,
            help='Fecha de fin (YYYY-MM-DD). Default: hoy'
        )
        parser.add_argument(
            '--ficha',
            type=str,
            help='Número de ficha (requerido para reporte de asistencia)'
        )
        parser.add_argument(
            '--todos',
            action='store_true',
            help='Genera todos los reportes configurados como activos'
        )
        parser.add_argument(
            '--enviar-email',
            action='store_true',
            help='Envía los reportes por email a los destinatarios configurados'
        )
        parser.add_argument(
            '--guardar',
            action='store_true',
            help='Guarda el reporte en la base de datos'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='media/reportes/generados',
            help='Directorio donde guardar los archivos generados'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO(
            f'[{timezone.now().strftime("%Y-%m-%d %H:%M:%S")}] Iniciando generación de reportes...'
        ))

        # Fechas por defecto
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=30)

        if options['fecha_inicio']:
            try:
                fecha_inicio = datetime.strptime(options['fecha_inicio'], '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('Formato de fecha inválido. Use YYYY-MM-DD')

        if options['fecha_fin']:
            try:
                fecha_fin = datetime.strptime(options['fecha_fin'], '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('Formato de fecha inválido. Use YYYY-MM-DD')

        # Crear directorio de salida si no existe
        output_dir = options['output_dir']
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if options['todos']:
            # Generar reportes según configuración activa
            self._generar_reportes_programados(options, fecha_inicio, fecha_fin, output_dir)
        elif options['tipo']:
            # Generar reporte específico
            self._generar_reporte_individual(
                options['tipo'],
                options['formato'],
                fecha_inicio,
                fecha_fin,
                options.get('ficha'),
                options['guardar'],
                options['enviar_email'],
                output_dir
            )
        else:
            self.stdout.write(self.style.WARNING(
                'Especifique --tipo o --todos para generar reportes'
            ))

        self.stdout.write(self.style.SUCCESS('Generación de reportes completada.'))

    def _generar_reportes_programados(self, options, fecha_inicio, fecha_fin, output_dir):
        """Genera reportes según las configuraciones activas"""
        configuraciones = ConfiguracionReporte.objects.filter(activo=True)

        if not configuraciones.exists():
            self.stdout.write(self.style.WARNING(
                'No hay configuraciones de reportes activas'
            ))
            return

        for config in configuraciones:
            self.stdout.write(f'Procesando: {config.nombre}')

            # Verificar si es hora de generar según frecuencia
            if not self._debe_generar(config):
                self.stdout.write(f'  - Saltando (no es momento de generar)')
                continue

            # Mapear tipo de reporte
            tipo_map = {
                'AFORO': 'aforo',
                'INCIDENTES': 'incidentes',
                'ASISTENCIA': 'asistencia',
                'SEGURIDAD': 'seguridad',
                'EQUIPAMIENTO': 'seguridad'
            }

            tipo = tipo_map.get(config.tipo_reporte)
            if not tipo:
                self.stdout.write(self.style.WARNING(
                    f'  - Tipo de reporte no soportado: {config.tipo_reporte}'
                ))
                continue

            # Generar reporte
            self._generar_reporte_individual(
                tipo,
                'pdf',
                fecha_inicio,
                fecha_fin,
                None,  # ficha
                True,  # guardar
                options['enviar_email'],
                output_dir,
                config
            )

            # Actualizar última generación
            config.ultima_generacion = timezone.now()
            config.save()

    def _debe_generar(self, config):
        """Verifica si es momento de generar el reporte según la frecuencia"""
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

    def _generar_reporte_individual(self, tipo, formato, fecha_inicio, fecha_fin,
                                    ficha, guardar, enviar_email, output_dir, config=None):
        """Genera un reporte individual"""
        self.stdout.write(f'Generando reporte de {tipo}...')

        # Obtener datos según tipo
        periodo_inicio = datetime.combine(fecha_inicio, datetime.min.time())
        periodo_fin = datetime.combine(fecha_fin, datetime.max.time())

        try:
            if tipo == 'aforo':
                datos = ReporteAforoService.generar_reporte(periodo_inicio, periodo_fin)
            elif tipo == 'incidentes':
                datos = ReporteIncidentesService.generar_reporte(periodo_inicio, periodo_fin)
            elif tipo == 'asistencia':
                if not ficha:
                    self.stdout.write(self.style.WARNING(
                        '  - Se requiere --ficha para reportes de asistencia'
                    ))
                    return
                datos = ReporteAsistenciaService.generar_reporte(ficha, periodo_inicio, periodo_fin)
            elif tipo == 'seguridad':
                datos = ReporteSeguridadService.generar_reporte(periodo_inicio, periodo_fin)
            else:
                raise CommandError(f'Tipo de reporte no válido: {tipo}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  - Error generando datos: {str(e)}'))
            return

        # Generar archivo según formato
        try:
            if formato == 'pdf':
                generator_method = getattr(PDFReporteGenerator, f'generar_reporte_{tipo}')
                buffer = generator_method(datos)
                extension = 'pdf'
                content_type = 'application/pdf'
            elif formato == 'excel':
                generator_method = getattr(ExcelReporteGenerator, f'generar_reporte_{tipo}')
                buffer = generator_method(datos)
                extension = 'xlsx'
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif formato == 'csv':
                generator_method = getattr(CSVReporteGenerator, f'generar_reporte_{tipo}')
                buffer = generator_method(datos)
                extension = 'csv'
                content_type = 'text/csv'
            else:
                raise CommandError(f'Formato no válido: {formato}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  - Error generando archivo: {str(e)}'))
            return

        # Guardar archivo
        filename = f'reporte_{tipo}_{fecha_inicio}_{fecha_fin}.{extension}'
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(buffer.getvalue())

        self.stdout.write(self.style.SUCCESS(f'  - Archivo guardado: {filepath}'))

        # Guardar en base de datos
        if guardar:
            self._guardar_reporte_db(tipo, periodo_inicio, periodo_fin, datos, filepath, config)

        # Enviar por email
        if enviar_email and config:
            self._enviar_email(config, filepath, filename, content_type)

    def _guardar_reporte_db(self, tipo, periodo_inicio, periodo_fin, datos, filepath, config=None):
        """Guarda el reporte en la base de datos"""
        try:
            # Obtener o crear configuración
            if not config:
                config, _ = ConfiguracionReporte.objects.get_or_create(
                    nombre=f'Reporte {tipo.title()} Automático',
                    tipo_reporte=tipo.upper(),
                    defaults={'frecuencia': 'DIARIO', 'activo': False}
                )

            # Obtener usuario sistema o admin
            usuario = Usuario.objects.filter(is_superuser=True).first()
            if not usuario:
                usuario = Usuario.objects.filter(rol='ADMINISTRATIVO').first()

            if usuario:
                reporte = ReporteGenerado.objects.create(
                    configuracion=config,
                    periodo_inicio=periodo_inicio,
                    periodo_fin=periodo_fin,
                    datos_json=datos,
                    generado_por=usuario
                )
                self.stdout.write(f'  - Guardado en BD: ID {reporte.id}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  - No se pudo guardar en BD: {str(e)}'))

    def _enviar_email(self, config, filepath, filename, content_type):
        """Envía el reporte por email a los destinatarios configurados"""
        destinatarios = config.destinatarios.all()

        if not destinatarios.exists():
            self.stdout.write('  - No hay destinatarios configurados')
            return

        emails = [d.email for d in destinatarios if d.email]

        if not emails:
            self.stdout.write('  - Los destinatarios no tienen email configurado')
            return

        try:
            subject = f'[SST] Reporte: {config.nombre}'
            body = f"""
Reporte generado automáticamente por el Sistema SST.

Nombre: {config.nombre}
Tipo: {config.get_tipo_reporte_display()}
Frecuencia: {config.get_frecuencia_display()}
Fecha de generación: {timezone.now().strftime('%d/%m/%Y %H:%M')}

El archivo adjunto contiene los datos del reporte.

---
Sistema SST - Centro Minero SENA
            """

            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=emails
            )

            with open(filepath, 'rb') as f:
                email.attach(filename, f.read(), content_type)

            email.send()
            self.stdout.write(self.style.SUCCESS(f'  - Email enviado a: {", ".join(emails)}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  - Error enviando email: {str(e)}'))

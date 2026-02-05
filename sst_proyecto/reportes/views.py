from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count
from django.http import HttpResponse
from datetime import datetime, timedelta

from .models import ConfiguracionReporte, ReporteGenerado
from .serializers import ConfiguracionReporteSerializer, ReporteGeneradoSerializer
from .services import (
    ReporteAforoService,
    ReporteIncidentesService,
    ReporteAsistenciaService,
    ReporteSeguridadService,
)
from .pdf_generator import PDFReporteGenerator
from .excel_generator import ExcelReporteGenerator
from .csv_generator import CSVReporteGenerator
from control_acceso.models import RegistroAcceso, ConfiguracionAforo
from emergencias.models import Emergencia
from usuarios.models import Usuario


class ReporteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para generación y gestión de reportes
    """
    queryset = ReporteGenerado.objects.all().order_by('-fecha_generacion')
    serializer_class = ReporteGeneradoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filtra reportes según el rol del usuario
        """
        user = self.request.user
        
        if not user.is_authenticated:
            return ReporteGenerado.objects.none()
        
        # ADMINISTRATIVO: Ve todos los reportes
        if user.rol == 'ADMINISTRATIVO' or user.is_superuser:
            return super().get_queryset()
        
        # INSTRUCTOR: Solo ve reportes de asistencia que generó
        elif user.rol == 'INSTRUCTOR':
            return ReporteGenerado.objects.filter(
                Q(generado_por=user) | 
                Q(configuracion__tipo_reporte='ASISTENCIA')
            ).order_by('-fecha_generacion')
        
        # VIGILANCIA: Solo reportes de aforo y seguridad
        elif user.rol == 'VIGILANCIA':
            return ReporteGenerado.objects.filter(
                configuracion__tipo_reporte__in=['AFORO', 'SEGURIDAD']
            ).order_by('-fecha_generacion')
        
        # BRIGADA: Solo reportes de incidentes/emergencias
        elif user.rol == 'BRIGADA':
            return ReporteGenerado.objects.filter(
                configuracion__tipo_reporte__in=['INCIDENTES', 'SEGURIDAD']
            ).order_by('-fecha_generacion')
        
        # APRENDIZ: Solo sus propios reportes
        elif user.rol == 'APRENDIZ':
            return ReporteGenerado.objects.filter(generado_por=user).order_by('-fecha_generacion')
        
        # VISITANTE: No puede ver reportes
        return ReporteGenerado.objects.none()

    @action(detail=False, methods=['get'])
    def aforo(self, request):
        """Genera reporte de aforo"""
        # Verificar permisos
        if request.user.rol not in ['ADMINISTRATIVO', 'VIGILANCIA']:
            return Response(
                {'error': 'No tienes permisos para generar reportes de aforo.'},
                status=status.HTTP_403_FORBIDDEN
            )

        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        formato = request.query_params.get('formato', 'json')  # json, pdf, excel, csv

        if not fecha_inicio or not fecha_fin:
            return Response(
                {'error': 'fecha_inicio y fecha_fin son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            periodo_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            periodo_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generar reporte
        datos = ReporteAforoService.generar_reporte(periodo_inicio, periodo_fin)

        # Guardar en base de datos si se solicita
        if request.query_params.get('guardar') == 'true':
            config, _ = ConfiguracionReporte.objects.get_or_create(
                nombre=f'Reporte Aforo {fecha_inicio} a {fecha_fin}',
                tipo_reporte='AFORO',
            )

            ReporteGenerado.objects.create(
                configuracion=config,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                datos_json=datos,
                generado_por=request.user
            )

        # Retornar en el formato solicitado
        if formato == 'pdf':
            pdf_buffer = PDFReporteGenerator.generar_reporte_aforo(datos)
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_aforo_{fecha_inicio}_{fecha_fin}.pdf"'
            return response

        elif formato == 'excel':
            excel_buffer = ExcelReporteGenerator.generar_reporte_aforo(datos)
            response = HttpResponse(
                excel_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="reporte_aforo_{fecha_inicio}_{fecha_fin}.xlsx"'
            return response

        elif formato == 'csv':
            csv_buffer = CSVReporteGenerator.generar_reporte_aforo(datos)
            response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="reporte_aforo_{fecha_inicio}_{fecha_fin}.csv"'
            return response

        return Response(datos)
    
    @action(detail=False, methods=['get'])
    def incidentes(self, request):
        """Genera reporte de incidentes"""
        if request.user.rol not in ['ADMINISTRATIVO', 'BRIGADA', 'INSTRUCTOR']:
            return Response(
                {'error': 'No tienes permisos para generar reportes de incidentes.'},
                status=status.HTTP_403_FORBIDDEN
            )

        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        formato = request.query_params.get('formato', 'json')  # json, pdf, excel, csv

        if not fecha_inicio or not fecha_fin:
            return Response(
                {'error': 'fecha_inicio y fecha_fin son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            periodo_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            periodo_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generar reporte
        if request.user.rol == 'INSTRUCTOR':
            datos = ReporteIncidentesService.generar_reporte_instruccion(
                periodo_inicio,
                periodo_fin,
                request.user
            )
        else:
            datos = ReporteIncidentesService.generar_reporte(periodo_inicio, periodo_fin)

        # Retornar en el formato solicitado
        if formato == 'pdf':
            pdf_buffer = PDFReporteGenerator.generar_reporte_incidentes(datos)
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_incidentes_{fecha_inicio}_{fecha_fin}.pdf"'
            return response

        elif formato == 'excel':
            excel_buffer = ExcelReporteGenerator.generar_reporte_incidentes(datos)
            response = HttpResponse(
                excel_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="reporte_incidentes_{fecha_inicio}_{fecha_fin}.xlsx"'
            return response

        elif formato == 'csv':
            csv_buffer = CSVReporteGenerator.generar_reporte_incidentes(datos)
            response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="reporte_incidentes_{fecha_inicio}_{fecha_fin}.csv"'
            return response

        return Response(datos)
    
    @action(detail=False, methods=['get'])
    def asistencia(self, request):
        """Genera reporte de asistencia"""
        if request.user.rol not in ['INSTRUCTOR', 'ADMINISTRATIVO', 'VIGILANCIA']:
            return Response(
                {'error': 'No tienes permisos para generar reportes de asistencia.'},
                status=status.HTTP_403_FORBIDDEN
            )

        ficha = request.query_params.get('ficha')
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        formato = request.query_params.get('formato', 'json')  # json, pdf, excel, csv

        if not all([ficha, fecha_inicio, fecha_fin]):
            return Response(
                {'error': 'ficha, fecha_inicio y fecha_fin son requeridos.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            periodo_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            periodo_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generar reporte
        datos = ReporteAsistenciaService.generar_reporte(ficha, periodo_inicio, periodo_fin)

        # Retornar en el formato solicitado
        if formato == 'pdf':
            pdf_buffer = PDFReporteGenerator.generar_reporte_asistencia(datos)
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_asistencia_ficha_{ficha}_{fecha_inicio}_{fecha_fin}.pdf"'
            return response

        elif formato == 'excel':
            excel_buffer = ExcelReporteGenerator.generar_reporte_asistencia(datos)
            response = HttpResponse(
                excel_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="reporte_asistencia_ficha_{ficha}_{fecha_inicio}_{fecha_fin}.xlsx"'
            return response

        elif formato == 'csv':
            csv_buffer = CSVReporteGenerator.generar_reporte_asistencia(datos)
            response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="reporte_asistencia_ficha_{ficha}_{fecha_inicio}_{fecha_fin}.csv"'
            return response

        return Response(datos)
    
    @action(detail=False, methods=['get'])
    def seguridad(self, request):
        """Genera reporte de seguridad"""
        if request.user.rol not in ['ADMINISTRATIVO', 'BRIGADA', 'VIGILANCIA']:
            return Response(
                {'error': 'No tienes permisos para generar reportes de seguridad.'},
                status=status.HTTP_403_FORBIDDEN
            )

        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        formato = request.query_params.get('formato', 'json')  # json, pdf, excel, csv

        if not fecha_inicio or not fecha_fin:
            fecha_fin = timezone.now().date()
            fecha_inicio = fecha_fin - timedelta(days=30)
            periodo_inicio = fecha_inicio
            periodo_fin = fecha_fin
        else:
            try:
                periodo_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
                periodo_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Generar reporte según rol
        if request.user.rol == 'VIGILANCIA':
            datos = ReporteSeguridadService.generar_reporte_vigilancia(periodo_inicio, periodo_fin)
        elif request.user.rol == 'BRIGADA':
            datos = ReporteSeguridadService.generar_reporte_emergencias(periodo_inicio, periodo_fin)
        else:
            datos = ReporteSeguridadService.generar_reporte(periodo_inicio, periodo_fin)

        fecha_inicio_str = fecha_inicio if isinstance(fecha_inicio, str) else fecha_inicio.strftime('%Y-%m-%d')
        fecha_fin_str = fecha_fin if isinstance(fecha_fin, str) else fecha_fin.strftime('%Y-%m-%d')

        # Retornar en el formato solicitado
        if formato == 'pdf':
            pdf_buffer = PDFReporteGenerator.generar_reporte_seguridad(datos)
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_seguridad_{fecha_inicio_str}_{fecha_fin_str}.pdf"'
            return response

        elif formato == 'excel':
            # Usar reporte de emergencias si es Brigada
            if request.user.rol == 'BRIGADA':
                excel_buffer = ExcelReporteGenerator.generar_reporte_emergencias(datos)
            else:
                excel_buffer = ExcelReporteGenerator.generar_reporte_seguridad(datos)
            response = HttpResponse(
                excel_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="reporte_seguridad_{fecha_inicio_str}_{fecha_fin_str}.xlsx"'
            return response

        elif formato == 'csv':
            # Usar reporte de emergencias si es Brigada
            if request.user.rol == 'BRIGADA':
                csv_buffer = CSVReporteGenerator.generar_reporte_emergencias(datos)
            else:
                csv_buffer = CSVReporteGenerator.generar_reporte_seguridad(datos)
            response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="reporte_seguridad_{fecha_inicio_str}_{fecha_fin_str}.csv"'
            return response

        return Response(datos)
    
    @action(detail=False, methods=['get'])
    def mi_asistencia(self, request):
        """Reporte de asistencia personal para aprendices"""
        if request.user.rol != 'APRENDIZ':
            return Response(
                {'error': 'Esta función es solo para aprendices.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = request.user
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=30)
        
        # Obtener registros del aprendiz
        registros = RegistroAcceso.objects.filter(
            usuario=user,
            fecha_hora_ingreso__date__gte=fecha_inicio,
            fecha_hora_ingreso__date__lte=fecha_fin
        ).order_by('fecha_hora_ingreso')
        
        datos_registros = []
        total_horas = 0
        
        for registro in registros:
            horas = 0
            if registro.fecha_hora_egreso:
                diferencia = registro.fecha_hora_egreso - registro.fecha_hora_ingreso
                horas = diferencia.total_seconds() / 3600
                total_horas += horas
            
            datos_registros.append({
                'fecha': registro.fecha_hora_ingreso.date(),
                'hora_ingreso': registro.fecha_hora_ingreso.time(),
                'hora_egreso': registro.fecha_hora_egreso.time() if registro.fecha_hora_egreso else None,
                'horas_trabajadas': round(horas, 2)
            })
        
        datos = {
            'aprendiz': user.get_full_name(),
            'ficha': user.ficha or 'No asignada',
            'periodo': f'{fecha_inicio} a {fecha_fin}',
            'total_dias': len(datos_registros),
            'total_horas': round(total_horas, 2),
            'registros': datos_registros
        }
        
        return Response(datos)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_estadisticas(request):
    """Retorna estadísticas para el dashboard principal"""
    user = request.user
    
    # Personas en el centro ahora
    personas_en_centro = RegistroAcceso.objects.filter(
        fecha_hora_egreso__isnull=True
    ).count()

    # Configuración de aforo
    config_aforo = ConfiguracionAforo.objects.first()
    aforo_maximo = config_aforo.aforo_maximo if config_aforo else 0
    porcentaje_aforo = (personas_en_centro / aforo_maximo * 100) if aforo_maximo > 0 else 0

    # Emergencias activas
    emergencias_activas = Emergencia.objects.filter(
        Q(estado='REPORTADA') | Q(estado='EN_ATENCION')
    ).count()

    # Ingresos de hoy
    hoy = timezone.now().date()
    ingresos_hoy = RegistroAcceso.objects.filter(
        fecha_hora_ingreso__date=hoy
    ).count()

    respuesta = {
        'personas_en_centro': personas_en_centro,
        'aforo_maximo': aforo_maximo,
        'porcentaje_aforo': round(porcentaje_aforo, 2),
        'emergencias_activas': emergencias_activas,
        'ingresos_hoy': ingresos_hoy,
        'timestamp': timezone.now(),
        'rol_usuario': user.rol
    }

    # Limitar datos según rol
    if user.rol == 'VISITANTE':
        return Response({
            'mensaje': 'Bienvenido al sistema SST',
            'rol_usuario': 'VISITANTE'
        })

    return Response(respuesta)
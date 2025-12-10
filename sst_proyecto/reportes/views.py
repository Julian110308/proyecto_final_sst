from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count
from datetime import datetime, timedelta
import os
from .models import ConfiguracionReporte, ReporteGenerado
from .services import (
    ReporteAforoService,
    ReporteIncidentesService,
    ReporteAsistenciaService,
    ReporteSeguridadService,
)
from control_acceso.models import RegistroAcceso, ConfiguracionAforo
from emergencias.models import Emergencia
from usuarios.models import Usuario

class ReporteViewSet(viewsets.ModelViewSet):

    # ViewSet para generación de reportes
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def aforo(self, request):

        # Genera reporte de aforo
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')

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

        return Response(datos)
    
    @action(detail=False, methods=['get'])
    def incidentes(self, request):

        # Genera reporte de incidentes
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')

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
        datos = ReporteIncidentesService.generar_reporte(periodo_inicio, periodo_fin)

        # Guardar en base de datos si se solicita
        if request.query_params.get('guardar') == 'true':
            config, _ = ConfiguracionReporte.objects.get_or_create(
                nombre=f'Reporte Incidentes {fecha_inicio} a {fecha_fin}',
                tipo_reporte='INCIDENTES',
            )

            ReporteGenerado.objects.create(
                configuracion=config,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                datos_json=datos,
                generado_por=request.user
            )

        return Response(datos)
    
    @action(detail=False, methods=['get'])
    def asistencia(self, request):

        # Genera reporte de asistencia por ficha
        ficha = request.query_params.get('ficha')
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')

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

        # Guardar en base de datos si se solicita
        if request.query_params.get('guardar') == 'true':
            config, _ = ConfiguracionReporte.objects.get_or_create(
                nombre=f'Reporte Asistencia {ficha}',
                tipo_reporte='ASISTENCIA',
            )

            ReporteGenerado.objects.create(
                configuracion=config,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                datos_json=datos,
                generado_por=request.user
            )

        return Response(datos)
    
    @action(detail=False, methods=['get'])
    def seguridad(self, request):

        # Genera reporte de seguridad
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')

        if not fecha_inicio or not fecha_fin:
            # Por defecto, último mes
            fecha_fin = timezone.now().date()
            fecha_inicio = fecha_fin - timedelta(days=30)
        else:
            try:
                periodo_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
                periodo_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Generar reporte
        datos = ReporteSeguridadService.generar_reporte(periodo_inicio, periodo_fin)

        # Guardar en base de datos si se solicita
        if request.query_params.get('guardar') == 'true':
            config, _ = ConfiguracionReporte.objects.get_or_create(
                nombre=f'Reporte Seguridad {fecha_inicio} a {fecha_fin}',
                tipo_reporte='SEGURIDAD',
            )

            ReporteGenerado.objects.create(
                configuracion=config,
                periodo_inicio=periodo_inicio,
                periodo_fin=periodo_fin,
                datos_json=datos,
                generado_por=request.user
            )
        
        return Response(datos)
    
    @action(detail=False, methods=['get'])
    def historial(self, request):

        # Obtiene el historial de reportes generados
        reportes = ReporteGenerado.objects.all().order_by('-fecha_generacion')

        datos_reportes = []
        for reporte in reportes:
            datos_reportes.append({
                'id': reporte.id,
                'nombre': reporte.configuracion.nombre,
                'tipo_reporte': reporte.configuracion.tipo_reporte,
                'fecha_generacion': reporte.fecha_generacion,
                'periodo_inicio': reporte.periodo_inicio,
                'periodo_fin': reporte.periodo_fin,
                'generado_por': reporte.generado_por.get_full_name() if reporte.generado_por else 'Sistema'
            })

        return Response(datos_reportes)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_estadisticas(request):

    # Retorna estadísticas para el dashboard principal
    
    # Personas en el centro ahora
    personas_en_centro = RegistroAcceso.objects.filter(
        fecha_hora_egreso__isnull=False
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

    # Usuarios por rol
    usuarios_por_rol = Usuario.objects.filter(activo=True).values('rol').annotate(
        total=Count('id')
    )

    # Emergencias de los últimos 7 días
    ultima_semana = timezone.now().date() - timedelta(days=7)
    emergencias_recientes = Emergencia.objects.filter(
        fecha_hora_reporte__gte=ultima_semana
    ).count()

    # Equipamiento operativo
    from mapas.models import EquipamientoSeguridad
    equipamiento_total = EquipamientoSeguridad.objects.count()
    equipamiento_operativo = EquipamientoSeguridad.objects.filter(estado='OPERATIVO').count()
    porcentaje_equipamiento = (equipamiento_operativo / equipamiento_total * 100) if equipamiento_total > 0 else 0

    return Response({
        'personas_en_centro': personas_en_centro,
        'aforo_maximo': aforo_maximo,
        'porcentaje_aforo': round(porcentaje_aforo, 2),
        'emergencias_activas': emergencias_activas,
        'ingresos_hoy': ingresos_hoy,
        'emergencias_recientes': emergencias_recientes,
        'equipamiento_operativo': equipamiento_operativo,
        'equipamiento_total': equipamiento_total,
        'porcentaje_equipamiento': round(porcentaje_equipamiento, 2),
        'usuarios_por_rol': list(usuarios_por_rol),
        'timestamp': timezone.now()
    })
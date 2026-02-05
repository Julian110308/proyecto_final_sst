from django.utils import timezone
from django.db.models import Count, Q, Avg
from django.db.models.functions import TruncDate, ExtractHour
from datetime import datetime, timedelta
import math

class ReporteAforoService:

    # Servicio para generar reportes de aforo
    @staticmethod
    def generar_reporte(periodo_inicio, periodo_fin):
        from control_acceso.models import RegistroAcceso, ConfiguracionAforo
        from usuarios.models import Usuario

        registros = RegistroAcceso.objects.filter(
            fecha_hora_ingreso__range=[periodo_inicio, periodo_fin]
        )

        total_ingresos = registros.count()

        # Aforo por dia (optimizado con TruncDate)
        aforo_diario = registros.annotate(
            fecha=TruncDate('fecha_hora_ingreso')
        ).values('fecha').annotate(
            total=Count('id')
        ).order_by('fecha')

        # Aforo por rol
        aforo_por_rol = Usuario.objects.filter(
            accesos__fecha_hora_ingreso__range=[periodo_inicio, periodo_fin]
        ).values('rol').annotate(
            total=Count('accesos')
        ).order_by('-total')

        # Configuración de aforo
        config_aforo = ConfiguracionAforo.objects.first()
        aforo_maximo = config_aforo.aforo_maximo if config_aforo else 0

        # Hora pico (optimizado con ExtractHour)
        hora_pico_data = registros.annotate(
            hora=ExtractHour('fecha_hora_ingreso')
        ).values('hora').annotate(
            total=Count('id')
        ).order_by('-total').first()

        # Tiempo promedio de permanencia
        registros_con_egreso = registros.filter(fecha_hora_egreso__isnull=False)
        tiempo_promedio = None
        if registros_con_egreso.exists():
            tiempos = []
            for registro in registros_con_egreso:
                if registro.duracion_permanencia:
                    tiempos.append(registro.duracion_permanencia.total_seconds() / 60) # En minutos
            if tiempos:
                tiempo_promedio = sum(tiempos) / len(tiempos)
        
        return {
            'periodo_inicio': periodo_inicio,
            'periodo_fin': periodo_fin,
            'total_ingresos': total_ingresos,
            'aforo_maximo_permitido': aforo_maximo,
            'porcentaje_uso': round((total_ingresos / aforo_maximo * 100) if aforo_maximo > 0 else 0,2),
            'aforo_diario': list(aforo_diario),
            'aforo_por_rol': list(aforo_por_rol),
            'hora_pico': hora_pico_data['hora'] if hora_pico_data else None,
            'total_hora_pico': hora_pico_data['total'] if hora_pico_data else 0,
            'tiempo_promedio_permanencia_minutos': round(tiempo_promedio, 2) if tiempo_promedio else None,
        }
    
class ReporteIncidentesService:

    # Servicio para generar reportes de incidentes
    @staticmethod
    def generar_reporte(periodo_inicio, periodo_fin):
        from emergencias.models import Emergencia

        emergencias = Emergencia.objects.filter(
            fecha_hora_reporte__range=[periodo_inicio, periodo_fin]
        )

        total_emergencias = emergencias.count()

        # Por tipo - usar tipo__nombre en lugar de tipo_nombre
        por_tipo = emergencias.values('tipo__nombre').annotate(
            total=Count('id')
        ).order_by('-total')

        # Renombrar la clave para mantener compatibilidad
        por_tipo_lista = [{'tipo_nombre': item['tipo__nombre'], 'total': item['total']} for item in por_tipo]

        # Por estado
        por_estado = emergencias.values('estado').annotate(
            total=Count('id')
        ).order_by('estado')

        # Tiempo promedio de respuesta
        emergencias_atendidas = emergencias.exclude(fecha_hora_resolucion__isnull=True)
        tiempo_promedio_respuesta = None
        if emergencias_atendidas.exists():
            tiempos = []
            for em in emergencias_atendidas:
                if em.tiempo_respuesta:
                    tiempos.append(em.tiempo_respuesta)
            if tiempos:
                tiempo_promedio_respuesta = sum(tiempos) / len(tiempos)

        # Personas afectadas
        total_afectados = emergencias.aggregate(
            total=Count('personas_afectadas')
        )['total'] or 0

        # Emergencias que requirieron evacuación
        evacuaciones = emergencias.filter(requiere_evacuacion=True).count()

        return {
            'periodo_inicio': periodo_inicio,
            'periodo_fin': periodo_fin,
            'total_emergencias': total_emergencias,
            'por_tipo': por_tipo_lista,
            'por_estado': list(por_estado),
            'tiempo_promedio_respuesta_minutos': (
                round(tiempo_promedio_respuesta, 2) if tiempo_promedio_respuesta else None
            ),
            'total_personas_afectadas': total_afectados,
            'evacuaciones_requeridas': evacuaciones,
            'porcentaje_resueltas': (
                round((emergencias.filter(estado='RESUELTA').count() / total_emergencias * 100), 2)
                if total_emergencias > 0 else 0
            )
        }

    @staticmethod
    def generar_reporte_instruccion(periodo_inicio, periodo_fin, usuario):
        """
        Genera reporte de incidentes filtrado para instructores.
        Incluye solo incidentes reportados por aprendices de sus fichas.
        """
        from emergencias.models import Emergencia
        from usuarios.models import Usuario

        # Obtener fichas asignadas al instructor (si aplica)
        fichas_instructor = Usuario.objects.filter(
            rol='APRENDIZ',
            activo=True
        ).values_list('ficha', flat=True).distinct()

        emergencias = Emergencia.objects.filter(
            fecha_hora_reporte__range=[periodo_inicio, periodo_fin]
        )

        total_emergencias = emergencias.count()

        # Por tipo
        por_tipo = emergencias.values('tipo__nombre').annotate(
            total=Count('id')
        ).order_by('-total')

        por_tipo_lista = [{'tipo_nombre': item['tipo__nombre'], 'total': item['total']} for item in por_tipo]

        # Por estado
        por_estado = emergencias.values('estado').annotate(
            total=Count('id')
        ).order_by('estado')

        # Tiempo promedio de respuesta
        emergencias_resueltas = emergencias.filter(estado='RESUELTA')
        tiempo_promedio_respuesta = None
        if emergencias_resueltas.exists():
            tiempos = []
            for em in emergencias_resueltas:
                if em.tiempo_respuesta:
                    tiempos.append(em.tiempo_respuesta)
            if tiempos:
                tiempo_promedio_respuesta = sum(tiempos) / len(tiempos)

        # Personas afectadas
        total_afectados = emergencias.aggregate(
            total=Count('personas_afectadas')
        )['total'] or 0

        # Evacuaciones
        evacuaciones = emergencias.filter(requiere_evacuacion=True).count()

        return {
            'periodo_inicio': periodo_inicio,
            'periodo_fin': periodo_fin,
            'total_emergencias': total_emergencias,
            'por_tipo': por_tipo_lista,
            'por_estado': list(por_estado),
            'tiempo_promedio_respuesta_minutos': (
                round(tiempo_promedio_respuesta, 2) if tiempo_promedio_respuesta else None
            ),
            'total_personas_afectadas': total_afectados,
            'evacuaciones_requeridas': evacuaciones,
            'porcentaje_resueltas': (
                round((emergencias_resueltas.count() / total_emergencias * 100), 2)
                if total_emergencias > 0 else 0
            ),
            'generado_por': usuario.get_full_name()
        }
    
class ReporteAsistenciaService:

    # Servicio para generar reportes de asistencia
    @staticmethod
    def generar_reporte(ficha, periodo_inicio, periodo_fin):
        from control_acceso.models import RegistroAcceso
        from usuarios.models import Usuario

        # Obtener aprendices de la ficha
        aprendices = Usuario.objects.filter(
            rol='APRENDIZ',
            ficha=ficha,
            activo=True
        )

        # Contar días del período (excluyendo fines de semana)
        dias_totales = 0
        current_date = periodo_inicio
        while current_date <= periodo_fin:
            if current_date.weekday() < 5: # 0-4 = Lunes a Viernes
                dias_totales += 1
            current_date += timedelta(days=1)

        # Generar reporte por aprendiz
        reporte_aprendices = []
        for aprendiz in aprendices:
            # Contar días de asistencia (días distintos con registro)
            dias_asistio = RegistroAcceso.objects.filter(
                usuario=aprendiz,
                fecha_hora_ingreso__range=[periodo_inicio, periodo_fin]
            ).extra({
                'fecha': 'date(fecha_hora_ingreso)'
            }).values('fecha').distinct().count()

            porcentaje = (dias_asistio / dias_totales * 100) if dias_totales > 0 else 0

            # Calcular puntualidad promedio
            registros = RegistroAcceso.objects.filter(
                usuario=aprendiz,
                fecha_hora_ingreso__range=[periodo_inicio, periodo_fin]
            )

            reporte_aprendices.append({
                'nombre': aprendiz.get_full_name(),
                'documento': aprendiz.numero_documento,
                'dias_asistio': dias_asistio,
                'dias_totales': dias_totales,
                'porcentaje_asistencia': round(porcentaje, 2),
                'estado': 'APROBADO' if porcentaje >= 80 else 'REPROBADO'
            })

        # Ordenar por porcentaje de asistencia (descendente)
        reporte_aprendices.sort(key=lambda x: x['porcentaje_asistencia'], reverse=True)

        return {
            'ficha': ficha,
            'periodo_inicio': periodo_inicio,
            'periodo_fin': periodo_fin,
            'dias_totales': dias_totales,
            'total_aprendices': aprendices.count(),
            'aprendices': reporte_aprendices,
            'promedio_asistencia': round(sum(a['porcentaje_asistencia'] 
            for a in reporte_aprendices) / len(reporte_aprendices), 2) if reporte_aprendices else 0
        }
    
class ReporteSeguridadService:

    # Servicio para generar reportes de seguridad
    @staticmethod
    def generar_reporte(periodo_inicio, periodo_fin):
        from mapas.models import EquipamientoSeguridad
        from emergencias.models import Emergencia
        from django.db.models.functions import TruncMonth

        # Estado de equipamiento
        equipamiento_total = EquipamientoSeguridad.objects.count()
        equipamiento_operativo = EquipamientoSeguridad.objects.filter(estado='OPERATIVO').count()
        equipamiento_mantenimiento = EquipamientoSeguridad.objects.filter(estado='MANTENIMIENTO').count()
        equipamiento_fuera_servicio = EquipamientoSeguridad.objects.filter(estado='FUERA_SERVICIO').count()

        # Por tipo de equipamiento
        equipamiento_por_tipo = EquipamientoSeguridad.objects.values('tipo').annotate(
            total=Count('id'),
            operativo=Count('id', filter=Q(estado='OPERATIVO')),
        ).order_by('-total')

        # Emergencias por tipo - usar tipo__nombre en lugar de tipo_nombre
        emergencias_por_tipo = Emergencia.objects.filter(
            fecha_hora_reporte__range=[periodo_inicio, periodo_fin]
        ).values('tipo__nombre').annotate(
            total=Count('id')
        ).order_by('-total')

        # Renombrar clave para compatibilidad
        emergencias_por_tipo_lista = [
            {'tipo_nombre': item['tipo__nombre'], 'total': item['total']}
            for item in emergencias_por_tipo
        ]

        # Tendencias mensuales (sin usar .extra() que está deprecado)
        tendencias = Emergencia.objects.filter(
            fecha_hora_reporte__range=[periodo_inicio, periodo_fin]
        ).annotate(
            mes=TruncMonth('fecha_hora_reporte')
        ).values('mes').annotate(
            total=Count('id')
        ).order_by('mes')

        # Formatear mes como string
        tendencias_lista = [
            {'mes': item['mes'].strftime('%Y-%m') if item['mes'] else '', 'total': item['total']}
            for item in tendencias
        ]

        return {
            'periodo_inicio': periodo_inicio,
            'periodo_fin': periodo_fin,
            'equipamiento_total': equipamiento_total,
            'equipamiento_operativo': equipamiento_operativo,
            'equipamiento_mantenimiento': equipamiento_mantenimiento,
            'equipamiento_fuera_servicio': equipamiento_fuera_servicio,
            'porcentaje_operativo': round((equipamiento_operativo / equipamiento_total * 100)
            if equipamiento_total > 0 else 0, 2),
            'equipamiento_por_tipo': list(equipamiento_por_tipo),
            'emergencias_por_tipo': emergencias_por_tipo_lista,
            'tendencias_mensuales': tendencias_lista
        }

    @staticmethod
    def generar_reporte_vigilancia(periodo_inicio, periodo_fin):
        """
        Genera reporte de seguridad enfocado en vigilancia.
        Incluye datos de accesos, visitantes y aforo.
        """
        from control_acceso.models import RegistroAcceso, ConfiguracionAforo, Visitante
        from mapas.models import EquipamientoSeguridad
        from django.db.models.functions import TruncDate

        # Datos de aforo
        config_aforo = ConfiguracionAforo.objects.first()
        aforo_maximo = config_aforo.aforo_maximo if config_aforo else 0

        # Registros de acceso en el período
        registros = RegistroAcceso.objects.filter(
            fecha_hora_ingreso__range=[periodo_inicio, periodo_fin]
        )

        total_ingresos = registros.count()
        total_egresos = registros.filter(fecha_hora_egreso__isnull=False).count()

        # Accesos por día
        accesos_diarios = registros.annotate(
            fecha=TruncDate('fecha_hora_ingreso')
        ).values('fecha').annotate(
            total=Count('id')
        ).order_by('fecha')

        # Visitantes en el período
        try:
            visitantes = Visitante.objects.filter(
                fecha_ingreso__range=[periodo_inicio, periodo_fin]
            )
            total_visitantes = visitantes.count()
            visitantes_activos = visitantes.filter(fecha_egreso__isnull=True).count()
        except Exception:
            total_visitantes = 0
            visitantes_activos = 0

        # Estado de equipamiento de vigilancia
        equipamiento_total = EquipamientoSeguridad.objects.count()
        equipamiento_operativo = EquipamientoSeguridad.objects.filter(estado='OPERATIVO').count()

        return {
            'periodo_inicio': periodo_inicio,
            'periodo_fin': periodo_fin,
            'aforo_maximo': aforo_maximo,
            'total_ingresos': total_ingresos,
            'total_egresos': total_egresos,
            'total_visitantes': total_visitantes,
            'visitantes_activos': visitantes_activos,
            'accesos_diarios': list(accesos_diarios),
            'equipamiento_total': equipamiento_total,
            'equipamiento_operativo': equipamiento_operativo,
            'equipamiento_mantenimiento': EquipamientoSeguridad.objects.filter(estado='MANTENIMIENTO').count(),
            'equipamiento_fuera_servicio': EquipamientoSeguridad.objects.filter(estado='FUERA_SERVICIO').count(),
            'porcentaje_operativo': round((equipamiento_operativo / equipamiento_total * 100)
                if equipamiento_total > 0 else 0, 2),
            'equipamiento_por_tipo': list(EquipamientoSeguridad.objects.values('tipo').annotate(
                total=Count('id'),
                operativo=Count('id', filter=Q(estado='OPERATIVO')),
            ).order_by('-total')),
            'emergencias_por_tipo': [],
            'tendencias_mensuales': []
        }

    @staticmethod
    def generar_reporte_emergencias(periodo_inicio, periodo_fin):
        """
        Genera reporte de seguridad enfocado en emergencias para brigada.
        Incluye detalles de emergencias y tiempos de respuesta.
        """
        from emergencias.models import Emergencia
        from mapas.models import EquipamientoSeguridad
        from django.db.models.functions import TruncMonth

        # Emergencias en el período
        emergencias = Emergencia.objects.filter(
            fecha_hora_reporte__range=[periodo_inicio, periodo_fin]
        )

        total_emergencias = emergencias.count()
        resueltas = emergencias.filter(estado='RESUELTA').count()
        en_atencion = emergencias.filter(estado='EN_ATENCION').count()

        # Tiempos de respuesta
        tiempos_respuesta = []
        tiempos_resolucion = []
        for em in emergencias:
            if em.tiempo_respuesta:
                tiempos_respuesta.append(em.tiempo_respuesta)
            if em.tiempo_resolucion:
                tiempos_resolucion.append(em.tiempo_resolucion)

        tiempo_promedio_respuesta = (sum(tiempos_respuesta) / len(tiempos_respuesta)) if tiempos_respuesta else 0
        tiempo_promedio_resolucion = (sum(tiempos_resolucion) / len(tiempos_resolucion)) if tiempos_resolucion else 0

        # Emergencias por tipo
        emergencias_por_tipo = emergencias.values('tipo__nombre').annotate(
            total=Count('id')
        ).order_by('-total')

        emergencias_por_tipo_lista = [
            {'tipo_nombre': item['tipo__nombre'], 'total': item['total']}
            for item in emergencias_por_tipo
        ]

        # Lista detallada de emergencias
        emergencias_lista = []
        for em in emergencias.select_related('tipo', 'reportada_por')[:50]:
            emergencias_lista.append({
                'fecha': em.fecha_hora_reporte.strftime('%Y-%m-%d %H:%M') if em.fecha_hora_reporte else '',
                'tipo': em.tipo.nombre if em.tipo else 'Sin tipo',
                'estado': em.estado,
                'ubicacion': em.descripcion[:50] if em.descripcion else '',
                'reportado_por': em.reportada_por.get_full_name() if em.reportada_por else 'Desconocido',
                'tiempo_respuesta': em.tiempo_respuesta or 0,
                'personas_afectadas': em.personas_afectadas or 0
            })

        # Estado de equipamiento
        equipamiento_total = EquipamientoSeguridad.objects.count()
        equipamiento_operativo = EquipamientoSeguridad.objects.filter(estado='OPERATIVO').count()

        # Tendencias mensuales
        tendencias = emergencias.annotate(
            mes=TruncMonth('fecha_hora_reporte')
        ).values('mes').annotate(
            total=Count('id')
        ).order_by('mes')

        tendencias_lista = [
            {'mes': item['mes'].strftime('%Y-%m') if item['mes'] else '', 'total': item['total']}
            for item in tendencias
        ]

        return {
            'periodo_inicio': periodo_inicio,
            'periodo_fin': periodo_fin,
            'total_emergencias': total_emergencias,
            'resueltas': resueltas,
            'en_atencion': en_atencion,
            'tiempo_promedio_respuesta': round(tiempo_promedio_respuesta, 2),
            'tiempo_promedio_resolucion': round(tiempo_promedio_resolucion, 2),
            'emergencias': emergencias_lista,
            'emergencias_por_tipo': emergencias_por_tipo_lista,
            'equipamiento_total': equipamiento_total,
            'equipamiento_operativo': equipamiento_operativo,
            'equipamiento_mantenimiento': EquipamientoSeguridad.objects.filter(estado='MANTENIMIENTO').count(),
            'equipamiento_fuera_servicio': EquipamientoSeguridad.objects.filter(estado='FUERA_SERVICIO').count(),
            'porcentaje_operativo': round((equipamiento_operativo / equipamiento_total * 100)
                if equipamiento_total > 0 else 0, 2),
            'equipamiento_por_tipo': list(EquipamientoSeguridad.objects.values('tipo').annotate(
                total=Count('id'),
                operativo=Count('id', filter=Q(estado='OPERATIVO')),
            ).order_by('-total')),
            'tendencias_mensuales': tendencias_lista
        }
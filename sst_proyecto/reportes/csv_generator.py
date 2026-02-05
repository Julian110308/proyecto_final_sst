import csv
from io import StringIO, BytesIO
from datetime import datetime


class CSVReporteGenerator:
    """
    Generador de reportes CSV para el sistema SST
    """

    @staticmethod
    def _crear_buffer():
        """Crea un buffer para escribir CSV"""
        return StringIO()

    @staticmethod
    def _finalizar_buffer(buffer):
        """Convierte StringIO a BytesIO para la respuesta HTTP"""
        buffer.seek(0)
        output = BytesIO()
        output.write(buffer.getvalue().encode('utf-8-sig'))  # BOM para Excel
        output.seek(0)
        return output

    @staticmethod
    def generar_reporte_aforo(datos):
        """
        Genera CSV para reporte de aforo
        """
        buffer = CSVReporteGenerator._crear_buffer()
        writer = csv.writer(buffer)

        # Encabezado del reporte
        writer.writerow(['REPORTE DE AFORO - CENTRO MINERO SENA'])
        writer.writerow([f"Periodo: {datos['periodo_inicio']} a {datos['periodo_fin']}"])
        writer.writerow([f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"])
        writer.writerow([])

        # Resumen General
        writer.writerow(['RESUMEN GENERAL'])
        writer.writerow(['Indicador', 'Valor'])
        writer.writerow(['Total de Ingresos', datos['total_ingresos']])
        writer.writerow(['Aforo Máximo Permitido', datos['aforo_maximo_permitido']])
        writer.writerow(['Porcentaje de Uso', f"{datos['porcentaje_uso']}%"])
        writer.writerow(['Hora Pico', f"{datos['hora_pico']}:00" if datos['hora_pico'] else 'N/A'])
        writer.writerow(['Total en Hora Pico', datos['total_hora_pico']])
        writer.writerow(['Tiempo Promedio Permanencia (min)',
                        datos['tiempo_promedio_permanencia_minutos'] or 'N/A'])
        writer.writerow([])

        # Aforo por Rol
        if datos['aforo_por_rol']:
            writer.writerow(['AFORO POR ROL'])
            writer.writerow(['Rol', 'Total Ingresos'])
            for item in datos['aforo_por_rol']:
                writer.writerow([item['rol'], item['total']])
            writer.writerow([])

        # Aforo Diario
        if datos['aforo_diario']:
            writer.writerow(['AFORO DIARIO'])
            writer.writerow(['Fecha', 'Total Ingresos'])
            for item in datos['aforo_diario']:
                fecha = item['fecha']
                if hasattr(fecha, 'strftime'):
                    fecha = fecha.strftime('%Y-%m-%d')
                writer.writerow([str(fecha), item['total']])

        return CSVReporteGenerator._finalizar_buffer(buffer)

    @staticmethod
    def generar_reporte_incidentes(datos):
        """
        Genera CSV para reporte de incidentes/emergencias
        """
        buffer = CSVReporteGenerator._crear_buffer()
        writer = csv.writer(buffer)

        # Encabezado del reporte
        writer.writerow(['REPORTE DE INCIDENTES Y EMERGENCIAS - CENTRO MINERO SENA'])
        writer.writerow([f"Periodo: {datos['periodo_inicio']} a {datos['periodo_fin']}"])
        writer.writerow([f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"])
        writer.writerow([])

        # Resumen General
        writer.writerow(['RESUMEN GENERAL'])
        writer.writerow(['Indicador', 'Valor'])
        writer.writerow(['Total de Emergencias', datos['total_emergencias']])
        writer.writerow(['Personas Afectadas', datos['total_personas_afectadas']])
        writer.writerow(['Evacuaciones Requeridas', datos['evacuaciones_requeridas']])
        writer.writerow(['Porcentaje Resueltas', f"{datos['porcentaje_resueltas']}%"])
        writer.writerow(['Tiempo Promedio Respuesta (min)',
                        datos['tiempo_promedio_respuesta_minutos'] or 'N/A'])
        writer.writerow([])

        # Por Tipo
        if datos['por_tipo']:
            writer.writerow(['INCIDENTES POR TIPO'])
            writer.writerow(['Tipo', 'Total'])
            for item in datos['por_tipo']:
                writer.writerow([item.get('tipo_nombre', item.get('tipo', 'N/A')), item['total']])
            writer.writerow([])

        # Por Estado
        if datos['por_estado']:
            writer.writerow(['INCIDENTES POR ESTADO'])
            writer.writerow(['Estado', 'Total'])
            for item in datos['por_estado']:
                writer.writerow([item['estado'], item['total']])

        return CSVReporteGenerator._finalizar_buffer(buffer)

    @staticmethod
    def generar_reporte_asistencia(datos):
        """
        Genera CSV para reporte de asistencia
        """
        buffer = CSVReporteGenerator._crear_buffer()
        writer = csv.writer(buffer)

        # Encabezado del reporte
        writer.writerow(['REPORTE DE ASISTENCIA - CENTRO MINERO SENA'])
        writer.writerow([f"Ficha: {datos['ficha']}"])
        writer.writerow([f"Periodo: {datos['periodo_inicio']} a {datos['periodo_fin']}"])
        writer.writerow([f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"])
        writer.writerow([])

        # Resumen General
        writer.writerow(['RESUMEN GENERAL'])
        writer.writerow(['Indicador', 'Valor'])
        writer.writerow(['Total de Aprendices', datos['total_aprendices']])
        writer.writerow(['Días Totales del Periodo', datos['dias_totales']])
        writer.writerow(['Promedio de Asistencia', f"{datos['promedio_asistencia']}%"])
        writer.writerow([])

        # Detalle por Aprendiz
        writer.writerow(['DETALLE POR APRENDIZ'])
        writer.writerow(['Nombre', 'Documento', 'Días Asistió', 'Días Totales', '% Asistencia', 'Estado'])
        for aprendiz in datos['aprendices']:
            writer.writerow([
                aprendiz['nombre'],
                aprendiz['documento'],
                aprendiz['dias_asistio'],
                aprendiz['dias_totales'],
                f"{aprendiz['porcentaje_asistencia']}%",
                aprendiz['estado']
            ])

        return CSVReporteGenerator._finalizar_buffer(buffer)

    @staticmethod
    def generar_reporte_seguridad(datos):
        """
        Genera CSV para reporte de seguridad
        """
        buffer = CSVReporteGenerator._crear_buffer()
        writer = csv.writer(buffer)

        # Encabezado del reporte
        writer.writerow(['REPORTE DE SEGURIDAD - CENTRO MINERO SENA'])
        writer.writerow([f"Periodo: {datos['periodo_inicio']} a {datos['periodo_fin']}"])
        writer.writerow([f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"])
        writer.writerow([])

        # Estado de Equipamiento
        writer.writerow(['ESTADO DEL EQUIPAMIENTO DE SEGURIDAD'])
        writer.writerow(['Indicador', 'Valor'])
        writer.writerow(['Total de Equipos', datos['equipamiento_total']])
        writer.writerow(['Equipos Operativos', datos['equipamiento_operativo']])
        writer.writerow(['En Mantenimiento', datos['equipamiento_mantenimiento']])
        writer.writerow(['Fuera de Servicio', datos['equipamiento_fuera_servicio']])
        writer.writerow(['Porcentaje Operativo', f"{datos['porcentaje_operativo']}%"])
        writer.writerow([])

        # Equipamiento por Tipo
        if datos['equipamiento_por_tipo']:
            writer.writerow(['EQUIPAMIENTO POR TIPO'])
            writer.writerow(['Tipo', 'Total', 'Operativos'])
            for item in datos['equipamiento_por_tipo']:
                writer.writerow([item['tipo'], item['total'], item['operativo']])
            writer.writerow([])

        # Emergencias por Tipo
        if datos['emergencias_por_tipo']:
            writer.writerow(['EMERGENCIAS POR TIPO'])
            writer.writerow(['Tipo', 'Total'])
            for item in datos['emergencias_por_tipo']:
                writer.writerow([item.get('tipo_nombre', 'N/A'), item['total']])
            writer.writerow([])

        # Tendencias Mensuales
        if datos.get('tendencias_mensuales'):
            writer.writerow(['TENDENCIAS MENSUALES'])
            writer.writerow(['Mes', 'Total Emergencias'])
            for item in datos['tendencias_mensuales']:
                writer.writerow([item['mes'], item['total']])

        return CSVReporteGenerator._finalizar_buffer(buffer)

    @staticmethod
    def generar_reporte_emergencias(datos):
        """
        Genera CSV para reporte detallado de emergencias
        """
        buffer = CSVReporteGenerator._crear_buffer()
        writer = csv.writer(buffer)

        # Encabezado del reporte
        writer.writerow(['REPORTE DETALLADO DE EMERGENCIAS - CENTRO MINERO SENA'])
        writer.writerow([f"Periodo: {datos['periodo_inicio']} a {datos['periodo_fin']}"])
        writer.writerow([f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"])
        writer.writerow([])

        # Resumen
        writer.writerow(['RESUMEN'])
        writer.writerow(['Indicador', 'Valor'])
        writer.writerow(['Total Emergencias', datos.get('total_emergencias', 0)])
        writer.writerow(['Resueltas', datos.get('resueltas', 0)])
        writer.writerow(['En Atención', datos.get('en_atencion', 0)])
        writer.writerow(['Tiempo Promedio Respuesta (min)', datos.get('tiempo_promedio_respuesta', 0)])
        writer.writerow(['Tiempo Promedio Resolución (min)', datos.get('tiempo_promedio_resolucion', 0)])
        writer.writerow([])

        # Listado de Emergencias
        if datos.get('emergencias'):
            writer.writerow(['LISTADO DE EMERGENCIAS'])
            writer.writerow(['Fecha', 'Tipo', 'Estado', 'Ubicación', 'Reportado Por',
                           'Tiempo Respuesta (min)', 'Personas Afectadas'])
            for emerg in datos['emergencias']:
                writer.writerow([
                    emerg.get('fecha', ''),
                    emerg.get('tipo', ''),
                    emerg.get('estado', ''),
                    emerg.get('ubicacion', ''),
                    emerg.get('reportado_por', ''),
                    emerg.get('tiempo_respuesta', 0),
                    emerg.get('personas_afectadas', 0)
                ])

        return CSVReporteGenerator._finalizar_buffer(buffer)

    @staticmethod
    def generar_datos_crudos_aforo(datos):
        """
        Genera CSV con datos crudos de aforo (para análisis)
        """
        buffer = CSVReporteGenerator._crear_buffer()
        writer = csv.writer(buffer)

        # Solo datos crudos para análisis
        writer.writerow(['fecha', 'total_ingresos'])
        for item in datos.get('aforo_diario', []):
            fecha = item['fecha']
            if hasattr(fecha, 'strftime'):
                fecha = fecha.strftime('%Y-%m-%d')
            writer.writerow([str(fecha), item['total']])

        return CSVReporteGenerator._finalizar_buffer(buffer)

    @staticmethod
    def generar_datos_crudos_asistencia(datos):
        """
        Genera CSV con datos crudos de asistencia (para análisis)
        """
        buffer = CSVReporteGenerator._crear_buffer()
        writer = csv.writer(buffer)

        # Solo datos crudos para análisis
        writer.writerow(['nombre', 'documento', 'ficha', 'dias_asistio', 'dias_totales',
                        'porcentaje_asistencia', 'estado'])
        for aprendiz in datos.get('aprendices', []):
            writer.writerow([
                aprendiz['nombre'],
                aprendiz['documento'],
                datos.get('ficha', ''),
                aprendiz['dias_asistio'],
                aprendiz['dias_totales'],
                aprendiz['porcentaje_asistencia'],
                aprendiz['estado']
            ])

        return CSVReporteGenerator._finalizar_buffer(buffer)

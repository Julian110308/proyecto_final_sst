from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime


class PDFReporteGenerator:
    """
    Generador de reportes PDF para el sistema SST
    """

    @staticmethod
    def _crear_encabezado(styles):
        """Crea el encabezado estándar para los reportes"""
        titulo_style = ParagraphStyle(
            'TituloPersonalizado',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        subtitulo_style = ParagraphStyle(
            'SubtituloPersonalizado',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#7f8c8d'),
            spaceAfter=20,
            alignment=TA_CENTER
        )

        return titulo_style, subtitulo_style

    @staticmethod
    def generar_reporte_aforo(datos):
        """
        Genera PDF para reporte de aforo
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Encabezados
        titulo_style, subtitulo_style = PDFReporteGenerator._crear_encabezado(styles)

        # Título
        elements.append(Paragraph("REPORTE DE AFORO", titulo_style))
        elements.append(Paragraph(
            f"Centro Minero SENA - Sistema SST",
            subtitulo_style
        ))
        elements.append(Paragraph(
            f"Periodo: {datos['periodo_inicio']} a {datos['periodo_fin']}",
            subtitulo_style
        ))
        elements.append(Spacer(1, 0.3*inch))

        # Resumen general
        resumen_data = [
            ['RESUMEN GENERAL', ''],
            ['Total de Ingresos:', str(datos['total_ingresos'])],
            ['Aforo Máximo Permitido:', str(datos['aforo_maximo_permitido'])],
            ['Porcentaje de Uso:', f"{datos['porcentaje_uso']}%"],
            ['Hora Pico:', f"{datos['hora_pico']}:00 hrs" if datos['hora_pico'] else 'N/A'],
            ['Total en Hora Pico:', str(datos['total_hora_pico'])],
            ['Tiempo Promedio de Permanencia:',
             f"{datos['tiempo_promedio_permanencia_minutos']} min" if datos['tiempo_promedio_permanencia_minutos'] else 'N/A'],
        ]

        resumen_table = Table(resumen_data, colWidths=[4*inch, 2*inch])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        elements.append(resumen_table)
        elements.append(Spacer(1, 0.3*inch))

        # Aforo por Rol
        if datos['aforo_por_rol']:
            elements.append(Paragraph("AFORO POR ROL", styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))

            rol_data = [['Rol', 'Total de Ingresos']]
            for item in datos['aforo_por_rol']:
                rol_data.append([item['rol'], str(item['total'])])

            rol_table = Table(rol_data, colWidths=[4*inch, 2*inch])
            rol_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            elements.append(rol_table)

        # Pie de página con fecha de generación
        elements.append(Spacer(1, 0.5*inch))
        fecha_gen = Paragraph(
            f"<i>Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>",
            ParagraphStyle('PiePagina', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_RIGHT)
        )
        elements.append(fecha_gen)

        # Construir PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generar_reporte_incidentes(datos):
        """
        Genera PDF para reporte de incidentes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Encabezados
        titulo_style, subtitulo_style = PDFReporteGenerator._crear_encabezado(styles)

        # Título
        elements.append(Paragraph("REPORTE DE INCIDENTES Y EMERGENCIAS", titulo_style))
        elements.append(Paragraph(
            f"Centro Minero SENA - Sistema SST",
            subtitulo_style
        ))
        elements.append(Paragraph(
            f"Periodo: {datos['periodo_inicio']} a {datos['periodo_fin']}",
            subtitulo_style
        ))
        elements.append(Spacer(1, 0.3*inch))

        # Resumen general
        resumen_data = [
            ['RESUMEN GENERAL', ''],
            ['Total de Emergencias:', str(datos['total_emergencias'])],
            ['Personas Afectadas:', str(datos['total_personas_afectadas'])],
            ['Evacuaciones Requeridas:', str(datos['evacuaciones_requeridas'])],
            ['Porcentaje Resueltas:', f"{datos['porcentaje_resueltas']}%"],
            ['Tiempo Promedio de Respuesta:',
             f"{datos['tiempo_promedio_respuesta_minutos']} min" if datos['tiempo_promedio_respuesta_minutos'] else 'N/A'],
        ]

        resumen_table = Table(resumen_data, colWidths=[4*inch, 2*inch])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        elements.append(resumen_table)
        elements.append(Spacer(1, 0.3*inch))

        # Por tipo
        if datos['por_tipo']:
            elements.append(Paragraph("INCIDENTES POR TIPO", styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))

            tipo_data = [['Tipo de Incidente', 'Total']]
            for item in datos['por_tipo']:
                tipo_data.append([item['tipo_nombre'], str(item['total'])])

            tipo_table = Table(tipo_data, colWidths=[4*inch, 2*inch])
            tipo_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e67e22')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            elements.append(tipo_table)
            elements.append(Spacer(1, 0.2*inch))

        # Por estado
        if datos['por_estado']:
            elements.append(Paragraph("INCIDENTES POR ESTADO", styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))

            estado_data = [['Estado', 'Total']]
            for item in datos['por_estado']:
                estado_data.append([item['estado'], str(item['total'])])

            estado_table = Table(estado_data, colWidths=[4*inch, 2*inch])
            estado_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            elements.append(estado_table)

        # Pie de página
        elements.append(Spacer(1, 0.5*inch))
        fecha_gen = Paragraph(
            f"<i>Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>",
            ParagraphStyle('PiePagina', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_RIGHT)
        )
        elements.append(fecha_gen)

        # Construir PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generar_reporte_asistencia(datos):
        """
        Genera PDF para reporte de asistencia
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Encabezados
        titulo_style, subtitulo_style = PDFReporteGenerator._crear_encabezado(styles)

        # Título
        elements.append(Paragraph("REPORTE DE ASISTENCIA", titulo_style))
        elements.append(Paragraph(
            f"Centro Minero SENA - Sistema SST",
            subtitulo_style
        ))
        elements.append(Paragraph(
            f"Ficha: {datos['ficha']} | Periodo: {datos['periodo_inicio']} a {datos['periodo_fin']}",
            subtitulo_style
        ))
        elements.append(Spacer(1, 0.3*inch))

        # Resumen general
        resumen_data = [
            ['RESUMEN GENERAL', ''],
            ['Total de Aprendices:', str(datos['total_aprendices'])],
            ['Días Totales del Periodo:', str(datos['dias_totales'])],
            ['Promedio de Asistencia:', f"{datos['promedio_asistencia']}%"],
        ]

        resumen_table = Table(resumen_data, colWidths=[4*inch, 2*inch])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16a085')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        elements.append(resumen_table)
        elements.append(Spacer(1, 0.3*inch))

        # Detalle por aprendiz
        elements.append(Paragraph("DETALLE POR APRENDIZ", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))

        aprendiz_data = [['Nombre', 'Documento', 'Días', 'Asistencia', 'Estado']]
        for aprendiz in datos['aprendices']:
            aprendiz_data.append([
                aprendiz['nombre'],
                aprendiz['documento'],
                f"{aprendiz['dias_asistio']}/{aprendiz['dias_totales']}",
                f"{aprendiz['porcentaje_asistencia']}%",
                aprendiz['estado']
            ])

        aprendiz_table = Table(aprendiz_data, colWidths=[2.2*inch, 1.3*inch, 0.9*inch, 1*inch, 1*inch])
        aprendiz_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        elements.append(aprendiz_table)

        # Pie de página
        elements.append(Spacer(1, 0.5*inch))
        fecha_gen = Paragraph(
            f"<i>Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>",
            ParagraphStyle('PiePagina', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_RIGHT)
        )
        elements.append(fecha_gen)

        # Construir PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generar_reporte_seguridad(datos):
        """
        Genera PDF para reporte de seguridad
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Encabezados
        titulo_style, subtitulo_style = PDFReporteGenerator._crear_encabezado(styles)

        # Título
        elements.append(Paragraph("REPORTE DE SEGURIDAD", titulo_style))
        elements.append(Paragraph(
            f"Centro Minero SENA - Sistema SST",
            subtitulo_style
        ))
        elements.append(Paragraph(
            f"Periodo: {datos['periodo_inicio']} a {datos['periodo_fin']}",
            subtitulo_style
        ))
        elements.append(Spacer(1, 0.3*inch))

        # Resumen de equipamiento
        resumen_data = [
            ['ESTADO DEL EQUIPAMIENTO DE SEGURIDAD', ''],
            ['Total de Equipos:', str(datos['equipamiento_total'])],
            ['Equipos Operativos:', str(datos['equipamiento_operativo'])],
            ['En Mantenimiento:', str(datos['equipamiento_mantenimiento'])],
            ['Fuera de Servicio:', str(datos['equipamiento_fuera_servicio'])],
            ['Porcentaje Operativo:', f"{datos['porcentaje_operativo']}%"],
        ]

        resumen_table = Table(resumen_data, colWidths=[4*inch, 2*inch])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]))
        elements.append(resumen_table)
        elements.append(Spacer(1, 0.3*inch))

        # Equipamiento por tipo
        if datos['equipamiento_por_tipo']:
            elements.append(Paragraph("EQUIPAMIENTO POR TIPO", styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))

            equipo_data = [['Tipo de Equipo', 'Total', 'Operativos']]
            for item in datos['equipamiento_por_tipo']:
                equipo_data.append([
                    item['tipo'],
                    str(item['total']),
                    str(item['operativo'])
                ])

            equipo_table = Table(equipo_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
            equipo_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2980b9')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            elements.append(equipo_table)
            elements.append(Spacer(1, 0.2*inch))

        # Emergencias por tipo
        if datos['emergencias_por_tipo']:
            elements.append(Paragraph("EMERGENCIAS POR TIPO", styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))

            emerg_data = [['Tipo de Emergencia', 'Total']]
            for item in datos['emergencias_por_tipo']:
                emerg_data.append([item['tipo_nombre'], str(item['total'])])

            emerg_table = Table(emerg_data, colWidths=[4*inch, 2*inch])
            emerg_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c0392b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            elements.append(emerg_table)

        # Pie de página
        elements.append(Spacer(1, 0.5*inch))
        fecha_gen = Paragraph(
            f"<i>Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_RIGHT)
        )
        elements.append(fecha_gen)

        # Construir PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

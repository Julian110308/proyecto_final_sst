# control_acceso/utils.py

def verificar_aforo_actual():
    """
    Verifica el aforo actual del centro
    Retorna: (personas_dentro, aforo_maximo, porcentaje, alerta)
    """
    from .models import RegistroAcceso, ConfiguracionAforo
    from django.utils import timezone

    hoy = timezone.now().date()

    # Contar personas actualmente en el centro (solo registros de hoy)
    personas_dentro = RegistroAcceso.objects.filter(
        fecha_hora_egreso__isnull=True,
        fecha_hora_ingreso__date=hoy
    ).count()

    # Obtener configuración de aforo
    config_aforo = ConfiguracionAforo.objects.filter(activo=True).first()

    if config_aforo:
        aforo_maximo = config_aforo.aforo_maximo
        aforo_minimo = config_aforo.aforo_minimo
        porcentaje = (personas_dentro / aforo_maximo) * 100

        # Determinar nivel de alerta
        if personas_dentro >= aforo_maximo:
            alerta = 'CRITICO'
        elif personas_dentro >= aforo_minimo:
            alerta = 'ADVERTENCIA'
        else:
            alerta = 'NORMAL'

        return {
            'personas_dentro': personas_dentro,
            'aforo_maximo': aforo_maximo,
            'aforo_minimo': aforo_minimo,
            'porcentaje': round(porcentaje, 2),
            'alerta': alerta,
            'mensaje': config_aforo.mensaje_alerta if alerta != 'NORMAL' else ''
        }
    else:
        return {
            'personas_dentro': personas_dentro,
            'aforo_maximo': 2000,
            'aforo_minimo': 1800,
            'porcentaje': 0,
            'alerta': 'NORMAL',
            'mensaje': ''
        }


def obtener_estadisticas_hoy():
    """
    Obtiene estadísticas de acceso del día actual
    """
    from .models import RegistroAcceso
    from usuarios.models import Visitante
    from django.utils import timezone
    from datetime import datetime, time

    hoy = timezone.now().date()
    inicio_dia = timezone.make_aware(datetime.combine(hoy, time.min))
    fin_dia = timezone.make_aware(datetime.combine(hoy, time.max))

    # Ingresos de hoy
    ingresos_hoy = RegistroAcceso.objects.filter(
        fecha_hora_ingreso__range=(inicio_dia, fin_dia)
    ).count()

    # Personas actualmente en el centro (solo registros de hoy)
    personas_dentro = RegistroAcceso.objects.filter(
        fecha_hora_egreso__isnull=True,
        fecha_hora_ingreso__date=hoy
    ).count()

    # Visitantes activos
    visitantes_activos = Visitante.objects.filter(
        fecha_visita=hoy,
        hora_salida__isnull=True,
        activo=True
    ).count()

    # Información de aforo
    aforo_info = verificar_aforo_actual()

    return {
        'ingresos_hoy': ingresos_hoy,
        'personas_dentro': personas_dentro,
        'visitantes_activos': visitantes_activos,
        'aforo': aforo_info
    }

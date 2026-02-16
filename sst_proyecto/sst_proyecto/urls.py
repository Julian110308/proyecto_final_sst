"""
URL configuration for sst_proyecto project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from usuarios.permissions import rol_requerido, excluir_visitantes
from usuarios.login_view import custom_login_view

# Vista principal de dashboard que redirige según el rol
@login_required
def dashboard_view(request):
    """
    Vista principal que redirige al dashboard específico según el rol del usuario
    CON DATOS REALES DE LA BASE DE DATOS
    """
    from usuarios.models import Usuario, Visitante
    from control_acceso.models import RegistroAcceso, ConfiguracionAforo
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import timedelta

    usuario = request.user

    # Mapeo de roles a templates
    dashboard_templates = {
        'APRENDIZ': 'dashboard/aprendiz.html',
        'INSTRUCTOR': 'dashboard/instructor.html',
        'ADMINISTRATIVO': 'dashboard/administrativo.html',
        'VIGILANCIA': 'dashboard/vigilancia.html',
        'BRIGADA': 'dashboard/brigada.html',
        'VISITANTE': 'dashboard/visitante.html',
    }

    # Obtener el template según el rol
    template = dashboard_templates.get(usuario.rol, 'dashboard.html')

    # CALCULAR DATOS REALES
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)

    # Total de usuarios registrados
    total_usuarios = Usuario.objects.filter(activo=True).count()

    # Usuarios nuevos este mes
    usuarios_mes = Usuario.objects.filter(
        fecha_registro__gte=inicio_mes,
        activo=True
    ).count()

    # Personas actualmente en el centro (tienen ingreso pero no egreso)
    personas_en_centro = RegistroAcceso.objects.filter(
        tipo='INGRESO',
        fecha_hora_egreso__isnull=True,
        fecha_hora_ingreso__date=hoy
    ).count()

    # Ingresos totales hoy
    ingresos_hoy = RegistroAcceso.objects.filter(
        tipo='INGRESO',
        fecha_hora_ingreso__date=hoy
    ).count()

    # Visitantes hoy
    visitantes_hoy = Visitante.objects.filter(
        fecha_visita=hoy
    ).count()

    # Configuración de aforo
    try:
        config_aforo = ConfiguracionAforo.objects.filter(activo=True).first()
        aforo_maximo = config_aforo.aforo_maximo if config_aforo else 2000
    except Exception:
        aforo_maximo = 2000

    # Porcentaje de ocupación
    porcentaje_ocupacion = round((personas_en_centro / aforo_maximo) * 100, 1) if aforo_maximo > 0 else 0

    # Últimos 7 días de registros (para gráficas) - una sola query agrupada
    from django.db.models.functions import TruncDate
    fecha_inicio_7 = hoy - timedelta(days=6)
    registros_por_dia = dict(
        RegistroAcceso.objects.filter(
            tipo='INGRESO',
            fecha_hora_ingreso__date__gte=fecha_inicio_7,
            fecha_hora_ingreso__date__lte=hoy
        ).annotate(
            dia=TruncDate('fecha_hora_ingreso')
        ).values('dia').annotate(
            cantidad=Count('id')
        ).values_list('dia', 'cantidad')
    )
    ultimos_7_dias = []
    for i in range(6, -1, -1):
        fecha = hoy - timedelta(days=i)
        ultimos_7_dias.append({
            'fecha': fecha.strftime('%d/%m'),
            'cantidad': registros_por_dia.get(fecha, 0)
        })

    # Últimos 5 accesos
    ultimos_accesos = RegistroAcceso.objects.select_related('usuario').filter(
        tipo='INGRESO'
    ).order_by('-fecha_hora_ingreso')[:5]

    # Contexto con datos reales
    context = {
        'usuario': usuario,
        'rol': usuario.rol,
        'permisos': usuario.get_permissions(),
        # Métricas principales
        'total_usuarios': total_usuarios,
        'usuarios_mes': usuarios_mes,
        'personas_en_centro': personas_en_centro,
        'ingresos_hoy': ingresos_hoy,
        'visitantes_hoy': visitantes_hoy,
        'aforo_maximo': aforo_maximo,
        'porcentaje_ocupacion': porcentaje_ocupacion,
        # Datos para gráficas
        'ultimos_7_dias': ultimos_7_dias,
        'ultimos_accesos': ultimos_accesos,
    }

    # Datos adicionales para INSTRUCTOR
    if usuario.rol == 'INSTRUCTOR':
        total_aprendices = Usuario.objects.filter(rol='APRENDIZ', activo=True).count()
        # Aprendices que ingresaron hoy
        aprendices_ids_hoy = RegistroAcceso.objects.filter(
            tipo='INGRESO',
            fecha_hora_ingreso__date=hoy,
            usuario__rol='APRENDIZ'
        ).values_list('usuario_id', flat=True).distinct()
        aprendices_presentes = aprendices_ids_hoy.count()
        # Últimos 5 accesos de aprendices hoy
        ultimos_accesos_aprendices = RegistroAcceso.objects.select_related('usuario').filter(
            tipo='INGRESO',
            fecha_hora_ingreso__date=hoy,
            usuario__rol='APRENDIZ'
        ).order_by('-fecha_hora_ingreso')[:5]
        context['total_aprendices'] = total_aprendices
        context['aprendices_presentes'] = aprendices_presentes
        context['ultimos_accesos_aprendices'] = ultimos_accesos_aprendices

        # Lista de todos los aprendices con estado presente/ausente
        from django.db.models import Exists, OuterRef
        aprendices_con_estado = Usuario.objects.filter(
            rol='APRENDIZ', activo=True
        ).annotate(
            presente_hoy=Exists(
                RegistroAcceso.objects.filter(
                    usuario=OuterRef('pk'),
                    tipo='INGRESO',
                    fecha_hora_ingreso__date=hoy
                )
            )
        ).order_by('ficha', 'last_name', 'first_name')[:20]
        context['aprendices_con_estado'] = aprendices_con_estado

        # Estadísticas de asistencia por ficha (top 5 fichas con más aprendices)
        from django.db.models import Count
        fichas_stats = Usuario.objects.filter(
            rol='APRENDIZ', activo=True, ficha__isnull=False
        ).exclude(ficha='').values('ficha').annotate(
            total=Count('id')
        ).order_by('-total')[:5]

        for ficha in fichas_stats:
            presentes = RegistroAcceso.objects.filter(
                tipo='INGRESO',
                fecha_hora_ingreso__date=hoy,
                usuario__ficha=ficha['ficha'],
                usuario__rol='APRENDIZ'
            ).values('usuario_id').distinct().count()
            ficha['presentes'] = presentes
            ficha['porcentaje'] = round((presentes / ficha['total']) * 100) if ficha['total'] > 0 else 0

        context['fichas_stats'] = list(fichas_stats)

        # Incidentes del mes para el instructor
        from reportes.models import Incidente as IncidenteInstructor
        context['incidentes_mes'] = IncidenteInstructor.objects.filter(
            fecha_reporte__date__gte=inicio_mes
        ).count()

    # Datos adicionales para BRIGADA
    if usuario.rol == 'BRIGADA':
        from reportes.models import Incidente
        incidentes_recientes = Incidente.objects.select_related('reportado_por').order_by('-fecha_reporte')[:10]
        incidentes_pendientes = Incidente.objects.exclude(estado__in=['RESUELTO', 'CERRADO']).count()
        incidentes_total_mes = Incidente.objects.filter(fecha_reporte__date__gte=inicio_mes).count()
        context['incidentes_recientes'] = incidentes_recientes
        context['incidentes_pendientes'] = incidentes_pendientes
        context['incidentes_total_mes'] = incidentes_total_mes

    # Datos adicionales para APRENDIZ
    if usuario.rol == 'APRENDIZ':
        mis_accesos = RegistroAcceso.objects.filter(
            usuario=usuario,
            tipo='INGRESO',
            fecha_hora_ingreso__date__gte=inicio_mes
        ).order_by('-fecha_hora_ingreso')[:5]
        mis_ingresos_mes = RegistroAcceso.objects.filter(
            usuario=usuario,
            tipo='INGRESO',
            fecha_hora_ingreso__date__gte=inicio_mes
        ).count()
        context['mis_accesos'] = mis_accesos
        context['mis_ingresos_mes'] = mis_ingresos_mes

        # Datos para gráfica de asistencia mensual (últimos 30 días)
        asistencia_mensual = []
        for i in range(29, -1, -1):
            fecha = hoy - timedelta(days=i)
            asistio = RegistroAcceso.objects.filter(
                usuario=usuario,
                tipo='INGRESO',
                fecha_hora_ingreso__date=fecha
            ).exists()
            asistencia_mensual.append({
                'fecha': fecha.strftime('%d'),
                'fecha_completa': fecha.strftime('%d/%m'),
                'asistio': 1 if asistio else 0
            })
        context['asistencia_mensual'] = asistencia_mensual
        context['dias_asistidos_mes'] = sum(1 for d in asistencia_mensual if d['asistio'])

        # Contactos de emergencia
        from emergencias.models import ContactoExterno
        contactos_emergencia = ContactoExterno.objects.filter(activo=True).order_by('orden_contacto')[:5]
        context['contactos_emergencia'] = contactos_emergencia

    return render(request, template, context)

# ==============================================
# VISTA DE PERFIL (Todos los roles)
# ==============================================

@login_required
def mi_perfil_view(request):
    """
    Vista de perfil del usuario autenticado.
    Permite ver y editar datos personales.
    """
    from django.contrib import messages as django_messages

    usuario = request.user

    if request.method == 'POST':
        # Campos editables por el usuario
        usuario.first_name = request.POST.get('first_name', usuario.first_name).strip()
        usuario.last_name = request.POST.get('last_name', usuario.last_name).strip()
        usuario.email = request.POST.get('email', usuario.email).strip()
        usuario.telefono = request.POST.get('telefono', usuario.telefono).strip()
        usuario.telefono_emergencia = request.POST.get('telefono_emergencia', usuario.telefono_emergencia).strip()
        usuario.contacto_emergencia = request.POST.get('contacto_emergencia', usuario.contacto_emergencia).strip()

        # Foto de perfil
        if 'foto' in request.FILES:
            foto = request.FILES['foto']
            if foto.size > 5 * 1024 * 1024:
                django_messages.error(request, 'La foto no puede superar 5 MB.')
                return redirect('mi_perfil')
            if not foto.content_type.startswith('image/'):
                django_messages.error(request, 'El archivo debe ser una imagen.')
                return redirect('mi_perfil')
            usuario.foto = foto

        usuario.save()
        django_messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('mi_perfil')

    # Contexto con información adicional según el rol
    from control_acceso.models import RegistroAcceso
    from django.utils import timezone

    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)

    total_accesos_mes = RegistroAcceso.objects.filter(
        usuario=usuario,
        tipo='INGRESO',
        fecha_hora_ingreso__date__gte=inicio_mes
    ).count()

    ultimo_acceso = RegistroAcceso.objects.filter(
        usuario=usuario,
        tipo='INGRESO'
    ).order_by('-fecha_hora_ingreso').first()

    context = {
        'usuario': usuario,
        'total_accesos_mes': total_accesos_mes,
        'ultimo_acceso': ultimo_acceso,
    }

    return render(request, 'perfil.html', context)


# ==============================================
# VISTAS ESPECÍFICAS PARA APRENDIZ
# ==============================================

@login_required
@rol_requerido('APRENDIZ')
def mi_asistencia_view(request):
    """
    Vista de asistencia del aprendiz
    """
    # Aquí puedes agregar lógica para obtener datos reales de asistencia
    from control_acceso.models import RegistroAcceso
    from django.utils import timezone
    from datetime import timedelta
    
    usuario = request.user
    hoy = timezone.now().date()
    
    # Obtener registros de este mes
    inicio_mes = hoy.replace(day=1)
    registros_mes = RegistroAcceso.objects.filter(
        usuario=usuario,
        tipo='INGRESO',
        fecha_hora_ingreso__gte=inicio_mes
    ).order_by('-fecha_hora_ingreso')
    
    context = {
        'usuario': usuario,
        'registros_mes': registros_mes,
        'dias_asistidos': registros_mes.count(),
        'total_dias_mes': hoy.day,
    }
    
    return render(request, 'dashboard/aprendiz/mi_asistencia.html', context)

@login_required
@rol_requerido('APRENDIZ')
def informacion_sst_view(request):
    """
    Vista de información SST para el aprendiz
    """
    return render(request, 'dashboard/aprendiz/informacion_sst.html')

@login_required
@excluir_visitantes
def mis_alertas_view(request):
    """
    Vista de alertas/notificaciones del usuario
    Accesible por todos los roles excepto visitante
    """
    from usuarios.models import Notificacion

    # Obtener notificaciones del usuario actual
    notificaciones = Notificacion.objects.filter(destinatario=request.user)

    # Separar por estado de lectura
    no_leidas = notificaciones.filter(leida=False).order_by('-fecha_creacion')[:10]
    leidas = notificaciones.filter(leida=True).order_by('-fecha_creacion')[:10]
    historial = notificaciones.order_by('-fecha_creacion')[:20]

    # Contar no leidas
    total_no_leidas = notificaciones.filter(leida=False).count()

    context = {
        'no_leidas': no_leidas,
        'leidas': leidas,
        'historial': historial,
        'total_no_leidas': total_no_leidas,
    }
    return render(request, 'dashboard/aprendiz/mis_alertas.html', context)

# ==============================================
# FIN VISTAS PARA APRENDIZ
# ==============================================

# ==============================================
# VISTAS ESPECÍFICAS PARA INSTRUCTOR
# ==============================================

@login_required
@rol_requerido('INSTRUCTOR')
def mis_aprendices_view(request):
    """
    Vista para que el instructor filtre por programa -> ficha -> aprendices
    Incluye información de asistencia del día actual
    """
    from usuarios.models import Usuario
    from control_acceso.models import RegistroAcceso
    from django.utils import timezone

    # Obtener programas dinámicamente de la BD
    PROGRAMAS = list(
        Usuario.objects.filter(
            rol='APRENDIZ', activo=True, programa_formacion__isnull=False
        ).exclude(programa_formacion='').values_list(
            'programa_formacion', flat=True
        ).distinct().order_by('programa_formacion')
    )

    programa_seleccionado = request.GET.get('programa', '')
    ficha_seleccionada = request.GET.get('ficha', '')
    fichas = []
    aprendices_con_asistencia = []
    total_aprendices = 0
    presentes_hoy = 0

    if programa_seleccionado:
        fichas = Usuario.objects.filter(
            rol='APRENDIZ', activo=True, programa_formacion=programa_seleccionado
        ).values_list('ficha', flat=True).distinct().order_by('ficha')

    if ficha_seleccionada:
        from django.db.models import OuterRef, Subquery, Exists

        hoy = timezone.now().date()

        # Subquery para obtener el último registro de hoy por aprendiz
        ultimo_registro_hoy = RegistroAcceso.objects.filter(
            usuario=OuterRef('pk'),
            fecha_hora_ingreso__date=hoy
        ).order_by('-fecha_hora_ingreso')

        aprendices = Usuario.objects.filter(
            rol='APRENDIZ', activo=True, ficha=ficha_seleccionada, programa_formacion=programa_seleccionado
        ).annotate(
            tiene_registro_hoy=Exists(
                RegistroAcceso.objects.filter(
                    usuario=OuterRef('pk'),
                    fecha_hora_ingreso__date=hoy
                )
            ),
            _en_centro=Exists(
                RegistroAcceso.objects.filter(
                    usuario=OuterRef('pk'),
                    fecha_hora_ingreso__date=hoy,
                    fecha_hora_egreso__isnull=True
                )
            ),
            _hora_ingreso=Subquery(ultimo_registro_hoy.values('fecha_hora_ingreso')[:1]),
        ).order_by('last_name', 'first_name')

        total_aprendices = aprendices.count()

        for aprendiz in aprendices:
            # Para el conteo de asistencia: tiene registro hoy = asistio
            asistio = aprendiz.tiene_registro_hoy
            hora_ingreso = aprendiz._hora_ingreso

            if asistio:
                presentes_hoy += 1

            aprendices_con_asistencia.append({
                'usuario': aprendiz,
                'presente': aprendiz._en_centro,
                'hora_ingreso': hora_ingreso,
                'tiene_registro_hoy': asistio,
            })

    ausentes = total_aprendices - presentes_hoy
    porcentaje_asistencia = round((presentes_hoy / total_aprendices) * 100) if total_aprendices > 0 else 0

    context = {
        'programas': PROGRAMAS,
        'programa_seleccionado': programa_seleccionado,
        'fichas': fichas,
        'ficha_seleccionada': ficha_seleccionada,
        'aprendices': aprendices_con_asistencia,
        'total_aprendices': total_aprendices,
        'presentes_hoy': presentes_hoy,
        'ausentes': ausentes,
        'porcentaje_asistencia': porcentaje_asistencia,
    }
    return render(request, 'dashboard/instructor/mis_aprendices.html', context)


# ==============================================
# VISTAS ESPECÍFICAS PARA ADMINISTRATIVO
# ==============================================

@login_required
@rol_requerido('ADMINISTRATIVO')
def gestion_usuarios_view(request):
    """
    Vista para gestión de usuarios (Administrativo)
    """
    from usuarios.models import Usuario
    # Excluir superusuarios para seguridad básica en la vista
    usuarios = Usuario.objects.all().exclude(is_superuser=True).order_by('-fecha_registro')
    
    context = {
        'usuarios': usuarios,
        'total_usuarios': usuarios.count()
    }
    return render(request, 'dashboard/administrativo/gestion_usuarios.html', context)

@login_required
@rol_requerido('ADMINISTRATIVO')
def configuracion_view(request):
    """
    Vista de configuración del sistema
    """
    from control_acceso.models import ConfiguracionAforo
    config_aforo = ConfiguracionAforo.objects.filter(activo=True).first()
    
    context = {
        'config_aforo': config_aforo
    }
    return render(request, 'dashboard/administrativo/configuracion.html', context)

# ==============================================
# VISTAS ESPECÍFICAS PARA VIGILANCIA
# ==============================================

@login_required
@rol_requerido('VIGILANCIA')
def gestion_visitantes_view(request):
    """
    Vista para gestión de visitantes (Vigilancia)
    """
    from usuarios.models import Visitante
    from django.utils import timezone
    
    hoy = timezone.now().date()
    # Visitantes registrados hoy
    visitantes_hoy = Visitante.objects.filter(fecha_visita=hoy).order_by('-hora_ingreso')
    
    context = {
        'visitantes': visitantes_hoy,
        'total_hoy': visitantes_hoy.count(),
        'activos_ahora': visitantes_hoy.filter(hora_salida__isnull=True).count()
    }
    return render(request, 'dashboard/vigilancia/gestion_visitantes.html', context)

@login_required
@rol_requerido('BRIGADA')
def equipos_brigada_view(request):
    """
    Vista para gestión de equipos de emergencia (Brigada)
    """
    from mapas.models import EquipamientoSeguridad, EdificioBloque
    from django.utils import timezone
    from datetime import timedelta

    # Obtener parámetros de filtrado
    tipo_filtro = request.GET.get('tipo', '')
    estado_filtro = request.GET.get('estado', '')
    busqueda = request.GET.get('q', '')

    # Consultar equipos reales de la BD
    equipos = EquipamientoSeguridad.objects.select_related('edificio', 'responsable').all()

    # Aplicar filtros
    if tipo_filtro:
        equipos = equipos.filter(tipo=tipo_filtro)
    if estado_filtro:
        equipos = equipos.filter(estado=estado_filtro)
    if busqueda:
        equipos = equipos.filter(
            models.Q(nombre__icontains=busqueda) |
            models.Q(codigo__icontains=busqueda) |
            models.Q(edificio__nombre__icontains=busqueda)
        )

    # Ordenar por estado (primero los que necesitan atención)
    equipos = equipos.order_by(
        models.Case(
            models.When(estado='FUERA_SERVICIO', then=0),
            models.When(estado='MANTENIMIENTO', then=1),
            default=2
        ),
        'tipo', 'codigo'
    )

    # Estadísticas
    total_equipos = EquipamientoSeguridad.objects.count()
    operativos = EquipamientoSeguridad.objects.filter(estado='OPERATIVO').count()
    en_mantenimiento = EquipamientoSeguridad.objects.filter(estado='MANTENIMIENTO').count()
    fuera_servicio = EquipamientoSeguridad.objects.filter(estado='FUERA_SERVICIO').count()

    # Equipos que necesitan revisión pronto (próximos 30 días)
    fecha_limite = timezone.now() + timedelta(days=30)
    proximos_revision = EquipamientoSeguridad.objects.filter(
        proxima_revision__lte=fecha_limite,
        proxima_revision__gte=timezone.now()
    ).count()

    # Tipos de equipamiento para el filtro
    tipos_equipamiento = EquipamientoSeguridad.TIPO_EQUIPAMIENTO

    context = {
        'equipos': equipos,
        'total_equipos': total_equipos,
        'operativos': operativos,
        'en_mantenimiento': en_mantenimiento,
        'fuera_servicio': fuera_servicio,
        'proximos_revision': proximos_revision,
        'tipos_equipamiento': tipos_equipamiento,
        'tipo_filtro': tipo_filtro,
        'estado_filtro': estado_filtro,
        'busqueda': busqueda,
    }
    return render(request, 'dashboard/brigada/equipos.html', context)

@login_required
@rol_requerido('BRIGADA')
def mi_brigada_view(request):
    """
    Vista para ver los miembros de la brigada
    """
    from usuarios.models import Usuario
    miembros = Usuario.objects.filter(rol='BRIGADA', activo=True).exclude(id=request.user.id)
    context = {
        'miembros': miembros,
        'total_miembros': miembros.count() + 1 # Contando al usuario actual
    }
    return render(request, 'dashboard/brigada/mi_brigada.html', context)

# ==============================================

# Vistas para usuarios autenticados (usan base.html)
@rol_requerido('ADMINISTRATIVO', 'VIGILANCIA')
def control_acceso_view(request):
    """
    Vista de Control de Acceso
    PERMISOS: Solo ADMINISTRATIVO y VIGILANCIA
    """
    return render(request, 'control_acceso.html')

# Importar la vista completa de mapas
from mapas.views import mapa_interactivo

# Decorador aplicado directamente en la vista mapa_interactivo en mapas/views.py

@excluir_visitantes
def emergencias_view(request):
    """
    Vista de Emergencias
    PERMISOS: Todos excepto VISITANTE
    """
    return render(request, 'emergencias.html')

@excluir_visitantes
def reportes_view(request):
    """
    Vista de Reportes
    PERMISOS: Todos excepto VISITANTE
    """
    return render(request, 'reportes.html')

urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticación - Rutas principales (con debugging temporal)
    path('accounts/login/', custom_login_view, name='login'),

    path('accounts/logout/', auth_views.LogoutView.as_view(
        next_page='login'
    ), name='logout'),

    # Recuperar Clave
    path('accounts/password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/recuperar_clave.html',
            email_template_name='registration/email_recuperacion.html',
            subject_template_name='registration/asunto_email.txt',
        ),
        name='password_reset'
    ),

    path('accounts/password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/correo_enviado.html'
        ),
        name='password_reset_done'
    ),

    path('accounts/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/nueva_clave.html'
        ),
        name='password_reset_confirm'
    ),

    path('accounts/reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/clave_cambiada.html'
        ),
        name='password_reset_complete'
    ),

    # Vistas principales del sistema (HTML templates)
    path('', dashboard_view, name='dashboard'),
    path('dashboard/', RedirectView.as_view(url='/', permanent=False)),
    path('perfil/', mi_perfil_view, name='mi_perfil'),
    path('acceso/', control_acceso_view, name='control_acceso'),
    path('mapas/', mapa_interactivo, name='mapas'),
    path('emergencias/', emergencias_view, name='emergencias'),

    # ==============================================
    # URLs ESPECÍFICAS PARA APRENDIZ
    # ==============================================
    path('aprendiz/mis-accesos/', mi_asistencia_view, name='mi_asistencia'),
    path('aprendiz/informacion-sst/', informacion_sst_view, name='informacion_sst'),
    path('aprendiz/alertas/', mis_alertas_view, name='mis_alertas'),
    # ==============================================

    # URLs PARA INSTRUCTOR
    path('instructor/mis-aprendices/', mis_aprendices_view, name='mis_aprendices'),

    # URLs PARA ADMINISTRATIVO
    path('administrativo/usuarios/', gestion_usuarios_view, name='gestion_usuarios'),
    path('administrativo/configuracion/', configuracion_view, name='configuracion_sistema'),

    # URLs PARA VIGILANCIA
    path('vigilancia/visitantes/', gestion_visitantes_view, name='gestion_visitantes'),

    # URLs PARA BRIGADA
    path('brigada/equipos/', equipos_brigada_view, name='equipos_brigada'),
    path('brigada/mi-brigada/', mi_brigada_view, name='mi_brigada'),
    # Vista General de Reportes
    path('reportes/general/', reportes_view, name='reportes_general'),

    # APIs REST (para operaciones AJAX/fetch desde el frontend)
    path('api/auth/', include('usuarios.urls')),
    path('api/acceso/', include('control_acceso.urls')),
    path('api/mapas/', include('mapas.urls')),
    path('api/emergencias/', include('emergencias.urls')),

    # Módulo de reportes (incluye vistas HTML de incidentes y API)
    path('reportes/', include('reportes.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
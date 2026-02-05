from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login, logout
from .models import Usuario, Visitante
from .serializers import UsuarioSerializer, LoginSerializer, VisitanteSerializer
# DESHABILITADO - Solo registro físico/manual
# from control_acceso.utils import generar_qr_usuario, generar_qr_visitante
from .permissions import PuedeGestionarUsuarios, EsAdministrativoOInstructor

class UsuarioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar usuarios
    PERMISOS:
    - Login/Registro: Todos (sin autenticación)
    - Ver perfil propio: Todos autenticados
    - Listar/Modificar usuarios: Solo ADMINISTRATIVO
    """
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    def get_permissions(self):
        # Permitir login y registro sin autenticación
        if self.action in ['login', 'create']:
            return [AllowAny()]

        # Ver perfil propio: todos
        if self.action in ['perfil']:
            return [IsAuthenticated()]

        # Gestionar usuarios: solo ADMINISTRATIVO
        if self.action in ['list', 'update', 'partial_update', 'destroy']:
            return [PuedeGestionarUsuarios()]

        return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        """Registro de nuevos usuarios - Simplificado"""
        try:
            # Validar contraseñas coincidan
            password = request.data.get('password')
            password2 = request.data.get('password2')
            
            if not password or not password2:
                return Response(
                    {'error': 'Debes proporcionar ambas contraseñas'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if password != password2:
                return Response(
                    {'error': 'Las contraseñas no coinciden'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(password) < 8:
                return Response(
                    {'error': 'La contraseña debe tener al menos 8 caracteres'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar campos requeridos
            username = request.data.get('username')
            email = request.data.get('email')
            numero_documento = request.data.get('numero_documento')
            tipo_documento = request.data.get('tipo_documento')
            rol = request.data.get('rol')
            
            if not all([username, email, numero_documento, tipo_documento, rol]):
                return Response(
                    {'error': 'Todos los campos son obligatorios'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar que el documento no exista
            if Usuario.objects.filter(numero_documento=numero_documento).exists():
                return Response(
                    {'error': 'Ya existe un usuario con este número de documento'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar que el username no exista
            if Usuario.objects.filter(username=username).exists():
                return Response(
                    {'error': 'Este nombre de usuario ya está en uso'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validar que el email no exista
            if Usuario.objects.filter(email=email).exists():
                return Response(
                    {'error': 'Este correo electrónico ya está registrado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Campos opcionales
            first_name = request.data.get('first_name', '').strip()
            last_name = request.data.get('last_name', '').strip()

            if not first_name or not last_name:
                return Response(
                    {'error': 'El nombre y apellido son obligatorios'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Campos exclusivos de aprendiz
            ficha = request.data.get('ficha', '').strip()
            programa_formacion = request.data.get('programa_formacion', '').strip()

            if rol == 'APRENDIZ' and (not ficha or not programa_formacion):
                return Response(
                    {'error': 'El número de ficha y programa de formación son obligatorios para aprendices'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Crear usuario
            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                rol=rol,
                tipo_documento=tipo_documento,
                numero_documento=numero_documento,
                first_name=first_name,
                last_name=last_name,
                ficha=ficha if rol == 'APRENDIZ' else None,
                programa_formacion=programa_formacion if rol == 'APRENDIZ' else None,
            )
            
            # Crear token
            token, created = Token.objects.get_or_create(user=usuario)
            
            return Response({
                'id': usuario.id,
                'username': usuario.username,
                'email': usuario.email,
                'rol': usuario.rol,
                'token': token.key,
                'mensaje': 'Usuario registrado exitosamente. Ya puedes iniciar sesión.'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Error al crear el usuario: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        usuario = serializer.validated_data['usuario']
        login(request, usuario)
        token, created = Token.objects.get_or_create(user=usuario)

        return Response({
            'token': token.key,
            'usuario': UsuarioSerializer(usuario).data,
            'mensaje': 'Login exitoso.'
        })
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            request.user.auth_token.delete()
        except:
            pass
        logout(request)
        return Response({'mensaje': 'Logout exitoso.'})
    
    @action(detail=False, methods=['get'])
    def perfil(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    # DESHABILITADO - Solo registro físico/manual
    # @action(detail=True, methods=['get'])
    # def generar_qr(self, request, pk=None):
    #     """
    #     Genera el código QR para un usuario
    #     """
    #     usuario = self.get_object()
    #     qr_base64 = generar_qr_usuario(usuario)
    #
    #     return Response({
    #         'usuario_id': usuario.id,
    #         'nombre': usuario.get_full_name(),
    #         'documento': usuario.numero_documento,
    #         'rol': usuario.get_rol_display(),
    #         'qr_image': qr_base64
    #     })
    #
    # @action(detail=False, methods=['get'])
    # def mi_qr(self, request):
    #     """
    #     Genera el código QR del usuario autenticado
    #     """
    #     qr_base64 = generar_qr_usuario(request.user)
    #
    #     return Response({
    #         'usuario_id': request.user.id,
    #         'nombre': request.user.get_full_name(),
    #         'documento': request.user.numero_documento,
    #         'rol': request.user.get_rol_display(),
    #         'qr_image': qr_base64
    #     })
    
class VisitanteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar visitantes
    PERMISOS: VIGILANCIA, ADMINISTRATIVO e INSTRUCTOR
    """
    queryset = Visitante.objects.all()
    serializer_class = VisitanteSerializer

    def get_permissions(self):
        # Solo VIGILANCIA, ADMINISTRATIVO e INSTRUCTOR pueden gestionar visitantes
        return [EsAdministrativoOInstructor()]

    def perform_create(self, serializer):
        serializer.save(registrado_por=self.request.user)

    # DESHABILITADO - Solo registro físico/manual
    # @action(detail=True, methods=['get'])
    # def generar_qr(self, request, pk=None):
    #     """
    #     Genera el código QR para un visitante
    #     """
    #     visitante = self.get_object()
    #     qr_base64 = generar_qr_visitante(visitante)
    #
    #     return Response({
    #         'visitante_id': visitante.id,
    #         'nombre': visitante.nombre_completo,
    #         'documento': visitante.numero_documento,
    #         'entidad': visitante.entidad,
    #         'qr_image': qr_base64
    #     })


class NotificacionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar notificaciones del usuario
    """
    from .serializers import NotificacionSerializer
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Solo retorna las notificaciones del usuario actual"""
        from .models import Notificacion
        return Notificacion.objects.filter(destinatario=self.request.user)

    @action(detail=True, methods=['post'])
    def marcar_leida(self, request, pk=None):
        """Marca una notificacion como leida"""
        from django.utils import timezone
        try:
            notificacion = self.get_object()
            notificacion.leida = True
            notificacion.fecha_lectura = timezone.now()
            notificacion.save()
            return Response({
                'success': True,
                'message': 'Notificacion marcada como leida'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def marcar_todas_leidas(self, request):
        """Marca todas las notificaciones del usuario como leidas"""
        from django.utils import timezone
        from .models import Notificacion
        try:
            actualizadas = Notificacion.objects.filter(
                destinatario=request.user,
                leida=False
            ).update(leida=True, fecha_lectura=timezone.now())

            return Response({
                'success': True,
                'message': f'{actualizadas} notificacion(es) marcadas como leidas'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def no_leidas(self, request):
        """Retorna solo las notificaciones no leidas"""
        from .models import Notificacion
        notificaciones = Notificacion.objects.filter(
            destinatario=request.user,
            leida=False
        ).order_by('-fecha_creacion')[:10]

        return Response({
            'count': notificaciones.count(),
            'notificaciones': self.get_serializer(notificaciones, many=True).data
        })

    @action(detail=False, methods=['get'])
    def count(self, request):
        """Retorna el conteo de notificaciones no leidas (para badge en navbar)"""
        from .models import Notificacion
        count = Notificacion.objects.filter(
            destinatario=request.user,
            leida=False
        ).count()

        return Response({'count': count})


class EstadisticasViewSet(viewsets.ViewSet):
    """
    ViewSet para estadísticas consolidadas del dashboard
    GET /api/estadisticas/dashboard/ - Estadísticas generales (todos)
    GET /api/estadisticas/acceso/ - Estadísticas de acceso (Vigilancia, Admin)
    GET /api/estadisticas/emergencias/ - Estadísticas de emergencias (Brigada, Admin)
    GET /api/estadisticas/incidentes/ - Estadísticas de incidentes (todos)
    GET /api/estadisticas/equipamiento/ - Estadísticas de equipamiento (Brigada, Admin)
    GET /api/estadisticas/asistencia-por-ficha/ - Asistencia (Instructor, Admin)
    GET /api/estadisticas/asistencia-aprendices/ - Lista aprendices (Instructor, Admin)
    """
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Permisos específicos por acción"""
        from .permissions import (
            EsVigilanciaOAdministrativo,
            EsBrigadaOAdministrativo,
            EsAdministrativoOInstructor
        )

        if self.action in ['acceso']:
            return [EsVigilanciaOAdministrativo()]
        elif self.action in ['emergencias', 'equipamiento']:
            return [EsBrigadaOAdministrativo()]
        elif self.action in ['asistencia_por_ficha', 'asistencia_aprendices']:
            return [EsAdministrativoOInstructor()]

        # dashboard, incidentes: todos los autenticados
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        Retorna estadísticas consolidadas para el dashboard principal.
        Incluye métricas clave de todos los módulos.
        """
        from django.utils import timezone
        from django.db.models import Count, Q
        from datetime import timedelta

        hoy = timezone.now().date()
        inicio_mes = hoy.replace(day=1)
        ahora = timezone.now()

        stats = {
            'fecha_consulta': ahora.isoformat(),
            'acceso': self._get_stats_acceso(hoy),
            'emergencias': self._get_stats_emergencias(inicio_mes),
            'incidentes': self._get_stats_incidentes(inicio_mes),
            'equipamiento': self._get_stats_equipamiento(),
            'usuarios': self._get_stats_usuarios(),
        }

        return Response(stats)

    @action(detail=False, methods=['get'])
    def acceso(self, request):
        """Estadísticas detalladas de control de acceso"""
        from django.utils import timezone
        hoy = timezone.now().date()
        return Response(self._get_stats_acceso(hoy, detallado=True))

    @action(detail=False, methods=['get'])
    def emergencias(self, request):
        """Estadísticas detalladas de emergencias"""
        from django.utils import timezone
        inicio_mes = timezone.now().date().replace(day=1)
        return Response(self._get_stats_emergencias(inicio_mes, detallado=True))

    @action(detail=False, methods=['get'])
    def incidentes(self, request):
        """Estadísticas detalladas de incidentes"""
        from django.utils import timezone
        inicio_mes = timezone.now().date().replace(day=1)
        return Response(self._get_stats_incidentes(inicio_mes, detallado=True))

    @action(detail=False, methods=['get'])
    def equipamiento(self, request):
        """Estadísticas detalladas de equipamiento"""
        return Response(self._get_stats_equipamiento(detallado=True))

    def _get_stats_acceso(self, hoy, detallado=False):
        """Obtiene estadísticas de acceso"""
        from control_acceso.models import RegistroAcceso, ConfiguracionAforo
        from django.db.models import Count

        # Personas actualmente en el centro
        personas_dentro = RegistroAcceso.objects.filter(
            fecha_hora_ingreso__date=hoy,
            fecha_hora_egreso__isnull=True
        ).count()

        # Ingresos del día
        ingresos_hoy = RegistroAcceso.objects.filter(
            fecha_hora_ingreso__date=hoy
        ).count()

        # Configuración de aforo
        config = ConfiguracionAforo.objects.filter(activo=True).first()
        aforo_maximo = config.aforo_maximo if config else 2000
        porcentaje = round((personas_dentro / aforo_maximo) * 100, 1) if aforo_maximo > 0 else 0

        stats = {
            'personas_dentro': personas_dentro,
            'ingresos_hoy': ingresos_hoy,
            'aforo_maximo': aforo_maximo,
            'porcentaje_ocupacion': porcentaje,
            'estado_aforo': 'CRITICO' if porcentaje >= 90 else 'ALERTA' if porcentaje >= 70 else 'NORMAL'
        }

        if detallado:
            # Distribución por rol
            from django.db.models import F
            distribucion = RegistroAcceso.objects.filter(
                fecha_hora_ingreso__date=hoy,
                fecha_hora_egreso__isnull=True
            ).values('usuario__rol').annotate(total=Count('id'))

            stats['distribucion_por_rol'] = {
                item['usuario__rol']: item['total'] for item in distribucion
            }

            # Visitantes activos
            visitantes_activos = Visitante.objects.filter(
                fecha_visita=hoy,
                hora_salida__isnull=True
            ).count()
            stats['visitantes_activos'] = visitantes_activos

        return stats

    def _get_stats_emergencias(self, inicio_mes, detallado=False):
        """Obtiene estadísticas de emergencias"""
        try:
            from emergencias.models import Emergencia
            from django.db.models import Count, Avg, F
            from django.db.models.functions import Extract

            # Emergencias del mes
            emergencias_mes = Emergencia.objects.filter(
                fecha_hora_reporte__date__gte=inicio_mes
            )

            # Conteo por estado
            activas = emergencias_mes.filter(estado__in=['REPORTADA', 'EN_ATENCION']).count()
            resueltas = emergencias_mes.filter(estado__in=['RESUELTA', 'CONTROLADA']).count()
            total_mes = emergencias_mes.count()

            stats = {
                'activas': activas,
                'resueltas': resueltas,
                'total_mes': total_mes,
                'tasa_resolucion': round((resueltas / total_mes) * 100, 1) if total_mes > 0 else 0
            }

            if detallado:
                # Por tipo
                por_tipo = emergencias_mes.values('tipo__nombre').annotate(
                    total=Count('id')
                ).order_by('-total')
                stats['por_tipo'] = list(por_tipo)

                # Por estado
                por_estado = emergencias_mes.values('estado').annotate(
                    total=Count('id')
                )
                stats['por_estado'] = {item['estado']: item['total'] for item in por_estado}

            return stats
        except Exception:
            return {'activas': 0, 'resueltas': 0, 'total_mes': 0, 'tasa_resolucion': 0}

    def _get_stats_incidentes(self, inicio_mes, detallado=False):
        """Obtiene estadísticas de incidentes"""
        try:
            from reportes.models import Incidente
            from django.db.models import Count

            incidentes_mes = Incidente.objects.filter(
                fecha_reporte__date__gte=inicio_mes
            )

            pendientes = incidentes_mes.filter(estado='REPORTADO').count()
            en_proceso = incidentes_mes.filter(estado__in=['EN_REVISION', 'EN_PROCESO']).count()
            resueltos = incidentes_mes.filter(estado='RESUELTO').count()
            total_mes = incidentes_mes.count()

            stats = {
                'pendientes': pendientes,
                'en_proceso': en_proceso,
                'resueltos': resueltos,
                'total_mes': total_mes
            }

            if detallado:
                # Por gravedad
                por_gravedad = incidentes_mes.values('gravedad').annotate(
                    total=Count('id')
                )
                stats['por_gravedad'] = {item['gravedad']: item['total'] for item in por_gravedad}

                # Por tipo
                por_tipo = incidentes_mes.values('tipo').annotate(
                    total=Count('id')
                ).order_by('-total')
                stats['por_tipo'] = list(por_tipo)

            return stats
        except Exception:
            return {'pendientes': 0, 'en_proceso': 0, 'resueltos': 0, 'total_mes': 0}

    def _get_stats_equipamiento(self, detallado=False):
        """Obtiene estadísticas de equipamiento de seguridad"""
        try:
            from mapas.models import EquipamientoSeguridad
            from django.db.models import Count

            equipos = EquipamientoSeguridad.objects.filter(activo=True)

            operativos = equipos.filter(estado='OPERATIVO').count()
            en_mantenimiento = equipos.filter(estado='MANTENIMIENTO').count()
            fuera_servicio = equipos.filter(estado='FUERA_SERVICIO').count()
            total = equipos.count()

            stats = {
                'operativos': operativos,
                'en_mantenimiento': en_mantenimiento,
                'fuera_servicio': fuera_servicio,
                'total': total,
                'porcentaje_operativo': round((operativos / total) * 100, 1) if total > 0 else 0
            }

            if detallado:
                # Por tipo
                por_tipo = equipos.values('tipo').annotate(
                    total=Count('id'),
                    operativos=Count('id', filter=Q(estado='OPERATIVO'))
                )
                stats['por_tipo'] = list(por_tipo)

            return stats
        except Exception:
            return {'operativos': 0, 'en_mantenimiento': 0, 'fuera_servicio': 0, 'total': 0, 'porcentaje_operativo': 0}

    def _get_stats_usuarios(self):
        """Obtiene estadísticas de usuarios"""
        from django.db.models import Count

        usuarios = Usuario.objects.filter(activo=True)

        por_rol = usuarios.values('rol').annotate(total=Count('id'))
        total = usuarios.count()

        return {
            'total_activos': total,
            'por_rol': {item['rol']: item['total'] for item in por_rol}
        }

    # ============================================================
    # ENDPOINTS PARA INSTRUCTORES - ASISTENCIA
    # ============================================================

    @action(detail=False, methods=['get'], url_path='asistencia-por-ficha')
    def asistencia_por_ficha(self, request):
        """
        Retorna estadísticas de asistencia agrupadas por ficha.
        Útil para el dashboard de instructor.

        Query params:
        - fecha: fecha específica (YYYY-MM-DD), por defecto hoy
        - periodo: 'hoy', 'semana', 'mes' (ignora fecha si se especifica)
        """
        from django.utils import timezone
        from django.db.models import Count, Q, Exists, OuterRef
        from control_acceso.models import RegistroAcceso
        from datetime import timedelta

        # Determinar fecha o periodo
        periodo = request.query_params.get('periodo', 'hoy')
        fecha_str = request.query_params.get('fecha')

        hoy = timezone.now().date()

        if fecha_str:
            try:
                from datetime import datetime
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                fecha = hoy
        else:
            fecha = hoy

        # Determinar rango de fechas según periodo
        if periodo == 'semana':
            fecha_inicio = hoy - timedelta(days=7)
            fecha_fin = hoy
        elif periodo == 'mes':
            fecha_inicio = hoy.replace(day=1)
            fecha_fin = hoy
        else:  # hoy
            fecha_inicio = fecha
            fecha_fin = fecha

        # Obtener fichas únicas de aprendices activos
        fichas = Usuario.objects.filter(
            rol='APRENDIZ',
            activo=True,
            ficha__isnull=False
        ).exclude(ficha='').values_list('ficha', flat=True).distinct()

        resultado = []

        for ficha in fichas:
            # Total de aprendices en esta ficha
            aprendices = Usuario.objects.filter(
                rol='APRENDIZ',
                activo=True,
                ficha=ficha
            )
            total = aprendices.count()

            # Aprendices con registro de acceso en el periodo
            if periodo == 'hoy':
                presentes = aprendices.filter(
                    accesos__fecha_hora_ingreso__date=fecha
                ).distinct().count()
            else:
                presentes = aprendices.filter(
                    accesos__fecha_hora_ingreso__date__gte=fecha_inicio,
                    accesos__fecha_hora_ingreso__date__lte=fecha_fin
                ).distinct().count()

            porcentaje = round((presentes / total) * 100, 1) if total > 0 else 0

            resultado.append({
                'ficha': ficha,
                'total': total,
                'presentes': presentes,
                'ausentes': total - presentes,
                'porcentaje': porcentaje
            })

        # Ordenar por ficha
        resultado.sort(key=lambda x: x['ficha'])

        return Response({
            'fecha': fecha.isoformat() if periodo == 'hoy' else None,
            'periodo': periodo,
            'fecha_inicio': fecha_inicio.isoformat(),
            'fecha_fin': fecha_fin.isoformat(),
            'fichas': resultado,
            'resumen': {
                'total_fichas': len(resultado),
                'total_aprendices': sum(f['total'] for f in resultado),
                'total_presentes': sum(f['presentes'] for f in resultado),
                'promedio_asistencia': round(
                    sum(f['porcentaje'] for f in resultado) / len(resultado), 1
                ) if resultado else 0
            }
        })

    @action(detail=False, methods=['get'], url_path='asistencia-aprendices')
    def asistencia_aprendices(self, request):
        """
        Retorna lista de aprendices con su estado de asistencia.

        Query params:
        - ficha: número de ficha (requerido o 'todas')
        - fecha: fecha específica (YYYY-MM-DD), por defecto hoy
        """
        from django.utils import timezone
        from django.db.models import Exists, OuterRef, Max
        from control_acceso.models import RegistroAcceso

        ficha = request.query_params.get('ficha')
        fecha_str = request.query_params.get('fecha')

        hoy = timezone.now().date()

        if fecha_str:
            try:
                from datetime import datetime
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                fecha = hoy
        else:
            fecha = hoy

        # Obtener aprendices
        aprendices = Usuario.objects.filter(
            rol='APRENDIZ',
            activo=True
        )

        if ficha and ficha != 'todas':
            aprendices = aprendices.filter(ficha=ficha)

        # Anotar con estado de asistencia
        aprendices = aprendices.annotate(
            presente_hoy=Exists(
                RegistroAcceso.objects.filter(
                    usuario=OuterRef('pk'),
                    fecha_hora_ingreso__date=fecha
                )
            ),
            ultima_entrada=Max(
                'accesos__fecha_hora_ingreso',
                filter=Q(accesos__fecha_hora_ingreso__date=fecha)
            )
        ).order_by('ficha', 'last_name', 'first_name')

        resultado = []
        for aprendiz in aprendices:
            resultado.append({
                'id': aprendiz.id,
                'nombre': aprendiz.get_full_name() or aprendiz.username,
                'documento': aprendiz.numero_documento,
                'ficha': aprendiz.ficha,
                'programa': aprendiz.programa_formacion,
                'presente': aprendiz.presente_hoy,
                'hora_entrada': aprendiz.ultima_entrada.strftime('%H:%M') if aprendiz.ultima_entrada else None
            })

        presentes = sum(1 for a in resultado if a['presente'])
        total = len(resultado)

        return Response({
            'fecha': fecha.isoformat(),
            'ficha': ficha or 'todas',
            'total': total,
            'presentes': presentes,
            'ausentes': total - presentes,
            'porcentaje': round((presentes / total) * 100, 1) if total > 0 else 0,
            'aprendices': resultado
        })
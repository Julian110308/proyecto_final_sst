from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import (
    EdificioBloque,
    PuntoEncuentro,
    EquipamientoSeguridad,
    RutaEvacuacion,
)
from .serializers import (
    EdificioBloqueSerializer,
    PuntoEncuentroSerializer,
    EquipamientoSeguridadSerializer,
    RutaEvacuacionSerializer,
)
from .services import encontrar_mas_cercano
from usuarios.permissions import NoEsVisitante, EsAdministrativo, excluir_visitantes
# Servicio centralizado de notificaciones
from usuarios.services import NotificacionService

@login_required
@excluir_visitantes
def mapa_interactivo(request):
    """Vista principal del mapa interactivo - TODOS excepto VISITANTE"""
    
    try:
        # 1. EDIFICIOS/BLOQUES

        edificios = EdificioBloque.objects.filter(activo=True).values(
            'id',
            'nombre',
            'tipo',
            'latitud',
            'longitud',
            'descripcion',
            'piso_minimo',
            'piso_maximo',
            'capacidad',
        )

        edificios_data = []
        for edificio in edificios:
            edificios_data.append({
                'id': edificio['id'],
                'nombre': edificio['nombre'],
                'tipo': edificio['tipo'],
                'latitud': float(edificio['latitud']),
                'longitud': float(edificio['longitud']),
                'descripcion': edificio['descripcion'] or f"Edificio {edificio['tipo']}",
                'pisos': f"{edificio['piso_minimo']} - {edificio['piso_maximo']}" if edificio['piso_maximo'] else str(edificio['piso_minimo'] or 1),
                'capacidad': edificio['capacidad'] or 0,
            })

        # 2. PUNTOS DE ENCUENTRO

        puntos_encuentro = PuntoEncuentro.objects.filter(activo=True).values(
            'id', 
            'nombre', 
            'latitud', 
            'longitud', 
            'capacidad', 
            'descripcion',
            'tipo_terreno',  # Agregado
            'prioridad',     # Agregado
        )
        
        # Convertir a lista con formato correcto
        puntos_data = []
        for punto in puntos_encuentro:
            puntos_data.append({
                'id': punto['id'],
                'nombre': punto['nombre'],
                'latitud': float(punto['latitud']),
                'longitud': float(punto['longitud']),
                'capacidad': punto['capacidad'],
                'descripcion': punto['descripcion'] or f"Punto de encuentro {punto['tipo_terreno']} - Prioridad {punto['prioridad']}",
            })

        # 3. EQUIPAMIENTO DE SEGURIDAD

        equipamientos = EquipamientoSeguridad.objects.filter(
            estado='OPERATIVO'
        ).select_related('edificio').values(
            'id',
            'tipo',
            'codigo',
            'latitud',
            'longitud',
            'descripcion',  # Este campo viene del modelo base UbicacionBase
            'ultima_revision',
            'estado',
            'edificio__nombre',  # Relación con edificio
        )
        
        # Convertir a lista con formato correcto
        equipamientos_data = []
        for equipo in equipamientos:
            # Formatear fecha de revisión
            ultima_revision_str = ''
            if equipo['ultima_revision']:
                from django.utils.dateformat import format
                ultima_revision_str = format(equipo['ultima_revision'], 'Y-m-d')
            
            # Crear descripción más detallada
            descripcion_completa = equipo['descripcion'] or ""
            if equipo['edificio__nombre']:
                descripcion_completa += f" | Ubicado en: {equipo['edificio__nombre']}"
            
            equipamientos_data.append({
                'id': equipo['id'],
                'tipo': equipo['tipo'],
                'codigo': equipo['codigo'],
                'latitud': float(equipo['latitud']),
                'longitud': float(equipo['longitud']),
                'ultima_revision': ultima_revision_str,
                'descripcion': descripcion_completa or f"Equipo {equipo['tipo']} - {equipo['codigo']}",
            })
        
        # 4. CREAR DATOS DE EJEMPLO SI NO HAY REALES

        if not edificios_data:
            # Coordenadas reales del Centro Nacional Minero SENA - Sogamoso, Vereda Morcá
            # Base: 5.7303596° N, -72.8943613° O
            edificios_data = [
                {
                    'id': 1,
                    'nombre': 'Edificio Administrativo Principal',
                    'tipo': 'ADMINISTRATIVO',
                    'latitud': 5.73036,
                    'longitud': -72.89436,
                    'descripcion': 'Dirección y administración del Centro Nacional Minero',
                    'pisos': '1 - 2',
                    'capacidad': 100,
                },
                {
                    'id': 2,
                    'nombre': 'Bloque de Aulas Teóricas',
                    'tipo': 'AULAS',
                    'latitud': 5.73070,
                    'longitud': -72.89460,
                    'descripcion': 'Aulas para formación teórica en minería',
                    'pisos': '1 - 2',
                    'capacidad': 300,
                },
                {
                    'id': 3,
                    'nombre': 'Talleres de Minería',
                    'tipo': 'TALLER',
                    'latitud': 5.73000,
                    'longitud': -72.89410,
                    'descripcion': 'Talleres prácticos de maquinaria y equipos mineros',
                    'pisos': '1',
                    'capacidad': 150,
                },
                {
                    'id': 4,
                    'nombre': 'Mina Didáctica Subterránea',
                    'tipo': 'TALLER',
                    'latitud': 5.72970,
                    'longitud': -72.89430,
                    'descripcion': 'Entrada a la mina didáctica para formación práctica',
                    'pisos': '1',
                    'capacidad': 50,
                },
                {
                    'id': 5,
                    'nombre': 'Laboratorios de Geología y Topografía',
                    'tipo': 'LABORATORIO',
                    'latitud': 5.73090,
                    'longitud': -72.89420,
                    'descripcion': 'Laboratorios especializados en ciencias de la tierra',
                    'pisos': '1',
                    'capacidad': 80,
                },
                {
                    'id': 6,
                    'nombre': 'Cafetería y Bienestar',
                    'tipo': 'CAFETERIA',
                    'latitud': 5.73050,
                    'longitud': -72.89480,
                    'descripcion': 'Zona de alimentación y descanso para aprendices',
                    'pisos': '1',
                    'capacidad': 200,
                },
                {
                    'id': 7,
                    'nombre': 'Parqueadero Principal',
                    'tipo': 'PARQUEADERO',
                    'latitud': 5.73120,
                    'longitud': -72.89510,
                    'descripcion': 'Parqueadero de vehículos y motos',
                    'pisos': '1',
                    'capacidad': 100,
                },
            ]

        if not puntos_data:
            puntos_data = [
                {
                    'id': 1,
                    'nombre': 'Punto Principal - Cancha Deportiva',
                    'latitud': 5.73040,
                    'longitud': -72.89430,
                    'capacidad': 500,
                    'descripcion': 'PRIORIDAD 1: Cancha deportiva central - Espacio abierto amplio para evacuación masiva',
                },
                {
                    'id': 2,
                    'nombre': 'Punto Secundario - Parqueadero Norte',
                    'latitud': 5.73130,
                    'longitud': -72.89510,
                    'capacidad': 250,
                    'descripcion': 'PRIORIDAD 2: Zona de parqueadero norte - Área despejada',
                },
                {
                    'id': 3,
                    'nombre': 'Punto Alterno - Entrada Principal',
                    'latitud': 5.73150,
                    'longitud': -72.89460,
                    'capacidad': 200,
                    'descripcion': 'PRIORIDAD 3: Zona de acceso principal - Salida rápida del centro',
                },
                {
                    'id': 4,
                    'nombre': 'Punto de Evacuación Sur',
                    'latitud': 5.72960,
                    'longitud': -72.89410,
                    'capacidad': 150,
                    'descripcion': 'EMERGENCIA: Punto sur para evacuación de talleres',
                }
            ]
        
        if not equipamientos_data:
            equipamientos_data = [
                {
                    'id': 1,
                    'tipo': 'EXTINTOR',
                    'codigo': 'EXT-001',
                    'latitud': 5.73036,
                    'longitud': -72.89436,
                    'ultima_revision': '2026-01-15',
                    'descripcion': 'Extintor PQS - Entrada principal edificio administrativo',
                },
                {
                    'id': 2,
                    'tipo': 'EXTINTOR',
                    'codigo': 'EXT-002',
                    'latitud': 5.72970,
                    'longitud': -72.89430,
                    'ultima_revision': '2026-01-15',
                    'descripcion': 'Extintor CO2 - Entrada mina didáctica',
                },
                {
                    'id': 3,
                    'tipo': 'BOTIQUIN',
                    'codigo': 'BOT-001',
                    'latitud': 5.73070,
                    'longitud': -72.89460,
                    'ultima_revision': '2026-01-20',
                    'descripcion': 'Botiquín tipo A - Bloque de aulas',
                },
                {
                    'id': 4,
                    'tipo': 'BOTIQUIN',
                    'codigo': 'BOT-002',
                    'latitud': 5.73000,
                    'longitud': -72.89410,
                    'ultima_revision': '2026-01-20',
                    'descripcion': 'Botiquín tipo A - Talleres de minería',
                }
            ]
        
        # 5. PREPARAR CONTEXTO

        context = {
            'edificios': edificios_data,
            'puntos_encuentro': puntos_data,
            'equipamiento': equipamientos_data,
            'centro_minero': {
                'lat': 5.7303596,
                'lng': -72.8943613,
                'nombre': 'Centro Nacional Minero SENA - Sogamoso, Vereda Morcá'
            }
        }
        
    except Exception as e:
        # Manejo de errores con datos de ejemplo
        import traceback
        print(f"❌ Error cargando datos del mapa: {e}")
        print(traceback.format_exc())

        context = {
            'edificios': [
                {
                    'id': 1,
                    'nombre': 'Edificio Administrativo Principal',
                    'tipo': 'ADMINISTRATIVO',
                    'latitud': 5.73036,
                    'longitud': -72.89436,
                    'descripcion': 'Dirección y administración del Centro Nacional Minero',
                    'pisos': '1 - 2',
                    'capacidad': 100,
                },
                {
                    'id': 2,
                    'nombre': 'Bloque de Aulas Teóricas',
                    'tipo': 'AULAS',
                    'latitud': 5.73070,
                    'longitud': -72.89460,
                    'descripcion': 'Aulas para formación teórica en minería',
                    'pisos': '1 - 2',
                    'capacidad': 300,
                },
                {
                    'id': 3,
                    'nombre': 'Mina Didáctica Subterránea',
                    'tipo': 'TALLER',
                    'latitud': 5.72970,
                    'longitud': -72.89430,
                    'descripcion': 'Entrada a la mina didáctica para formación práctica',
                    'pisos': '1',
                    'capacidad': 50,
                },
            ],
            'puntos_encuentro': [
                {
                    'id': 1,
                    'nombre': 'Punto Principal - Cancha Deportiva',
                    'latitud': 5.73040,
                    'longitud': -72.89430,
                    'capacidad': 500,
                    'descripcion': 'PRIORIDAD 1: Cancha deportiva central - Espacio abierto amplio para evacuación masiva',
                },
                {
                    'id': 2,
                    'nombre': 'Punto Secundario - Parqueadero Norte',
                    'latitud': 5.73130,
                    'longitud': -72.89510,
                    'capacidad': 250,
                    'descripcion': 'PRIORIDAD 2: Zona de parqueadero norte - Área despejada',
                }
            ],
            'equipamiento': [
                {
                    'id': 1,
                    'tipo': 'EXTINTOR',
                    'codigo': 'EXT-001',
                    'latitud': 5.73036,
                    'longitud': -72.89436,
                    'ultima_revision': '2026-01-15',
                    'descripcion': 'Extintor PQS - Entrada principal edificio administrativo',
                },
                {
                    'id': 2,
                    'tipo': 'BOTIQUIN',
                    'codigo': 'BOT-001',
                    'latitud': 5.73070,
                    'longitud': -72.89460,
                    'ultima_revision': '2026-01-20',
                    'descripcion': 'Botiquín tipo A - Bloque de aulas',
                }
            ],
            'centro_minero': {
                'lat': 5.7303596,
                'lng': -72.8943613,
                'nombre': 'Centro Nacional Minero SENA - Sogamoso, Vereda Morcá'
            }
        }
    
    return render(request, 'mapas.html', context)
class EdificioBloqueViewSet(viewsets.ModelViewSet):
    """
    ViewSet para edificios/bloques
    PERMISOS: Todos excepto VISITANTE pueden ver, solo ADMINISTRATIVO puede modificar
    """
    queryset = EdificioBloque.objects.filter(activo=True)
    serializer_class = EdificioBloqueSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [EsAdministrativo()]
        return [NoEsVisitante()]

class PuntoEncuentroViewSet(viewsets.ModelViewSet):
    """
    ViewSet para puntos de encuentro
    PERMISOS: Todos excepto VISITANTE
    """
    queryset = PuntoEncuentro.objects.filter(activo=True)
    serializer_class = PuntoEncuentroSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [EsAdministrativo()]
        return [NoEsVisitante()]

    @action(detail=True, methods=['get'])
    def mas_cercano(self, request):

        # Encuentra el punto de encuentro más cercano
        latitud = request.query_params.get('lat')
        longitud = request.query_params.get('lon')

        if not latitud or not longitud:
            return Response({'error': 'Parámetros lat y lon son requeridos.'}, status=400)
        
        try:
            lat = float(latitud)
            lon = float(longitud)
        except ValueError:
            return Response({'error': 'Parámetros lat y lon deben ser números válidos.'}, status=400)
        
        punto_cercano, distancia = encontrar_mas_cercano(
            lat, lon, self.get_queryset()
        )

        if punto_cercano:
            serializer = self.get_serializer(punto_cercano)
            return Response({
                'punto': serializer.data,
                'distancia_metros': round(distancia, 2)
            })
        
        return Response({'mensaje': 'No hay puntos de encuentro cercanos.'})
    
class EquipamientoSeguridadViewSet(viewsets.ModelViewSet):
    """
    ViewSet para equipamientos de seguridad
    PERMISOS: Todos excepto VISITANTE
    """
    queryset = EquipamientoSeguridad.objects.all()
    serializer_class = EquipamientoSeguridadSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [EsAdministrativo()]
        return [NoEsVisitante()]

    @action(detail=False, methods=['get'])
    def cercanos(self, request):

        # Encuentra equipamientos cercanos a una ubicación
        latitud = request.query_params.get('lat')
        longitud = request.query_params.get('lon')
        radio_metros = float(request.query_params.get('radio', 500))

        if not latitud or not longitud:
            return Response({'error': 'Latitud y longitud son requeridos.'}, status=400)

        try:
            lat = float(latitud)
            lon = float(longitud)
        except ValueError:
            return Response({'error': 'Latitud y longitud deben ser números válidos.'}, status=400)

        equipos_cercanos = []
        for equipo in self.queryset.filter(estado='OPERATIVO'):
            from .services import calcular_distancia
            distancia = calcular_distancia(lat, lon, equipo.latitud, equipo.longitud)
            if distancia <= radio_metros:
                equipos_cercanos.append({
                    'equipo': EquipamientoSeguridadSerializer(equipo).data,
                    'distancia_metros': round(distancia, 2)
                })

        # Ordenar por distancia
        equipos_cercanos.sort(key=lambda x: x['distancia_metros'])

        return Response(equipos_cercanos)

    @action(detail=True, methods=['post'])
    def verificar(self, request, pk=None):
        """
        Registrar verificación de un equipo específico
        PERMISOS: BRIGADA y ADMINISTRATIVO
        """
        from django.utils import timezone
        from datetime import timedelta

        # Verificar permisos
        if request.user.rol not in ['BRIGADA', 'ADMINISTRATIVO']:
            return Response({
                'success': False,
                'error': 'No tiene permisos para verificar equipos'
            }, status=403)

        try:
            equipo = self.get_object()
            ahora = timezone.now()

            # Actualizar fechas de revisión
            equipo.ultima_revision = ahora
            # Programar próxima revisión según el tipo de equipo
            if equipo.tipo in ['EXTINTOR', 'HIDRANTE']:
                equipo.proxima_revision = ahora + timedelta(days=180)  # 6 meses
            elif equipo.tipo in ['BOTIQUIN', 'DEA']:
                equipo.proxima_revision = ahora + timedelta(days=90)   # 3 meses
            else:
                equipo.proxima_revision = ahora + timedelta(days=365)  # 1 año

            equipo.save()

            return Response({
                'success': True,
                'message': f'Equipo {equipo.codigo} verificado correctamente',
                'ultima_revision': equipo.ultima_revision.strftime('%d/%m/%Y'),
                'proxima_revision': equipo.proxima_revision.strftime('%d/%m/%Y')
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)

    @action(detail=True, methods=['post'])
    def cambiar_estado(self, request, pk=None):
        """
        Cambiar el estado de un equipo
        PERMISOS: BRIGADA y ADMINISTRATIVO
        """
        # Verificar permisos
        if request.user.rol not in ['BRIGADA', 'ADMINISTRATIVO']:
            return Response({
                'success': False,
                'error': 'No tiene permisos para cambiar el estado de equipos'
            }, status=403)

        try:
            equipo = self.get_object()
            nuevo_estado = request.data.get('estado')
            observaciones = request.data.get('observaciones', '')

            if nuevo_estado not in ['OPERATIVO', 'MANTENIMIENTO', 'FUERA_SERVICIO']:
                return Response({
                    'success': False,
                    'error': 'Estado no válido'
                }, status=400)

            equipo.estado = nuevo_estado
            # Guardar observaciones en descripción si las hay
            if observaciones:
                equipo.descripcion = f"{equipo.descripcion or ''}\n[{request.user.get_full_name()}]: {observaciones}".strip()
            equipo.save()

            # Notificar a la brigada si el equipo necesita atención
            if nuevo_estado in ['MANTENIMIENTO', 'FUERA_SERVICIO']:
                NotificacionService.notificar_equipo_requiere_revision(equipo)

            return Response({
                'success': True,
                'message': f'Estado del equipo {equipo.codigo} actualizado a {nuevo_estado}',
                'nuevo_estado': nuevo_estado
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)

    @action(detail=False, methods=['post'])
    def verificacion_general(self, request):
        """
        Realizar verificación general de todos los equipos operativos
        PERMISOS: BRIGADA y ADMINISTRATIVO
        """
        from django.utils import timezone
        from datetime import timedelta

        # Verificar permisos
        if request.user.rol not in ['BRIGADA', 'ADMINISTRATIVO']:
            return Response({
                'success': False,
                'error': 'No tiene permisos para realizar verificación general'
            }, status=403)

        try:
            ahora = timezone.now()
            equipos_operativos = EquipamientoSeguridad.objects.filter(estado='OPERATIVO')
            contador = 0

            for equipo in equipos_operativos:
                equipo.ultima_revision = ahora
                # Programar próxima revisión según el tipo
                if equipo.tipo in ['EXTINTOR', 'HIDRANTE']:
                    equipo.proxima_revision = ahora + timedelta(days=180)
                elif equipo.tipo in ['BOTIQUIN', 'DEA']:
                    equipo.proxima_revision = ahora + timedelta(days=90)
                else:
                    equipo.proxima_revision = ahora + timedelta(days=365)
                equipo.save()
                contador += 1

            return Response({
                'success': True,
                'message': f'Verificación general completada',
                'equipos_verificados': contador,
                'fecha_verificacion': ahora.strftime('%d/%m/%Y %H:%M')
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)
    
class RutaEvacuacionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para rutas de evacuación
    PERMISOS: Todos excepto VISITANTE
    """
    queryset = RutaEvacuacion.objects.filter(activa=True)
    serializer_class = RutaEvacuacionSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [EsAdministrativo()]
        return [NoEsVisitante()]
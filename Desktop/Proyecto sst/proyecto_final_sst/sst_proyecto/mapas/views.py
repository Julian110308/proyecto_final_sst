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
from usuarios.permissions import NoEsVisitante, EsAdministrativo

@login_required
def mapa_interactivo(request):
    """Vista principal del mapa interactivo"""
    
    try:
        # 1. PUNTOS DE ENCUENTRO

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
        
        # 2. EQUIPAMIENTO DE SEGURIDAD

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
        
        # 3. CREAR DATOS DE EJEMPLO SI NO HAY REALES

        if not puntos_data:
            puntos_data = [
                {
                    'id': 1,
                    'nombre': 'Cancha Principal',
                    'latitud': 5.5342,
                    'longitud': -73.3670,
                    'capacidad': 200,
                    'descripcion': 'Área abierta principal para evacuación - Prioridad 1',
                },
                {
                    'id': 2,
                    'nombre': 'Parqueadero Trasero',
                    'latitud': 5.5336,
                    'longitud': -73.3678,
                    'capacidad': 150,
                    'descripcion': 'Zona segura trasera del edificio - Prioridad 2',
                }
            ]
        
        if not equipamientos_data:
            equipamientos_data = [
                {
                    'id': 1,
                    'tipo': 'EXTINTOR',
                    'codigo': 'EXT-001',
                    'latitud': 5.5339,
                    'longitud': -73.3674,
                    'ultima_revision': '2024-12-01',
                    'descripcion': 'Extintor CO2 en entrada principal',
                },
                {
                    'id': 2,
                    'tipo': 'BOTIQUIN',
                    'codigo': 'BOT-001',
                    'latitud': 5.5341,
                    'longitud': -73.3676,
                    'ultima_revision': '2024-11-15',
                    'descripcion': 'Botiquín de primeros auxilios completo',
                }
            ]
        
        # 4. PREPARAR CONTEXTO

        context = {
            'puntos_encuentro': puntos_data,
            'equipamiento': equipamientos_data,
            'centro_minero': {
                'lat': 5.5339,
                'lng': -73.3674,
                'nombre': 'Centro Minero SENA Sogamoso'
            }
        }
        
    except Exception as e:
        # Manejo de errores con datos de ejemplo
        import traceback
        print(f"❌ Error cargando datos del mapa: {e}")
        print(traceback.format_exc())
        
        context = {
            'puntos_encuentro': [
                {
                    'id': 1,
                    'nombre': 'Cancha Principal',
                    'latitud': 5.5342,
                    'longitud': -73.3670,
                    'capacidad': 200,
                    'descripcion': 'Área abierta principal para evacuación - Prioridad 1',
                },
                {
                    'id': 2,
                    'nombre': 'Parqueadero Trasero',
                    'latitud': 5.5336,
                    'longitud': -73.3678,
                    'capacidad': 150,
                    'descripcion': 'Zona segura trasera del edificio - Prioridad 2',
                }
            ],
            'equipamiento': [
                {
                    'id': 1,
                    'tipo': 'EXTINTOR',
                    'codigo': 'EXT-001',
                    'latitud': 5.5339,
                    'longitud': -73.3674,
                    'ultima_revision': '2024-12-01',
                    'descripcion': 'Extintor CO2 en entrada principal',
                },
                {
                    'id': 2,
                    'tipo': 'BOTIQUIN',
                    'codigo': 'BOT-001',
                    'latitud': 5.5341,
                    'longitud': -73.3676,
                    'ultima_revision': '2024-11-15',
                    'descripcion': 'Botiquín de primeros auxilios completo',
                }
            ],
            'centro_minero': {
                'lat': 5.5339,
                'lng': -73.3674,
                'nombre': 'Centro Minero SENA Sogamoso'
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
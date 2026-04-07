"""
Servicio de cálculo de rutas peatonales para evacuación.
Usa el grafo NodoCamino/TramoCamino y el algoritmo de Dijkstra (NetworkX).
"""

import math
import logging

import networkx as nx

logger = logging.getLogger(__name__)

# Velocidad promedio peatonal en emergencia: 5 km/h = 83.3 m/min
VELOCIDAD_METROS_POR_MINUTO = 83.3


def haversine(lat1, lng1, lat2, lng2):
    """Distancia en metros entre dos puntos GPS usando la fórmula de Haversine."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def construir_grafo():
    """
    Lee NodoCamino y TramoCamino de la BD y construye un grafo NetworkX.
    Retorna (grafo, dict_nodos) donde dict_nodos = {id: {lat, lng, nombre, tipo}}
    """
    from .models import NodoCamino, TramoCamino

    G = nx.Graph()

    nodos = NodoCamino.objects.filter(activo=True)
    nodos_data = {}
    for nodo in nodos:
        G.add_node(nodo.id, lat=nodo.latitud, lng=nodo.longitud, nombre=nodo.nombre, tipo=nodo.tipo)
        nodos_data[nodo.id] = {"lat": nodo.latitud, "lng": nodo.longitud, "nombre": nodo.nombre, "tipo": nodo.tipo}

    tramos = TramoCamino.objects.filter(activo=True).select_related("nodo_origen", "nodo_destino")
    for tramo in tramos:
        G.add_edge(
            tramo.nodo_origen_id,
            tramo.nodo_destino_id,
            weight=tramo.distancia_metros,
            tipo=tramo.tipo,
        )

    return G, nodos_data


def nodo_mas_cercano(G, lat, lng, max_distancia_m=500):
    """
    Devuelve el id del nodo más cercano a (lat, lng) y su distancia.
    Retorna (None, inf) si el grafo está vacío o no hay nodo dentro de max_distancia_m.
    """
    min_dist = float("inf")
    closest_id = None

    for node_id, data in G.nodes(data=True):
        d = haversine(lat, lng, data["lat"], data["lng"])
        if d < min_dist:
            min_dist = d
            closest_id = node_id

    if min_dist > max_distancia_m:
        return None, min_dist

    return closest_id, min_dist


def calcular_ruta(lat_usuario, lng_usuario, punto_encuentro_id):
    """
    Calcula la ruta peatonal más corta desde la posición del usuario
    hasta el punto de encuentro indicado.

    Retorna un dict con:
        - waypoints: [[lat, lng], ...] incluyendo inicio y fin
        - distancia_metros: float
        - tiempo_minutos: float
        - encontrado: bool (False si no hay grafo o no hay camino)
        - mensaje: str descriptivo
    """
    from .models import PuntoEncuentro

    resultado_vacio = {
        "waypoints": [],
        "distancia_metros": 0,
        "tiempo_minutos": 0,
        "encontrado": False,
        "mensaje": "",
    }

    try:
        punto = PuntoEncuentro.objects.get(id=punto_encuentro_id, activo=True)
    except PuntoEncuentro.DoesNotExist:
        resultado_vacio["mensaje"] = "Punto de encuentro no encontrado."
        return resultado_vacio

    G, _ = construir_grafo()

    if G.number_of_nodes() == 0:
        # Sin grafo definido: devuelve línea directa como fallback
        resultado_vacio["encontrado"] = False
        resultado_vacio["mensaje"] = "No hay caminos definidos. Muestra ruta directa."
        resultado_vacio["waypoints"] = [
            [lat_usuario, lng_usuario],
            [punto.latitud, punto.longitud],
        ]
        dist = haversine(lat_usuario, lng_usuario, punto.latitud, punto.longitud)
        resultado_vacio["distancia_metros"] = round(dist, 1)
        resultado_vacio["tiempo_minutos"] = round(dist / VELOCIDAD_METROS_POR_MINUTO, 1)
        return resultado_vacio

    # Nodo más cercano al usuario
    nodo_inicio_id, dist_al_inicio = nodo_mas_cercano(G, lat_usuario, lng_usuario)
    if nodo_inicio_id is None:
        resultado_vacio["mensaje"] = "No hay nodos de camino cercanos a tu ubicación."
        resultado_vacio["waypoints"] = [[lat_usuario, lng_usuario], [punto.latitud, punto.longitud]]
        return resultado_vacio

    # Nodo más cercano al punto de encuentro
    nodo_fin_id, dist_al_fin = nodo_mas_cercano(G, punto.latitud, punto.longitud)
    if nodo_fin_id is None:
        resultado_vacio["mensaje"] = "No hay nodos de camino cercanos al punto de encuentro."
        resultado_vacio["waypoints"] = [[lat_usuario, lng_usuario], [punto.latitud, punto.longitud]]
        return resultado_vacio

    # Dijkstra
    try:
        path_ids = nx.dijkstra_path(G, nodo_inicio_id, nodo_fin_id, weight="weight")
        distancia_grafo = nx.dijkstra_path_length(G, nodo_inicio_id, nodo_fin_id, weight="weight")
    except nx.NetworkXNoPath:
        resultado_vacio["mensaje"] = "No existe camino entre los puntos. Revisa que el grafo esté conectado."
        resultado_vacio["waypoints"] = [[lat_usuario, lng_usuario], [punto.latitud, punto.longitud]]
        return resultado_vacio
    except nx.NodeNotFound:
        resultado_vacio["mensaje"] = "Error en el grafo de caminos."
        return resultado_vacio

    # Construir lista de waypoints completa:
    # posición real del usuario → nodos del grafo → posición real del punto de encuentro
    waypoints = [[lat_usuario, lng_usuario]]
    for node_id in path_ids:
        data = G.nodes[node_id]
        waypoints.append([data["lat"], data["lng"]])
    waypoints.append([punto.latitud, punto.longitud])

    # Distancia total = tramo usuario→nodo_inicio + grafo + nodo_fin→punto
    distancia_total = dist_al_inicio + distancia_grafo + dist_al_fin

    return {
        "waypoints": waypoints,
        "distancia_metros": round(distancia_total, 1),
        "tiempo_minutos": round(distancia_total / VELOCIDAD_METROS_POR_MINUTO, 1),
        "encontrado": True,
        "mensaje": f"Ruta hacia {punto.nombre} ({round(distancia_total)}m · ~{round(distancia_total / VELOCIDAD_METROS_POR_MINUTO, 1)} min)",
        "punto_encuentro": {
            "id": punto.id,
            "nombre": punto.nombre,
            "lat": punto.latitud,
            "lng": punto.longitud,
        },
    }


def calcular_ruta_mas_corta(lat_usuario, lng_usuario):
    """
    Entre todos los puntos de encuentro activos, calcula la ruta más corta.
    Retorna el mismo dict que calcular_ruta() para el punto de encuentro óptimo.
    """
    from .models import PuntoEncuentro

    puntos = PuntoEncuentro.objects.filter(activo=True).order_by("prioridad")
    if not puntos.exists():
        return {"encontrado": False, "mensaje": "No hay puntos de encuentro activos.", "waypoints": []}

    mejor = None
    for punto in puntos:
        resultado = calcular_ruta(lat_usuario, lng_usuario, punto.id)
        if resultado["distancia_metros"] > 0:
            if mejor is None or resultado["distancia_metros"] < mejor["distancia_metros"]:
                mejor = resultado

    return mejor or {"encontrado": False, "mensaje": "No se pudo calcular ninguna ruta.", "waypoints": []}


def grafo_como_json():
    """
    Exporta el grafo completo en formato GeoJSON-compatible para el editor visual.
    """
    from .models import NodoCamino, TramoCamino

    nodos = list(
        NodoCamino.objects.filter(activo=True).values(
            "id",
            "nombre",
            "latitud",
            "longitud",
            "tipo",
            "edificio_id",
            "punto_encuentro_id",
        )
    )

    tramos = list(
        TramoCamino.objects.filter(activo=True)
        .select_related("nodo_origen", "nodo_destino")
        .values(
            "id",
            "nodo_origen_id",
            "nodo_origen__latitud",
            "nodo_origen__longitud",
            "nodo_destino_id",
            "nodo_destino__latitud",
            "nodo_destino__longitud",
            "tipo",
            "distancia_metros",
            "bidireccional",
        )
    )

    return {"nodos": nodos, "tramos": tramos}

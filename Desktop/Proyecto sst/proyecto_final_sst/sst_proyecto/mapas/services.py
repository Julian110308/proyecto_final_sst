import math

def calcular_distancia(lat1,lon1,lat2,lon2):

    """
    Calcula la distancia entre dos puntos geográficos usando la fórmula de Haversine
    Retorna la distancia en metros
    """

    # Radio de la Tierra en metros
    R = 6371000

    # Convertir grados a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Diferencias de coordenadas
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Formula de Haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distancia = R * c

    return distancia

def encontrar_mas_cercano(lat_usuario, lon_usuario, objetos, radio_maximo=1000):

    """
    Encuentra el objeto más cercano a la ubicación del usuario
    radio_maximo: distancia máxima en metros
    """

    objeto_cercano = None
    distancia_minima = float('inf')

    for obj in objetos:
        if hasattr(obj, 'latitud') and hasattr(obj, 'longitud'):
            distancia = calcular_distancia(
                lat_usuario, lon_usuario,
                obj.latitud, obj.longitud
            )

            if distancia < distancia_minima and distancia <= radio_maximo:
                distancia_minima = distancia
                objeto_cercano = obj
    
    return objeto_cercano, distancia_minima
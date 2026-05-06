# repartidores/utils.py


import requests
import os
from django.conf import settings
import logging

# Configurar logging para depuración
logger = logging.getLogger(__name__)

def get_geocoding_from_address(calle, numero, comuna, ciudad):
    """
    Obtiene la latitud y longitud de una dirección usando la API de Google Maps.
    Si la geocodificación falla, intenta con una dirección aproximada (solo comuna y ciudad).
    """
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY') or settings.GOOGLE_MAPS_API_KEY

    if not api_key:
        logger.error("No se encontró la clave de API de Google Maps.")
        return None, None

    # Formatear la dirección completa, incluyendo país y región para mayor precisión
    address = f"{calle} {numero}, {comuna}, {ciudad}, Región de la Araucanía, Chile".strip()
    if not calle or not numero:  # Para el intento aproximado
        address = f"{comuna}, {ciudad}, Región de la Araucanía, Chile".strip()

    # Incluir region=cl para priorizar resultados en Chile
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={requests.utils.quote(address)}&region=cl&key={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "OK":
            location = data["results"][0]["geometry"]["location"]
            logger.info(f"Geocodificación exitosa para {address}: ({location['lat']}, {location['lng']})")
            return location["lat"], location["lng"]
        else:
            logger.warning(f"Geocodificación falló para {address}. Estado: {data.get('status')}")
            # Si la dirección completa falla y es un intento con calle/numero, probar con comuna/ciudad
            if calle and numero:
                logger.info(f"Intentando geocodificación aproximada para {comuna}, {ciudad}")
                return get_geocoding_from_address("", "", comuna, ciudad)
            return None, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en la solicitud de geocodificación para {address}: {str(e)}")
        return None, None
    except (KeyError, IndexError) as e:
        logger.error(f"Error al analizar la respuesta de la API para {address}: {str(e)}")
        return None, None
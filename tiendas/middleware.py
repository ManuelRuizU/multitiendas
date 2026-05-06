# tiendas/middleware.py

from django.http import Http404, HttpResponseRedirect
from django.conf import settings
from .models import Tienda

class TiendaSubdominioMiddleware:
    """
    Middleware para identificar la tienda basándose en el subdominio.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Obtiene el nombre del host (ej. 'mipizza.multitienda.com')
        host = request.get_host().lower()

        # Determina el dominio principal (ajusta según tu configuración de producción)
        # En desarrollo, el dominio principal puede ser 'localhost:8000'
        main_domain = settings.MAIN_DOMAIN

        # Si el host no es el dominio principal, intenta encontrar una tienda.
        if host != main_domain:
            # Separar el subdominio del resto del host
            try:
                subdomain = host.split('.')[0]
                # Buscar la tienda por su campo 'slug'
                # Asume que tu modelo Tienda tiene un campo 'slug' único
                # que coincide con el subdominio.
                tienda = Tienda.objects.get(slug=subdomain)
                
                # Si se encuentra, adjunta el objeto 'tienda' a la solicitud.
                request.tienda = tienda
            
            except (IndexError, Tienda.DoesNotExist):
                # Si el subdominio no es válido o la tienda no existe,
                # redirige a la página principal.
                return HttpResponseRedirect(f"http://{main_domain}")
        else:
            # Si el host es el dominio principal, no hay tienda específica.
            request.tienda = None

        response = self.get_response(request)
        return response


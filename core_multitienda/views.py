# core_multitienda/views.py

# core_multitienda/views.py

from django.shortcuts import render, get_object_or_404, Http404
from tiendas.models import Tienda
from productos.models import Producto # ¡Asegúrate de que este import esté presente!

def tienda_home_view(request, slug):
    try:
        tienda = get_object_or_404(Tienda, slug=slug)
        
        # Esta es la parte crucial. Aquí obtenemos todos los productos
        # que pertenecen a la tienda actual y que están disponibles.
        productos = Producto.objects.filter(tienda=tienda, disponible=True)
        
        # Pasamos la lista de productos (llamada 'productos') a la plantilla.
        context = {
            'tienda': tienda,
            'productos': productos,
        }
        
        # Renderizamos la plantilla con el contexto
        return render(request, 'tiendas/tienda_home.html', context)

    except Http404:
        raise Http404("Tienda no encontrada. Por favor, verifique la URL.")
# carritos/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CarritoViewSet, ItemCarritoViewSet

router = DefaultRouter()
router.register(r'items', ItemCarritoViewSet, basename='item-carrito')

urlpatterns = [
    # Endpoint para obtener/crear el carrito del usuario o invitado
    path('mi_carrito/', CarritoViewSet.as_view({'get': 'mi_carrito', 'post': 'mi_carrito'}), name='mi-carrito'),
    # Endpoint para fusionar carritos (cuando un invitado inicia sesión)
    path('fusionar_carrito/', CarritoViewSet.as_view({'post': 'fusionar_carrito'}), name='fusionar-carrito'),
    # Endpoints para gestionar ítems dentro de un carrito (add, update, delete)
    path('', include(router.urls)),
]
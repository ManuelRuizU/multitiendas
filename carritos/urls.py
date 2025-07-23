# carritos/urls.py (¡Vuelve a esta versión!)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers # Asegúrate de importar esto

from .views import CarritoViewSet, ItemCarritoViewSet

# 1. Router principal para el CarritoViewSet
router = DefaultRouter()
router.register(r'carritos', CarritoViewSet, basename='carrito')

# 2. Router anidado para el ItemCarritoViewSet
carritos_router = routers.NestedSimpleRouter(router, r'carritos', lookup='carrito')
carritos_router.register(r'items', ItemCarritoViewSet, basename='carrito-item')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(carritos_router.urls)),
    path('fusionar_carrito/', CarritoViewSet.as_view({'post': 'fusionar_carrito'}), name='fusionar-carrito'),
]




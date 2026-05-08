# carritos/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import CarritoViewSet, GrupoCarritoViewSet, ItemCarritoViewSet

# Router principal — Carrito
router = DefaultRouter()
router.register(r'carritos', CarritoViewSet, basename='carrito')

# Router anidado — GrupoCarrito dentro de Carrito
grupos_router = routers.NestedSimpleRouter(router, r'carritos', lookup='carrito')
grupos_router.register(r'grupos', GrupoCarritoViewSet, basename='carrito-grupo')

# Router anidado — ItemCarrito dentro de GrupoCarrito
items_router = routers.NestedSimpleRouter(grupos_router, r'grupos', lookup='grupo')
items_router.register(r'items', ItemCarritoViewSet, basename='carrito-grupo-item')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(grupos_router.urls)),
    path('', include(items_router.urls)),
    path(
        'fusionar_carrito/',
        CarritoViewSet.as_view({'post': 'fusionar_carrito'}),
        name='fusionar-carrito'
    ),
]


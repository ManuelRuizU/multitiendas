# pedidos/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, OrderItemViewSet

router = DefaultRouter()
router.register(r'pedidos', OrderViewSet, basename='pedido')
router.register(r'items-pedido', OrderItemViewSet, basename='item-pedido')

urlpatterns = [
    path('', include(router.urls)),
]
# usuarios/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, PerfilVendedorViewSet, ClienteViewSet, DireccionViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'perfiles-vendedor', PerfilVendedorViewSet)
router.register(r'clientes', ClienteViewSet)
router.register(r'direcciones', DireccionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
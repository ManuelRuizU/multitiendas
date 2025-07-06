# tiendas/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TiendaViewSet, RadioEnvioViewSet

router = DefaultRouter()
router.register(r'tiendas', TiendaViewSet)
router.register(r'radios-envio', RadioEnvioViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
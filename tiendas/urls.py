# tiendas/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TiendaViewSet, RadioEnvioViewSet, CuadranteEnvioViewSet

router = DefaultRouter()

# Agregamos 'basename' para que el router sepa cómo nombrar las rutas dinámicas
router.register(r'tiendas', TiendaViewSet, basename='tienda')
router.register(r'radios-envio', RadioEnvioViewSet, basename='radio-envio')
router.register(r'cuadrantes-envio', CuadranteEnvioViewSet, basename='cuadrante-envio')

urlpatterns = [
    path('', include(router.urls)),
]



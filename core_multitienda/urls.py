# core_multitienda/urls.py
# modificado 19/8/2025
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import TokenRefreshView
from usuarios.views import MyTokenObtainPairView

from .views import tienda_home_view

urlpatterns = [
    # MOVIDO: Las URLs de API y de administración deben estar al principio
    # para evitar conflictos con la ruta de tienda.
    path('admin/', admin.site.urls),

    # URLs para tus APIs REST
    path('api/usuarios/', include('usuarios.urls')),
    path('api/', include('tiendas.urls')),
    path('api/', include('productos.urls')),
    path('api/', include('carritos.urls')),
    path('api/', include('pedidos.urls')),
    path('api/', include('plataforma_config.urls')),
    path('api/', include('repartidores.urls')),

    # URLs para tokens JWT (ruta canónica; MyTokenObtainPairView añade datos del usuario en la respuesta)
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # URLs para el login/logout del DRF browsable API (opcional, pero útil)
    path('api-auth/', include('rest_framework.urls')),

    # DEJAR ESTA AL FINAL: Este es el patrón general para las tiendas.
    # Se evalúa solo si las rutas anteriores no coinciden.
    re_path(r'^(?P<slug>[\w-]+)/$', tienda_home_view, name='tienda_home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
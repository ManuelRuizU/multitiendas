# core_multitienda/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Importa las vistas de token de simple_jwt AQUI, en urls.py
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # URLs para tus APIs REST
    path('api/usuarios/', include('usuarios.urls')),
    path('api/tiendas/', include('tiendas.urls')),
    path('api/productos/', include('productos.urls')),
    path('api/pedidos/', include('pedidos.urls')),
    path('api/plataforma/', include('plataforma_config.urls')),
    path('api/carritos/', include('carritos.urls')),

    # --- ¡ESTAS LÍNEAS PARA JWT DEBEN ESTAR AQUÍ EN urls.py! ---
    # Estas son las URLs para obtener y refrescar tokens JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # ---------------------------------------------------------

    # URLs para el login/logout del DRF browsable API (opcional, pero útil)
    path('api-auth/', include('rest_framework.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    
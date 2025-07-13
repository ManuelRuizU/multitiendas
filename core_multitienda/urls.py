
# core_multitienda/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # URLs para tus APIs REST
    path('api/usuarios/', include('usuarios.urls')),
    path('api/tiendas/', include('tiendas.urls')),
    path('api/productos/', include('productos.urls')),
    path('api/pedidos/', include('pedidos.urls')),
    path('api/plataforma/', include('plataforma_config.urls')),
    path('api/carritos/', include('carritos.urls')),

    # --- ¡AÑADE ESTAS LÍNEAS PARA DJOSER! ---
    #path('api/auth/', include('djoser.urls')), # URLs generales de Djoser (registro, gestión de usuarios)
    #path('api/auth/', include('djoser.urls.authtoken')), # URLs para autenticación con Token (login, logout)
    # ----------------------------------------

    # URLs para el login/logout del DRF browsable API (opcional, pero útil)
    path('api-auth/', include('rest_framework.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
"""
URL configuration for core_multitienda project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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
    path('api/plataforma/', include('plataforma_config.urls')), # La nueva API de configuración

    # URLs para el login/logout del DRF browsable API (muy útil para testing)
    path('api-auth/', include('rest_framework.urls')),
]

# Solo sirve archivos de medios en modo de desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

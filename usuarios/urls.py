# usuarios/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Eliminamos CustomAuthToken de aquí ya que fue eliminada de views.py
# También eliminamos csrf_exempt, ya que no es necesario para DRF con JWT
from .views import UserViewSet, PerfilVendedorViewSet, ClienteViewSet, DireccionViewSet, RegisterUserView

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'perfiles-vendedor', PerfilVendedorViewSet)
router.register(r'clientes', ClienteViewSet)
router.register(r'direcciones', DireccionViewSet)

urlpatterns = [
    # Esto incluye todas las URLs generadas por el router (para ViewSets)
    path('', include(router.urls)),
    
    # URL para la vista de registro. Ya no necesita csrf_exempt.
    # El CSRF está desactivado globalmente para la API o manejado por DRF.
    path('register/', RegisterUserView.as_view(), name='user-register'), 
    
    # ¡MUY IMPORTANTE! Esta línea debe ELIMINARSE.
    # La obtención de tokens JWT ahora se maneja en el urls.py principal (core_multitienda/urls.py)
    # a través de las vistas de rest_framework_simplejwt.
    # path('auth/token/', CustomAuthToken.as_view(), name='obtain-token'),
]
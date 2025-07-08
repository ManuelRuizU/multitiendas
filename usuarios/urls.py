# usuarios/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Asegúrate de importar tu nueva vista de registro aquí
from .views import CustomAuthToken, UserViewSet, PerfilVendedorViewSet, ClienteViewSet, DireccionViewSet, RegisterUserView
from django.views.decorators.csrf import csrf_exempt # <-- ¡Añade esta importación!

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'perfiles-vendedor', PerfilVendedorViewSet)
router.register(r'clientes', ClienteViewSet)
router.register(r'direcciones', DireccionViewSet)

urlpatterns = [
    # Esto incluye todas las URLs generadas por el router (para ViewSets)
    path('', include(router.urls)),
    
    # AÑADE ESTA LÍNEA ESPECÍFICA PARA LA VISTA DE REGISTRO
    # Esto creará la URL http://127.0.0.1:8000/api/usuarios/register/
    path('register/', csrf_exempt(RegisterUserView.as_view()), name='user-register'), # <-- ¡CAMBIO AQUÍ!
    
    # Para la vista de obtención de token, generalmente no necesita csrf_exempt si usas TokenAuthentication,
    # pero si te da problemas, podrías aplicarlo también. Por ahora, lo dejamos sin.
    path('auth/token/', CustomAuthToken.as_view(), name='obtain-token'),
]
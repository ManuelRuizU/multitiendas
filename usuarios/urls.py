# usuarios/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Asegúrate de importar tu nueva vista de registro aquí
from .views import UserViewSet, PerfilVendedorViewSet, ClienteViewSet, DireccionViewSet, RegisterUserView 

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
    path('register/', RegisterUserView.as_view(), name='user-register'),
]
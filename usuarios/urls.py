# usuarios/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    BuyerProfileViewSet,
    SellerProfileViewSet,
    ClienteViewSet,
    DireccionViewSet,
    ClienteRegistrationView,
    SellerRegistrationView,
    RepartidorRegistrationView,
    ChangePasswordView,
    AgregarRolVendedorView,
    AgregarRolRepartidorView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'buyer-profiles', BuyerProfileViewSet, basename='buyer-profile')
router.register(r'seller-profiles', SellerProfileViewSet, basename='seller-profile')
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'direcciones', DireccionViewSet, basename='direccion')

urlpatterns = [
    path('', include(router.urls)),

    # --- Registro por rol ---
    path('register/cliente/', ClienteRegistrationView.as_view(), name='register-cliente'),
    path('register/vendedor/', SellerRegistrationView.as_view(), name='register-vendedor'),
    path('register/repartidor/', RepartidorRegistrationView.as_view(), name='register-repartidor'),

    # --- Cuenta ---
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # --- Agregar roles a usuario existente ---
    path('agregar-rol-vendedor/', AgregarRolVendedorView.as_view(), name='agregar-rol-vendedor'),
    path('agregar-rol-repartidor/', AgregarRolRepartidorView.as_view(), name='agregar-rol-repartidor'),
]








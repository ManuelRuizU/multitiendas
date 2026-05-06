# usuarios/urls.py
# version final 10/8/2025

from django.urls import path, include
from rest_framework.routers import DefaultRouter
# Asegúrate de que estas importaciones coincidan con las clases en usuarios/views.py
from .views import (
    MyTokenObtainPairView, 
    UserViewSet, 
    BuyerProfileViewSet, 
    SellerProfileViewSet, 
    ClienteViewSet, 
    DireccionViewSet, 
    SellerRegistrationView, 
    ChangePasswordView 
)

# Crea un enrutador para tus ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet) 
router.register(r'buyer-profiles', BuyerProfileViewSet, basename='buyer-profile')
router.register(r'seller-profiles', SellerProfileViewSet, basename='seller-profile')
router.register(r'clientes', ClienteViewSet, basename='cliente') 
router.register(r'direcciones', DireccionViewSet, basename='direccion') 

urlpatterns = [
    path('', include(router.urls)),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register-seller/', SellerRegistrationView.as_view(), name='register-seller'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]









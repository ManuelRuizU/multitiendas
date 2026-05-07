# usuarios/views.py
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.serializers import ValidationError
from django.db import transaction
from django.contrib.auth import get_user_model 
import uuid 

from rest_framework.views import APIView 

# Importaciones corregidas: Se elimina UserType
from .models import BuyerProfile, SellerProfile, Cliente, Direccion
from .serializers import (
    UserSerializer, 
    UserRegistrationSerializer, 
    SellerRegistrationSerializer, 
    BuyerProfileSerializer,
    SellerProfileSerializer,
    ClienteSerializer, 
    DireccionSerializer,
    ChangePasswordSerializer
)

from rest_framework_simplejwt.views import TokenObtainPairView

CustomUser = get_user_model() 

# 1. OBTENER TOKEN JWT
class MyTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            user = CustomUser.objects.get(username=request.data['username']) 
            user_data = UserSerializer(user).data 
            response.data['user'] = user_data
        return response

# 2. USER VIEWSET
class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer 
        return UserSerializer 

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()] 
        return [IsAuthenticated()] 

# 3. REGISTRO DE VENDEDOR
class SellerRegistrationView(generics.CreateAPIView):
    serializer_class = SellerRegistrationSerializer
    permission_classes = [AllowAny] 

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save() 
        user.refresh_from_db() 
        return Response(
            {"message": "Vendedor registrado exitosamente.", "user_id": user.id}, 
            status=status.HTTP_201_CREATED
        )

# 4. BUYER PROFILE VIEWSET
class BuyerProfileViewSet(viewsets.ModelViewSet):
    queryset = BuyerProfile.objects.all()
    serializer_class = BuyerProfileSerializer
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        if self.request.user.is_staff: 
            return BuyerProfile.objects.all()
        # Ajustado al nuevo related_name: perfil_cliente (o buyer_profile según tu serializer)
        if hasattr(self.request.user, 'buyer_profile'):
            return BuyerProfile.objects.filter(user=self.request.user)
        return BuyerProfile.objects.none()

    @action(detail=False, methods=['get'])
    def mi_perfil(self, request):
        perfil = getattr(request.user, 'buyer_profile', None)
        if perfil:
            serializer = self.get_serializer(perfil)
            return Response(serializer.data)
        return Response({"detail": "Perfil no encontrado."}, status=404)

# 5. SELLER PROFILE VIEWSET
class SellerProfileViewSet(viewsets.ModelViewSet):
    queryset = SellerProfile.objects.all()
    serializer_class = SellerProfileSerializer
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        if self.request.user.is_staff: 
            return SellerProfile.objects.all()
        if hasattr(self.request.user, 'seller_profile'):
            return SellerProfile.objects.filter(user=self.request.user)
        return SellerProfile.objects.none()

# 6. CLIENTE VIEWSET (Maneja Invitados y Registrados)
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        if self.request.user.is_staff: 
            return Cliente.objects.all()
        if hasattr(self.request.user, 'cliente_data'):
            return Cliente.objects.filter(user=self.request.user)
        return Cliente.objects.none()

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_or_create_guest_client(self, request):
        guest_uuid_str = request.data.get('guest_uuid')
        if guest_uuid_str:
            cliente = Cliente.objects.filter(guest_uuid=guest_uuid_str, user__isnull=True).first()
            if cliente:
                return Response(self.get_serializer(cliente).data)
        
        # Crear nuevo invitado si no existe o no se envió UUID
        data = request.data.copy()
        if not guest_uuid_str:
            data['guest_uuid'] = uuid.uuid4()
        data['is_guest'] = True
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=None)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# 7. DIRECCIÓN VIEWSET
class DireccionViewSet(viewsets.ModelViewSet):
    queryset = Direccion.objects.all()
    serializer_class = DireccionSerializer 
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        if self.request.user.is_staff: 
            return Direccion.objects.all()
        if hasattr(self.request.user, 'cliente_data'):
            return Direccion.objects.filter(cliente=self.request.user.cliente_data)
        return Direccion.objects.none()

# 8. CAMBIO DE CONTRASEÑA
class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,) 

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.data.get('old_password')):
                return Response({"old_password": ["Incorrecta"]}, status=400)
            user.set_password(serializer.data.get('new_password'))
            user.save()
            return Response({"detail": "Contraseña actualizada."})
        return Response(serializer.errors, status=400)
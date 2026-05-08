# usuarios/views.py
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
import uuid

from .models import BuyerProfile, SellerProfile, Cliente, Direccion
from .serializers import (
    UserSerializer,
    ClienteRegistrationSerializer,
    SellerRegistrationSerializer,
    RepartidorRegistrationSerializer,
    BuyerProfileSerializer,
    SellerProfileSerializer,
    ClienteSerializer,
    DireccionSerializer,
    ChangePasswordSerializer,
)
from .permissions import IsSeller, IsCliente, IsOwnerOrReadOnly

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

CustomUser = get_user_model()


# ------------------------------------------------------------------
# 1. TOKEN JWT CON DATOS DEL USUARIO
# ------------------------------------------------------------------
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        print("=== VALIDATE EJECUTADO ===")
        data = super().validate(attrs)
        print("=== USER:", self.user)
        data['user'] = UserSerializer(self.user).data
        print("=== DATA KEYS:", list(data.keys()))
        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


# ------------------------------------------------------------------
# 2. REGISTRO DE CLIENTE
# Cualquier visitante puede registrarse como cliente.
# ------------------------------------------------------------------
class ClienteRegistrationView(generics.CreateAPIView):
    """
    Registro de cliente.
    Crea: CustomUser + BuyerProfile (automático) + Cliente
    Devuelve tokens JWT al completar el registro.
    """
    serializer_class = ClienteRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Cliente registrado exitosamente.",
                "user_id": user.id,
                "tokens": serializer.data.get('tokens'),
            },
            status=status.HTTP_201_CREATED
        )


# ------------------------------------------------------------------
# 3. REGISTRO DE VENDEDOR
# El usuario completa el registro como emprendedor.
# ------------------------------------------------------------------
class SellerRegistrationView(generics.CreateAPIView):
    """
    Registro de vendedor/emprendedor.
    Crea: CustomUser + BuyerProfile + SellerProfile + Cliente + Direccion
    Activa is_vendedor=True automáticamente.
    Devuelve tokens JWT al completar el registro.
    """
    serializer_class = SellerRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Vendedor registrado exitosamente.",
                "user_id": user.id,
                "tokens": serializer.data.get('tokens'),
            },
            status=status.HTTP_201_CREATED
        )


# ------------------------------------------------------------------
# 4. REGISTRO DE REPARTIDOR
# El usuario completa el registro como repartidor.
# ------------------------------------------------------------------
class RepartidorRegistrationView(generics.CreateAPIView):
    """
    Registro de repartidor.
    Crea: CustomUser + BuyerProfile + Repartidor + Cliente
    Activa is_repartidor=True automáticamente.
    Devuelve tokens JWT al completar el registro.
    """
    serializer_class = RepartidorRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Repartidor registrado exitosamente.",
                "user_id": user.id,
                "tokens": serializer.data.get('tokens'),
            },
            status=status.HTTP_201_CREATED
        )


# ------------------------------------------------------------------
# 5. PERFIL DEL USUARIO AUTENTICADO
# Ver y editar datos básicos del usuario.
# ------------------------------------------------------------------
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de usuarios.
    - Lista: solo staff
    - Detalle: solo el propio usuario o staff
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['list']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_staff:
            return CustomUser.objects.all()
        return CustomUser.objects.filter(pk=self.request.user.pk)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Retorna los datos del usuario autenticado."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


# ------------------------------------------------------------------
# 6. BUYER PROFILE VIEWSET
# ------------------------------------------------------------------
class BuyerProfileViewSet(viewsets.ModelViewSet):
    """Gestión del perfil de cliente."""
    serializer_class = BuyerProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return BuyerProfile.objects.all()
        if hasattr(self.request.user, 'buyer_profile'):
            return BuyerProfile.objects.filter(user=self.request.user)
        return BuyerProfile.objects.none()

    @action(detail=False, methods=['get'])
    def mi_perfil(self, request):
        """Retorna el perfil del cliente autenticado."""
        perfil = getattr(request.user, 'buyer_profile', None)
        if perfil:
            return Response(self.get_serializer(perfil).data)
        return Response(
            {"detail": "Perfil de cliente no encontrado."},
            status=status.HTTP_404_NOT_FOUND
        )


# ------------------------------------------------------------------
# 7. SELLER PROFILE VIEWSET
# ------------------------------------------------------------------
class SellerProfileViewSet(viewsets.ModelViewSet):
    """Gestión del perfil de vendedor."""
    serializer_class = SellerProfileSerializer
    permission_classes = [IsAuthenticated, IsSeller]

    def get_queryset(self):
        if self.request.user.is_staff:
            return SellerProfile.objects.all()
        if hasattr(self.request.user, 'seller_profile'):
            return SellerProfile.objects.filter(user=self.request.user)
        return SellerProfile.objects.none()

    @action(detail=False, methods=['get'])
    def mi_perfil(self, request):
        """Retorna el perfil del vendedor autenticado."""
        perfil = getattr(request.user, 'seller_profile', None)
        if perfil:
            return Response(self.get_serializer(perfil).data)
        return Response(
            {"detail": "Perfil de vendedor no encontrado."},
            status=status.HTTP_404_NOT_FOUND
        )


# ------------------------------------------------------------------
# 8. CLIENTE VIEWSET
# Maneja clientes registrados e invitados.
# ------------------------------------------------------------------
class ClienteViewSet(viewsets.ModelViewSet):
    """Gestión de clientes (registrados e invitados)."""
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Cliente.objects.all()
        if hasattr(self.request.user, 'cliente_data'):
            return Cliente.objects.filter(user=self.request.user)
        return Cliente.objects.none()

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_or_create_guest(self, request):
        """
        Obtiene o crea un cliente invitado.
        Si se envía guest_uuid y existe → retorna el existente.
        Si no → crea uno nuevo con UUID generado.
        """
        guest_uuid_str = request.data.get('guest_uuid')
        if guest_uuid_str:
            cliente = Cliente.objects.filter(
                guest_uuid=guest_uuid_str,
                user__isnull=True
            ).first()
            if cliente:
                return Response(self.get_serializer(cliente).data)

        # Crear nuevo cliente invitado
        cliente = Cliente.objects.create(
            guest_uuid=uuid.uuid4(),
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', ''),
            email=request.data.get('email'),
            telefono=request.data.get('telefono'),
        )
        return Response(
            self.get_serializer(cliente).data,
            status=status.HTTP_201_CREATED
        )


# ------------------------------------------------------------------
# 9. DIRECCIÓN VIEWSET
# ------------------------------------------------------------------
class DireccionViewSet(viewsets.ModelViewSet):
    """Gestión de direcciones del cliente autenticado."""
    serializer_class = DireccionSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Direccion.objects.all()
        if hasattr(self.request.user, 'cliente_data'):
            return Direccion.objects.filter(
                cliente=self.request.user.cliente_data
            )
        return Direccion.objects.none()

    def perform_create(self, serializer):
        """Asigna automáticamente el cliente al crear una dirección."""
        serializer.save(cliente=self.request.user.cliente_data)


# ------------------------------------------------------------------
# 10. CAMBIO DE CONTRASEÑA
# ------------------------------------------------------------------
class ChangePasswordView(APIView):
    """Cambio de contraseña del usuario autenticado."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {"old_password": "Contraseña actual incorrecta."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(
                {"detail": "Contraseña actualizada exitosamente."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
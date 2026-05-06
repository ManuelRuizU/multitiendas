# repartidores/views.py


from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.serializers import ValidationError
from django.db import transaction
from django.contrib.auth import get_user_model 
import uuid 

from rest_framework.views import APIView 

from .models import BuyerProfile, SellerProfile, Cliente, Direccion, UserType
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
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

CustomUser = get_user_model() 

# ------------------------------------------------------------------
# 1. VISTA PERSONALIZADA PARA OBTENER TOKEN JWT (MyTokenObtainPairView)
# ------------------------------------------------------------------
class MyTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            user = CustomUser.objects.get(username=request.data['username']) 
            user_data = UserSerializer(user).data 
            response.data['user'] = user_data
        return response

# ------------------------------------------------------------------
# 2. USER VIEWSET (Para registro general de compradores y gestión de CustomUser)
# ------------------------------------------------------------------
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

    def perform_create(self, serializer):
        if CustomUser.objects.filter(username=serializer.validated_data['username']).exists():
            raise ValidationError("El nombre de usuario ya existe.")
        if CustomUser.objects.filter(email=serializer.validated_data['email']).exists():
            raise ValidationError("El correo electrónico ya existe.")
        user = serializer.save() 

    def perform_update(self, serializer):
        if not self.request.user.is_staff and serializer.instance != self.request.user:
            raise ValidationError("No tienes permiso para actualizar este usuario.")
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if not self.request.user.is_staff and instance != self.request.user:
            raise ValidationError("No tienes permiso para eliminar este usuario.")
        super().perform_destroy(instance)

# ------------------------------------------------------------------
# 3. VISTA DE REGISTRO DE VENDEDOR (SellerRegistrationView)
# ------------------------------------------------------------------
class SellerRegistrationView(generics.CreateAPIView):
    serializer_class = SellerRegistrationSerializer
    permission_classes = [AllowAny] 

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save() # Guarda el usuario y crea el SellerProfile
        
        # Refresca la instancia del usuario para asegurar que seller_profile esté cargado
        user.refresh_from_db() 
        
        return Response(
            {"message": "Vendedor registrado exitosamente con perfil completo.", "user_id": user.id}, 
            status=status.HTTP_201_CREATED
        )

# ------------------------------------------------------------------
# 4. BUYER PROFILE VIEWSET (CRUD para perfiles de comprador)
# ------------------------------------------------------------------
class BuyerProfileViewSet(viewsets.ModelViewSet):
    queryset = BuyerProfile.objects.all()
    serializer_class = BuyerProfileSerializer
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        if self.request.user.is_staff: 
            return BuyerProfile.objects.all()
        if hasattr(self.request.user, 'buyer_profile'):
            return BuyerProfile.objects.filter(user=self.request.user)
        return BuyerProfile.objects.none()

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'buyer_profile'):
            raise ValidationError("Este usuario ya tiene un perfil de comprador.")
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        if not self.request.user.is_staff and serializer.instance.user != self.request.user:
            raise ValidationError("No tienes permiso para actualizar este perfil de comprador.")
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if not self.request.user.is_staff and instance.user != self.request.user:
            raise ValidationError("No tienes permiso para eliminar este perfil de comprador.")
        super().perform_destroy(instance)

    @action(detail=False, methods=['get'])
    def mi_perfil(self, request):
        try:
            perfil = request.user.buyer_profile
            serializer = self.get_serializer(perfil)
            return Response(serializer.data)
        except BuyerProfile.DoesNotExist:
            return Response({"detail": "Perfil de comprador no encontrado para este usuario."}, status=status.HTTP_404_NOT_FOUND)

# ------------------------------------------------------------------
# 5. SELLER PROFILE VIEWSET (CRUD para perfiles de vendedor)
# ------------------------------------------------------------------
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

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'seller_profile'):
            raise ValidationError("Este usuario ya tiene un perfil de vendedor.")
        serializer.save(user=self.request.user) 

    def perform_update(self, serializer):
        if not self.request.user.is_staff and serializer.instance.user != self.request.user:
            raise ValidationError("No tienes permiso para actualizar este perfil de vendedor.")
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if not self.request.user.is_staff and instance.user != self.request.user:
            raise ValidationError("No tienes permiso para eliminar este perfil de vendedor.")
        super().perform_destroy(instance)

    @action(detail=False, methods=['get', 'patch'])
    def mi_perfil(self, request):
        try:
            perfil = request.user.seller_profile
            serializer = self.get_serializer(perfil)
            return Response(serializer.data)
        except SellerProfile.DoesNotExist:
            return Response({"detail": "Perfil de vendedor no encontrado para este usuario."}, status=status.HTTP_404_NOT_FOUND)

# ------------------------------------------------------------------
# 6. CLIENTE VIEWSET (CRUD para el modelo Cliente - registrados e invitados)
# ------------------------------------------------------------------
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        if self.request.user.is_staff: 
            return Cliente.objects.all()
        if self.request.user.is_authenticated and hasattr(self.request.user, 'cliente_data'):
            return Cliente.objects.filter(user=self.request.user)
        return Cliente.objects.none()

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            if hasattr(self.request.user, 'cliente_data'):
                raise ValidationError("Este usuario ya tiene un perfil de cliente asociado.")
            serializer.save(user=self.request.user, is_guest=False, guest_uuid=None)
        else:
            raise ValidationError("Debes estar autenticado para crear un perfil de cliente.")

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            if serializer.instance.user != self.request.user:
                raise ValidationError("No tienes permiso para actualizar este perfil de cliente.")
            if serializer.instance.is_guest and 'guest_uuid' in serializer.validated_data and serializer.validated_data['guest_uuid'] != serializer.instance.guest_uuid:
                raise ValidationError("No puedes cambiar el guest_uuid de un cliente invitado existente.")
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if not self.request.user.is_staff and instance.user != self.request.user:
            raise ValidationError("No tienes permiso para eliminar este perfil de cliente.")
        super().perform_destroy(instance)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def get_or_create_guest_client(self, request):
        guest_uuid_str = request.data.get('guest_uuid')
        email = request.data.get('email')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        telefono = request.data.get('telefono')

        if guest_uuid_str:
            try:
                cliente_instance = Cliente.objects.get(guest_uuid=guest_uuid_str, user__isnull=True)
                serializer = self.get_serializer(cliente_instance)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Cliente.DoesNotExist:
                pass 
            except ValueError:
                raise ValidationError({"guest_uuid": "Formato de UUID inválido."})

        if not guest_uuid_str:
            import uuid 
            guest_uuid_str = uuid.uuid4() 

        serializer = self.get_serializer(data={
            'guest_uuid': guest_uuid_str,
            'is_guest': True,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'telefono': telefono,
        })
        serializer.is_valid(raise_exception=True)
        cliente_instance = serializer.save(user=None, is_guest=True) 
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# ------------------------------------------------------------------
# 7. DIRECCIÓN VIEWSET (CRUD para Direcciones)
# ------------------------------------------------------------------
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

    def perform_create(self, serializer):
        if not hasattr(self.request.user, 'cliente_data'):
            raise ValidationError("El usuario debe tener un perfil de cliente para añadir direcciones.")
        with transaction.atomic():
            # Si la nueva dirección es principal, desmarcar otras direcciones principales
            if serializer.validated_data.get('principal', False):
                Direccion.objects.filter(cliente=self.request.user.cliente_data, principal=True).update(principal=False)
            serializer.save(cliente=self.request.user.cliente_data)

    def perform_update(self, serializer):
        direccion_a_actualizar = self.get_object()
        if not self.request.user.is_staff and direccion_a_actualizar.cliente.user != self.request.user:
            raise ValidationError("No tienes permiso para actualizar esta dirección.")
        with transaction.atomic():
            # Si la dirección actualizada se marca como principal, desmarcar otras
            if serializer.validated_data.get('principal', False):
                Direccion.objects.filter(cliente=self.request.user.cliente_data, principal=True).exclude(id=direccion_a_actualizar.id).update(principal=False)
            serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff and instance.cliente.user != self.request.user:
            raise ValidationError("No tienes permiso para eliminar esta dirección.")
        super().perform_destroy(instance)

# ------------------------------------------------------------------
# 8. CAMBIO DE CONTRASEÑA (ChangePasswordView)
# ------------------------------------------------------------------
class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,) 

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.data.get('old_password')):
                return Response({"old_password": ["Contraseña antigua incorrecta."]}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.data.get('new_password'))
            user.save()
            return Response({"detail": "Contraseña actualizada correctamente."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# usuarios/views.py
# Elimina importaciones de authtoken, ya no las necesitamos
# from rest_framework.authtoken.views import ObtainAuthToken
# from rest_framework.authtoken.models import Token 

# Asegúrate de que estas importaciones están
from django.utils.decorators import method_decorator # Mantenemos si se necesita para otros decoradores
from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model # Mejor usar get_user_model para el modelo de usuario
from .models import PerfilVendedor, Cliente, Direccion
from .serializers import UserSerializer, UserRegisterSerializer, PerfilVendedorSerializer, ClienteSerializer, DireccionSerializer
from rest_framework.serializers import ValidationError as SerializerValidationError 
from django.db import IntegrityError 

# Obtener el modelo de usuario actual de Django (es una buena práctica)
User = get_user_model() 

# --- VISTA PARA REGISTRO DE USUARIOS ---
# Ya no es necesario el decorador @method_decorator(csrf_exempt, name='dispatch')
# si csrf_middleware está comentado en settings.py y usas DRF.
class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny] # Cualquiera puede registrarse

    def create(self, request, *args, **kwargs):
        print("--- Iniciando método create en RegisterUserView ---")
        print(f"Request method: {request.method}")
        print(f"Request data: {request.data}")
        print(f"Request user authenticated: {request.user.is_authenticated}")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        # Opcional: Podrías querer devolver los tokens JWT directamente aquí después del registro
        # Esto requeriría importar TokenObtainPairSerializer de simple_jwt y usarlo.
        # Por ahora, solo devolvemos los datos del usuario, y el cliente hará otra petición a /api/token/
        
        return Response({"username": user.username, "email": user.email, "id": user.id},
                        status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save()

# --- UserViewSet (Mantener si aún lo necesitas, principalmente para admins) ---
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser] # Solo para usuarios staff/admin


# --- PerfilVendedorViewSet (No requiere cambios directos por JWT) ---
class PerfilVendedorViewSet(viewsets.ModelViewSet):
    queryset = PerfilVendedor.objects.all()
    serializer_class = PerfilVendedorSerializer
    permission_classes = [permissions.IsAuthenticated] # Requiere JWT para autenticación

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_staff: 
            return PerfilVendedor.objects.all()
        return PerfilVendedor.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if PerfilVendedor.objects.filter(user=self.request.user).exists():
            raise SerializerValidationError({"detail": "Ya existe un perfil de vendedor para este usuario."})
        serializer.save(user=self.request.user)

    # Puedes mantener el @action my_profile si lo necesitas y está en tus urls.
    # from rest_framework.decorators import action
    # @action(detail=False, methods=['get', 'post'], url_path='mi-perfil')
    # def my_profile(self, request):
    #     ...


# --- ClienteViewSet (No requiere cambios directos por JWT) ---
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    
    def get_permissions(self):
        if self.action == 'create': 
            return [permissions.AllowAny()] 
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                return Cliente.objects.all()
            return Cliente.objects.filter(user=self.request.user)
        return Cliente.objects.none()

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            if Cliente.objects.filter(user=self.request.user).exists():
                raise SerializerValidationError({"detail": "Ya existe un perfil de cliente para este usuario."})
            serializer.save(user=self.request.user)
        else:
            try:
                serializer.save()
            except IntegrityError:
                raise SerializerValidationError({"detail": "Error al crear cliente invitado. El email podría estar duplicado o ya registrado."})

    # Mantén el @action my_profile si lo necesitas y está en tus urls.
    # from rest_framework.decorators import action
    # @action(detail=False, methods=['get'], url_path='mi-perfil')
    # def my_profile(self, request):
    #    ...


# --- DireccionViewSet (No requiere cambios directos por JWT) ---
class DireccionViewSet(viewsets.ModelViewSet):
    queryset = Direccion.objects.all()
    serializer_class = DireccionSerializer
    permission_classes = [permissions.IsAuthenticated] # Requiere JWT para autenticación

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return Direccion.objects.all()
        
        try:
            cliente = Cliente.objects.get(user=self.request.user)
            return self.queryset.filter(cliente=cliente)
        except Cliente.DoesNotExist:
            return Direccion.objects.none() 

    def perform_create(self, serializer):
        try:
            cliente = Cliente.objects.get(user=self.request.user)
        except Cliente.DoesNotExist:
            raise SerializerValidationError({"detail": "Para crear una dirección, debes tener un perfil de cliente asociado a tu cuenta."})
        
        serializer.save(cliente=cliente)

# --- ¡MUY IMPORTANTE! Esta clase DEBE ELIMINARSE ---
# La funcionalidad de obtener tokens ahora es manejada por simple_jwt
# No necesitas esta vista personalizada CustomAuthToken.
# class CustomAuthToken(ObtainAuthToken):
#    def post(self, request, *args, **kwargs):
#        serializer = self.serializer_class(data=request.data,
#                                           context={'request': request})
#        serializer.is_valid(raise_exception=True)
#        user = serializer.validated_data['user']
#        token, created = Token.objects.get_or_create(user=user) # ESTO ES EL PROBLEMA
#        return Response({
#            'token': token.key,
#            'user_id': user.pk,
#            'email': user.email,
#            'username': user.username
#        })
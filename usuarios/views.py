# usuarios/views.py
from rest_framework import viewsets, generics, permissions, status # Asegúrate de importar 'generics', 'permissions', 'status'
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import PerfilVendedor, Cliente, Direccion
# Importa tu nuevo serializador para el registro y los otros serializadores
from .serializers import UserSerializer, UserRegisterSerializer, PerfilVendedorSerializer, ClienteSerializer, DireccionSerializer


# --- VISTA PARA REGISTRO DE USUARIOS (NUEVA CLASE) ---
class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer # Usa el serializador de registro aquí
    permission_classes = [permissions.AllowAny] # Permite que cualquiera se registre

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # Puedes retornar solo el username o un token si usas tokens
        return Response({"username": user.username, "email": user.email, "id": user.id},
                        status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        # Llama al método create del serializador para manejar el hashing de la contraseña
        return serializer.save()
# --- FIN DE RegisterUserView ---


# Tus ViewSets existentes (si los tenías)
class UserViewSet(viewsets.ReadOnlyModelViewSet): # Este ViewSet es solo para ver usuarios (admin/lectura)
    queryset = User.objects.all()
    serializer_class = UserSerializer # Usa el UserSerializer básico (sin passwords)
    permission_classes = [permissions.IsAdminUser] # Solo admins pueden ver todos los usuarios

class PerfilVendedorViewSet(viewsets.ModelViewSet):
    queryset = PerfilVendedor.objects.all()
    serializer_class = PerfilVendedorSerializer
    permission_classes = [permissions.IsAuthenticated] # Solo autenticados pueden ver/editar perfiles

    # Opcional: Asegurar que un usuario solo pueda ver/editar su propio perfil
    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_staff: # O un rol de super_vendedor
            return PerfilVendedor.objects.all()
        return PerfilVendedor.objects.filter(user=self.request.user)


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Opcional: Asegurar que un usuario solo pueda ver/editar su propio perfil de cliente
    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return Cliente.objects.all()
        return Cliente.objects.filter(user=self.request.user)


class DireccionViewSet(viewsets.ModelViewSet):
    queryset = Direccion.objects.all()
    serializer_class = DireccionSerializer
    permission_classes = [permissions.IsAuthenticated]

    # Asegurar que un usuario solo pueda ver/editar sus propias direcciones
    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return Direccion.objects.all()
        return Direccion.objects.filter(cliente__user=self.request.user)

    # Al crear una dirección, automáticamente asignarla al cliente del usuario autenticado
    def perform_create(self, serializer):
        if self.request.user.is_authenticated and hasattr(self.request.user, 'cliente'):
            serializer.save(cliente=self.request.user.cliente)
        else:
            # Puedes manejar esto con un error o con una lógica para crear el perfil de cliente
            raise serializers.ValidationError("Usuario no tiene perfil de cliente.")
# usuarios/views.py
from rest_framework import viewsets
from django.contrib.auth.models import User
from .models import PerfilVendedor, Cliente, Direccion
from .serializers import UserSerializer, PerfilVendedorSerializer, ClienteSerializer, DireccionSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny # Importa permisos

# Permisos: puedes personalizar esto más adelante
# Por ahora, IsAuthenticated para la mayoría, AllowAny para la creación de usuarios si es pública.

class UserViewSet(viewsets.ReadOnlyModelViewSet): # ReadOnly para seguridad, no se editan users directamente por API
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated] # Solo usuarios autenticados pueden ver usuarios

class PerfilVendedorViewSet(viewsets.ModelViewSet):
    queryset = PerfilVendedor.objects.all()
    serializer_class = PerfilVendedorSerializer
    permission_classes = [IsAuthenticated] # Solo autenticados pueden ver/editar perfiles

    # Opcional: Asegurar que un usuario solo pueda ver/editar su propio perfil
    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_staff: # O un rol de super_vendedor
            return PerfilVendedor.objects.all()
        return PerfilVendedor.objects.filter(user=self.request.user)


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    # Opcional: Asegurar que un usuario solo pueda ver/editar su propio perfil de cliente
    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return Cliente.objects.all()
        return Cliente.objects.filter(user=self.request.user)


class DireccionViewSet(viewsets.ModelViewSet):
    queryset = Direccion.objects.all()
    serializer_class = DireccionSerializer
    permission_classes = [IsAuthenticated]

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

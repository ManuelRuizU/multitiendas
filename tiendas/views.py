# tiendas/views.py
from rest_framework import viewsets
from .models import Tienda, RadioEnvio
from .serializers import TiendaSerializer, RadioEnvioSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny # Permisos

class TiendaViewSet(viewsets.ModelViewSet):
    queryset = Tienda.objects.all()
    serializer_class = TiendaSerializer
    permission_classes = [AllowAny] # Permite ver todas las tiendas para todos

    # Solo el vendedor asociado o un superusuario puede editar/borrar su tienda
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated] # O una clase de permiso personalizada
            # Aquí podrías añadir una lógica para verificar si el usuario es el dueño de la tienda
        return super().get_permissions()

    # Opcional: Filtrar tiendas por el vendedor actual para listados específicos
    # def get_queryset(self):
    #     if self.request.user.is_authenticated and hasattr(self.request.user, 'perfil_vendedor'):
    #         return Tienda.objects.filter(vendedor=self.request.user.perfil_vendedor)
    #     return Tienda.objects.none() # No mostrar nada si no es un vendedor o está autenticado

    # Al crear una tienda, automáticamente asignarla al vendedor autenticado
    def perform_create(self, serializer):
        if self.request.user.is_authenticated and hasattr(self.request.user, 'perfil_vendedor'):
            serializer.save(vendedor=self.request.user.perfil_vendedor)
        else:
            raise serializers.ValidationError("Solo vendedores registrados pueden crear tiendas.")


class RadioEnvioViewSet(viewsets.ModelViewSet):
    queryset = RadioEnvio.objects.all()
    serializer_class = RadioEnvioSerializer
    permission_classes = [IsAuthenticated] # Solo usuarios autenticados pueden ver/editar radios

    # Asegurar que solo se pueda ver/editar radios de las tiendas del vendedor autenticado
    def get_queryset(self):
        if self.request.user.is_authenticated and hasattr(self.request.user, 'perfil_vendedor'):
            return RadioEnvio.objects.filter(tienda__vendedor=self.request.user.perfil_vendedor)
        return RadioEnvio.objects.none()

    # Al crear, asegurar que el radio se asocie a una tienda del vendedor actual
    def perform_create(self, serializer):
        tienda = serializer.validated_data.get('tienda')
        if tienda.vendedor != self.request.user.perfil_vendedor:
            raise serializers.ValidationError("No tienes permiso para añadir radios de envío a esta tienda.")
        serializer.save()

    # tiendas/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.serializers import ValidationError
from rest_framework.decorators import action

from .models import Tienda, RadioEnvio, CuadranteEnvio
from .serializers import TiendaSerializer, RadioEnvioSerializer, CuadranteEnvioSerializer

from usuarios.permissions import IsSeller 
from usuarios.models import SellerProfile

class TiendaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar las Tiendas.
    - Público: Ver todas las tiendas activas.
    - Vendedores: Gestionar sus propias tiendas.
    """
    serializer_class = TiendaSerializer

    def get_permissions(self):
        # Solo los vendedores pueden crear, editar o borrar
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsSeller()]
        return [AllowAny()]

    def get_queryset(self):
        user = self.request.user
        # Si el usuario es vendedor y no es administrador, ve solo sus tiendas
        if user.is_authenticated and hasattr(user, 'seller_profile') and not user.is_staff:
            return Tienda.objects.filter(propietario_perfil=user.seller_profile)
        # Por defecto (Público/Admin) se ven todas las tiendas activas
        return Tienda.objects.filter(activo=True)

    def perform_create(self, serializer):
        # Asigna automáticamente el perfil del vendedor logueado
        if not hasattr(self.request.user, 'seller_profile'):
            raise ValidationError("El usuario no tiene un perfil de vendedor asociado.")
        serializer.save(propietario_perfil=self.request.user.seller_profile)

    def perform_update(self, serializer):
        # Validación de seguridad extra: el vendedor solo edita lo suyo
        tienda = self.get_object()
        if not self.request.user.is_staff and tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No tienes permiso para modificar esta tienda.")
        super().perform_update(serializer)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def calcular_envio(self, request, pk=None):
        """
        Calcula el costo de envío basado en latitud y longitud del cliente.
        URL: /api/tiendas/{id}/calcular_envio/?lat=-37.79&lng=-72.71
        """
        tienda = self.get_object()
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')

        if not lat or not lng:
            return Response(
                {'detail': 'Se requieren los parámetros "lat" y "lng" (coordenadas del cliente).'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Lógica centralizada en el modelo (Ray Casting + Haversine)
            costo = tienda.calcular_costo_envio(lat, lng)
            
            if costo is not None:
                return Response({
                    'tienda': tienda.nombre,
                    'costo_envio': costo,
                    'cubierto': True
                }, status=status.HTTP_200_OK)
            
            return Response({
                'detail': 'La ubicación se encuentra fuera del radio y cuadrantes de cobertura.',
                'costo_envio': None,
                'cubierto': False
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'detail': f'Error en el cálculo: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


class RadioEnvioViewSet(viewsets.ModelViewSet):
    """
    Gestiona los radios circulares de cobertura.
    """
    serializer_class = RadioEnvioSerializer
    permission_classes = [IsSeller]

    def get_queryset(self):
        # Solo muestra los radios de las tiendas que pertenecen al vendedor
        if self.request.user.is_authenticated and hasattr(self.request.user, 'seller_profile'):
            return RadioEnvio.objects.filter(tienda__propietario_perfil=self.request.user.seller_profile)
        return RadioEnvio.objects.none()

    def perform_create(self, serializer):
        tienda = serializer.validated_data['tienda']
        if tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No puedes añadir radios a una tienda que no te pertenece.")
        serializer.save()


class CuadranteEnvioViewSet(viewsets.ModelViewSet):
    """
    Gestiona los polígonos (geofencing) de cobertura.
    """
    serializer_class = CuadranteEnvioSerializer
    permission_classes = [IsSeller]

    def get_queryset(self):
        # Solo muestra los cuadrantes de las tiendas que pertenecen al vendedor
        if self.request.user.is_authenticated and hasattr(self.request.user, 'seller_profile'):
            return CuadranteEnvio.objects.filter(tienda__propietario_perfil=self.request.user.seller_profile)
        return CuadranteEnvio.objects.none()

    def perform_create(self, serializer):
        tienda = serializer.validated_data['tienda']
        if tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No puedes añadir cuadrantes a una tienda que no te pertenece.")
        serializer.save()
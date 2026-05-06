    # tiendas/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.serializers import ValidationError
from rest_framework.decorators import action 

from .models import Tienda, RadioEnvio
from .serializers import TiendaSerializer, RadioEnvioSerializer

from usuarios.permissions import IsSeller 
from usuarios.models import SellerProfile

class TiendaViewSet(viewsets.ModelViewSet):
    queryset = Tienda.objects.all()
    serializer_class = TiendaSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsSeller()] 
        return [AllowAny()]

    def get_queryset(self):
        if self.request.user.is_authenticated and hasattr(self.request.user, 'seller_profile') and not self.request.user.is_staff:
            return Tienda.objects.filter(propietario_perfil=self.request.user.seller_profile)
        return Tienda.objects.all()

    def perform_create(self, serializer):
        try:
            perfil_vendedor = self.request.user.seller_profile
        except SellerProfile.DoesNotExist:
            raise ValidationError("El usuario no tiene un perfil de vendedor asociado.")
        serializer.save(propietario_perfil=perfil_vendedor)

    def perform_update(self, serializer):
        tienda_a_actualizar = self.get_object()
        if not self.request.user.is_staff and tienda_a_actualizar.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No tienes permiso para actualizar esta tienda.")
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if not self.request.user.is_staff and instance.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No tienes permiso para eliminar esta tienda.")
        super().perform_destroy(instance)


    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def calcular_envio(self, request, pk=None):
        try:
            tienda = self.get_object() 
        except Tienda.DoesNotExist:
            return Response({'detail': 'Tienda no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        distancia_km_str = request.query_params.get('distancia_km')

        if not distancia_km_str:
            return Response({'detail': 'Parámetro "distancia_km" es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            distancia_km_float = float(distancia_km_str)
            if distancia_km_float < 0:
                raise ValueError
        except ValueError:
            return Response({'detail': 'La distancia_km debe ser un número positivo válido.'}, status=status.HTTP_400_BAD_REQUEST)

        costo = tienda.calcular_costo_envio(distancia_km_float)

        if costo is not None:
            return Response({'costo_envio': costo}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Distancia fuera del radio de cobertura para esta tienda.', 'costo_envio': None}, status=status.HTTP_404_NOT_FOUND)


class RadioEnvioViewSet(viewsets.ModelViewSet):
    queryset = RadioEnvio.objects.all()
    serializer_class = RadioEnvioSerializer
    permission_classes = [IsSeller] 

    def get_queryset(self):
        if self.request.user.is_authenticated and hasattr(self.request.user, 'seller_profile'):
            return RadioEnvio.objects.filter(tienda__propietario_perfil=self.request.user.seller_profile)
        return RadioEnvio.objects.none()

    def perform_create(self, serializer):
        vendedor_autenticado = self.request.user.seller_profile
        tienda_obj = serializer.validated_data['tienda'] 
        if tienda_obj.propietario_perfil != vendedor_autenticado:
            raise ValidationError({"tienda": "No tienes permiso para añadir radios de envío a esta tienda."})
        serializer.save(tienda=tienda_obj)

    def perform_update(self, serializer):
        radio_a_actualizar = self.get_object()
        if not self.request.user.is_staff and radio_a_actualizar.tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No tienes permiso para actualizar este radio de envío.")
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if not self.request.user.is_staff and instance.tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No tienes permiso para eliminar este radio de envío.")
        super().perform_destroy(instance)


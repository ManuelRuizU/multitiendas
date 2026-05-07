# pedidos/views.py
# version mejorada y corregida 13/8/2025

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.serializers import ValidationError
from django.db import transaction 
from django.shortcuts import get_object_or_404

# Importamos los MODELOS necesarios
from .models import Order, OrderItem 
from productos.models import Producto 
from tiendas.models import Tienda 
from usuarios.models import Cliente, Direccion 

# Importamos los SERIALIZADORES
from .serializers import OrderSerializer, OrderItemSerializer, OrderInvitadoSerializer

# Permiso personalizado para OrderViewSet
class IsOrderOwnerOrSeller(permissions.BasePermission):
    """
    Permite el acceso a un pedido si:
    - El usuario autenticado es el cliente que realizó el pedido.
    - El usuario autenticado es el vendedor de la tienda asociada al pedido.
    - El usuario es staff/superadmin.
    """
    def has_permission(self, request, view):
        # Para la lista de pedidos, solo usuarios autenticados
        if request.user.is_authenticated:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        # obj es una instancia de Order o OrderItem
        if request.user.is_staff:
            return True

        if hasattr(request.user, 'cliente_data'):
            if isinstance(obj, Order) and obj.cliente == request.user.cliente_data:
                return True
            if isinstance(obj, OrderItem) and obj.order.cliente == request.user.cliente_data:
                return True

        if hasattr(request.user, 'seller_profile'):
            if isinstance(obj, Order) and obj.tienda.propietario_perfil == request.user.seller_profile:
                return True
            if isinstance(obj, OrderItem) and obj.order.tienda.propietario_perfil == request.user.seller_profile:
                return True
            
        return False


VALID_TRANSITIONS = {
    'PENDING':    ['CONFIRMED', 'CANCELLED'],
    'CONFIRMED':  ['PREPARING', 'CANCELLED'],
    'PREPARING':  ['ON_THE_WAY', 'CANCELLED'],
    'ON_THE_WAY': ['DELIVERED', 'CANCELLED'],
    'DELIVERED':  [],
    'CANCELLED':  [],
}


# ViewSet para usuarios registrados
class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderOwnerOrSeller] 

    def get_queryset(self):
        # Filtra los pedidos para que solo sean visibles por el cliente o vendedor apropiado
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return Order.objects.all()
        if hasattr(user, 'cliente_data'):
            return Order.objects.filter(cliente=user.cliente_data)
        if hasattr(user, 'seller_profile'):
            # Los vendedores solo pueden ver los pedidos de su tienda
            return Order.objects.filter(tienda__propietario_perfil=user.seller_profile)
        return Order.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        
        # 1. Obtener el perfil de cliente o lanzar un error si no existe.
        # Esto es más explícito que solo usar `hasattr` y es una práctica común.
        try:
            cliente_perfil = Cliente.objects.get(user=user)
        except Cliente.DoesNotExist:
            raise ValidationError("El usuario debe tener un perfil de cliente para realizar pedidos.")
        
        delivery_address_id = self.request.data.get('delivery_address_id')
        billing_address_id = self.request.data.get('billing_address_id')
        
        # 2. Validar que las direcciones pertenecen al cliente autenticado.
        try:
            delivery_address_obj = Direccion.objects.get(id=delivery_address_id, cliente=cliente_perfil)
        except Direccion.DoesNotExist:
            raise ValidationError({"delivery_address_id": "La dirección de envío no pertenece a este cliente."})
        
        if billing_address_id:
            try:
                billing_address_obj = Direccion.objects.get(id=billing_address_id, cliente=cliente_perfil)
            except Direccion.DoesNotExist:
                raise ValidationError({"billing_address_id": "La dirección de facturación no pertenece a este cliente."})
        
        # 3. Guardar el pedido, asignando el perfil de cliente validado.
        serializer.save(cliente=cliente_perfil)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOrderOwnerOrSeller])
    def change_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')

        if new_status not in [choice[0] for choice in Order.STATUS_CHOICES]:
            return Response({'error': 'Estado de pedido inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        allowed = VALID_TRANSITIONS.get(order.status, [])
        if new_status not in allowed:
            return Response(
                {'error': f"Transición no permitida: {order.status} → {new_status}. "
                          f"Transiciones válidas: {allowed or 'ninguna'}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if self.request.user.is_staff or \
           (hasattr(self.request.user, 'seller_profile') and order.tienda.propietario_perfil == self.request.user.seller_profile):
            order.status = new_status
            order.save()
            return Response({'status': f'Estado cambiado a {new_status}'})
        else:
            return Response({'error': 'No tiene permiso para cambiar el estado de este pedido.'}, status=status.HTTP_403_FORBIDDEN)


# ViewSet para los items del pedido (solo lectura)
class OrderItemViewSet(viewsets.ReadOnlyModelViewSet): 
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderOwnerOrSeller] 

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return OrderItem.objects.all()
        
        if hasattr(user, 'cliente_data'):
            return OrderItem.objects.filter(order__cliente=user.cliente_data)

        if hasattr(user, 'seller_profile'):
            return OrderItem.objects.filter(order__tienda__propietario_perfil=user.seller_profile)
            
        return OrderItem.objects.none() 


# ViewSet para usuarios invitados
class OrderInvitadoViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderInvitadoSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        serializer.save()

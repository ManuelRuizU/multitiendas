# pedidos/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny # Añadido AllowAny si necesitas alguna vista pública

from django.db import transaction # Para asegurar que las operaciones de BD sean atómicas

# Importamos los MODELOS necesarios
from .models import Order, OrderItem # Modelos de la propia app 'pedidos'
from productos.models import Producto # ¡IMPORTACIÓN CRUCIAL DEL MODELO PRODUCTO!
from tiendas.models import Tienda # ¡IMPORTACIÓN CRUCIAL DEL MODELO TIENDA!
from usuarios.models import Cliente, Direccion # ¡IMPORTACIÓN CRUCIAL DE LOS MODELOS CLIENTE Y DIRECCION!
from django.contrib.auth.models import User # Importar el modelo User de Django

# Importamos los SERIALIZADORES
from .serializers import OrderSerializer, OrderItemSerializer
from rest_framework.serializers import ValidationError # Importar ValidationError directamente


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated] # Solo usuarios autenticados pueden crear/ver sus pedidos

    def get_queryset(self):
        # Un usuario solo puede ver sus propios pedidos o, si es staff/superadmin, todos los pedidos
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        
        # 1. Asegurar que el usuario tiene un perfil de cliente.
        if not hasattr(user, 'cliente'):
            raise ValidationError("El usuario debe tener un perfil de cliente para realizar pedidos.")
        
        cliente_perfil = user.cliente # Obtener el perfil de cliente del usuario

        # Obtener datos de la solicitud
        # Usamos .get() para evitar KeyError si el campo no viene en la solicitud
        delivery_address = self.request.data.get('delivery_address') # Esto es una cadena de texto
        delivery_latitude = self.request.data.get('delivery_latitude')
        delivery_longitude = self.request.data.get('delivery_longitude')
        
        # Obtener la tienda usando el tienda_id que se envía en la solicitud
        tienda_id = self.request.data.get('tienda_id')
        if not tienda_id:
            raise ValidationError("Debe especificar la tienda para el pedido (tienda_id).")
        try:
            tienda = Tienda.objects.get(id=tienda_id)
        except Tienda.DoesNotExist:
            raise ValidationError("La tienda especificada no existe.")

        # Obtener la dirección del cliente si se proporcionó un customer_address_id
        customer_address = None
        customer_address_id = self.request.data.get('customer_address_id')
        if customer_address_id:
            try:
                # Asegurarse de que la dirección pertenece al cliente autenticado
                customer_address = Direccion.objects.get(id=customer_address_id, cliente=cliente_perfil)
            except Direccion.DoesNotExist:
                raise ValidationError("La dirección del cliente especificada no existe o no pertenece a este usuario.")

        # Lógica de cálculo de envío (EJEMPLO - DEBE SER MÁS COMPLEJA EN PRODUCCIÓN)
        # Esto es solo un placeholder, la lógica real implicará cálculos de distancia
        # y radios de envío de la tienda.
        delivery_cost = 0.00 # Aquí deberías calcular el costo de envío real
        # if tienda and delivery_latitude and delivery_longitude:
        #     # Implementar lógica de cálculo de distancia y costo con RadioEnvio de la tienda
        #     # Por ejemplo: calcular_costo_envio(tienda, delivery_latitude, delivery_longitude)
        #     delivery_cost = 5.00 # Ejemplo de costo fijo

        # Procesar items (los items se enviarán como una lista en el JSON en la solicitud POST)
        request_items_data = self.request.data.get('items', []) # Asumiendo que 'items' viene en el body
        
        # Validación básica y cálculo del subtotal
        subtotal_amount = 0
        items_to_create = []
        for item_data in request_items_data:
            product_id = item_data.get('product_id')
            quantity = item_data.get('quantity')
            
            if not product_id or not quantity or quantity <= 0:
                raise ValidationError("Cada ítem del pedido debe tener product_id y quantity válidos.")
            
            try:
                # Asegurarse de que el producto sea de la tienda seleccionada
                product = Producto.objects.get(id=product_id, tienda=tienda)
            except Producto.DoesNotExist:
                raise ValidationError(f"Producto con ID {product_id} no encontrado en la tienda seleccionada.")
            
            if product.stock < quantity:
                raise ValidationError(f"Stock insuficiente para {product.nombre}. Disponible: {product.stock}")
            
            # Lógica para determinar precio (tarjeta/efectivo).
            # Aquí 'True' siempre elige precio_tarjeta. Deberías reemplazar 'True' con tu condición real.
            price_at_purchase = product.precio_tarjeta if True else product.precio_efectivo 
            
            subtotal_amount += price_at_purchase * quantity
            items_to_create.append({'product': product, 'quantity': quantity, 'price_at_purchase': price_at_purchase})
            
        total_amount = subtotal_amount + delivery_cost

        # Guardar la orden y sus ítems en una transacción atómica
        with transaction.atomic():
            order = serializer.save(
                user=user,
                tienda=tienda, # Asignamos el objeto Tienda
                subtotal_amount=subtotal_amount,
                delivery_cost=delivery_cost,
                total_amount=total_amount,
                delivery_address=delivery_address,
                delivery_latitude=delivery_latitude,
                delivery_longitude=delivery_longitude,
                customer_address=customer_address, # Asignamos el objeto Direccion (puede ser None)
                customer_notes=self.request.data.get('customer_notes', ''), # Obtener notas del request
                tienda_notes=self.request.data.get('tienda_notes', ''), # Obtener notas del request
            )
            for item_data in items_to_create:
                OrderItem.objects.create(order=order, **item_data)
                # Opcional: Reducir el stock del producto
                item_data['product'].stock -= item_data['quantity']
                item_data['product'].save()

    # Acción personalizada para cambiar el estado de un pedido (solo para vendedores/admins)
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def change_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')

        if new_status not in [choice[0] for choice in Order.STATUS_CHOICES]:
            return Response({'error': 'Estado de pedido inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar si el usuario tiene permiso para cambiar este estado
        # Por ejemplo, solo el vendedor de la tienda o un admin puede cambiar el estado
        if self.request.user.is_staff or \
           (hasattr(self.request.user, 'perfil_vendedor') and order.tienda.vendedor == self.request.user.perfil_vendedor):
            order.status = new_status
            order.save()
            return Response({'status': f'Estado de pedido cambiado a {new_status}'})
        else:
            return Response({'error': 'No tiene permiso para cambiar el estado de este pedido.'}, status=status.HTTP_403_FORBIDDEN)


class OrderItemViewSet(viewsets.ReadOnlyModelViewSet): # Los OrderItems no deben ser creados/editados directamente
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    # Asegurar que solo se vean los ítems de pedidos propios
    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return OrderItem.objects.all()
        return OrderItem.objects.filter(order__user=self.request.user)
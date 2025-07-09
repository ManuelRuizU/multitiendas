# pedidos/models.py
from django.db import models
# from django.contrib.auth.models import User # Ya no importamos User aquí directamente para el pedido
from tiendas.models import Tienda 
from productos.models import Producto 
from usuarios.models import Cliente, Direccion # ¡Importamos Cliente y Direccion!

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('CONFIRMED', 'Confirmado'),
        ('PREPARING', 'Preparando'),
        ('ON_THE_WAY', 'En camino'),
        ('DELIVERED', 'Entregado'),
        ('CANCELLED', 'Cancelado'),
    ]

    # Vinculamos el pedido directamente al modelo Cliente (que incluye registrados e invitados)
    # on_delete=models.SET_NULL: Si el cliente se elimina, el pedido permanece (pero la relación se anula).
    # related_name='orders': Para acceder a los pedidos desde un objeto Cliente (ej. cliente.orders.all())
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    tienda = models.ForeignKey(Tienda, on_delete=models.PROTECT, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Montos finales del pedido (calculados en el backend al crear/actualizar)
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2) # Este no debería tener default=0.00
    
    # --- ¡CAMBIO CRÍTICO AQUÍ! ---
    # Referencia a la dirección de ENVÍO completa desde tu modelo Direccion
    # on_delete=models.PROTECT: Evita borrar una Direccion si hay pedidos asociados.
    # related_name='orders_as_delivery_address': Nombre más específico.
    delivery_address = models.ForeignKey(
        Direccion,
        on_delete=models.PROTECT, # ¡Muy importante para integridad!
        related_name='orders_as_delivery_address',
        help_text="La dirección completa de envío para este pedido, referenciando el modelo Direccion."
    )

    # Opcional: Dirección de FACTURACIÓN (puede ser la misma que la de envío o diferente)
    # Se referencia el mismo modelo Direccion.
    billing_address = models.ForeignKey(
        Direccion,
        on_delete=models.PROTECT,
        related_name='orders_as_billing_address',
        null=True, blank=True, # Puede ser nulo si no hay una dirección de facturación diferente
        help_text="La dirección de facturación para este pedido (opcional)."
    )
    # --- FIN CAMBIO CRÍTICO ---
    
    # Notas adicionales del cliente o tienda
    customer_notes = models.TextField(blank=True, null=True)
    tienda_notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-order_date']

    def __str__(self):
        # Asegúrate de que cliente no sea None antes de acceder a sus atributos
        cliente_str = self.cliente.__str__() if self.cliente else "Cliente Eliminado"
        return f'Pedido {self.id} de {self.tienda.nombre} - {cliente_str} - {self.status}'

    # Método para calcular el subtotal (ejemplo, la lógica real estará en la vista/serializador)
    # El método calculate_subtotal debería estar en OrderManager o en el serializer/view,
    # ya que order.items.all() solo funcionará después de que el pedido esté guardado.
    # Si lo mantienes aquí, asegúrate de llamarlo después de que los OrderItems se hayan creado.
    def calculate_subtotal(self):
        # Calcula el subtotal sumando los precios totales de los OrderItem.
        # Usa .aggregate() para un cálculo más eficiente a nivel de base de datos.
        from django.db.models import Sum
        total = self.items.aggregate(total_sum=Sum('price_at_purchase', field='quantity * price_at_purchase'))['total_sum']
        return total if total is not None else 0.00
    
    def calculate_total_amount(self):
        # Si tienes lógica de impuestos o descuentos globales, iría aquí.
        return self.subtotal_amount + self.delivery_cost


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Producto, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2) # El precio del producto en el momento de la compra

    class Meta:
        verbose_name = "Ítem de Pedido"
        verbose_name_plural = "Ítems de Pedido"
        unique_together = ('order', 'product') # Un producto solo puede estar una vez en un pedido.

    def get_total_price(self):
        return self.quantity * self.price_at_purchase

    def __str__(self):
        return f'{self.quantity} x {self.product.name} ({self.order.id})'
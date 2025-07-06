# pedidos/models.py
from django.db import models
from django.contrib.auth.models import User # Para el usuario que hace el pedido
from tiendas.models import Tienda # Para la tienda a la que se hace el pedido
from productos.models import Producto # Para los ítems individuales del pedido
from usuarios.models import Direccion # ¡Importamos Direccion desde la app usuarios!

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('CONFIRMED', 'Confirmado'),
        ('PREPARING', 'Preparando'),
        ('ON_THE_WAY', 'En camino'),
        ('DELIVERED', 'Entregado'),
        ('CANCELLED', 'Cancelado'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    tienda = models.ForeignKey(Tienda, on_delete=models.PROTECT, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Montos finales del pedido (calculados en el backend al crear/actualizar)
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Información de dirección de entrega del pedido (captura del momento del pedido)
    delivery_address = models.CharField(max_length=255)
    delivery_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Referencia a la dirección guardada del cliente (opcional, para referencia)
    customer_address = models.ForeignKey(Direccion, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders_made')

    # Notas adicionales del cliente o tienda
    customer_notes = models.TextField(blank=True, null=True)
    tienda_notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-order_date']

    def __str__(self):
        return f'Pedido {self.id} de {self.tienda.nombre} - {self.status}'

    # Método para calcular el subtotal (ejemplo, la lógica real estará en la vista/serializador)
    def calculate_subtotal(self):
        return sum(item.get_total_price() for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Producto, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Ítem de Pedido"
        verbose_name_plural = "Ítems de Pedido"
        unique_together = ('order', 'product')

    def get_total_price(self):
        return self.quantity * self.price_at_purchase

    def __str__(self):
        return f'{self.quantity} x {self.product.name} ({self.order.id})'
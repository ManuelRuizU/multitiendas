# carritos/models.py
from django.db import models
from django.conf import settings
from productos.models import Producto
from django.core.exceptions import ValidationError # Necesario para clean()

class Carrito(models.Model):
    # El carrito puede pertenecer a un usuario registrado O a un usuario anónimo (guest_id).
    # Hacemos 'usuario' nullable.
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carrito',
        null=True,      # Permite que el campo sea nulo en la DB
        blank=True      # Permite que el campo esté vacío en formularios/serializers
    )
    # Identificador único para usuarios no registrados (turistas, etc.).
    # Lo haremos único para evitar colisiones y gestionarlo desde el frontend.
    guest_id = models.CharField(max_length=255, unique=True, null=True, blank=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"
        ordering = ['-fecha_creacion']

    # Validación a nivel de modelo para asegurar que al menos uno de los campos esté presente.
    def clean(self):
        # Un carrito debe estar asociado a un usuario O a un guest_id, pero no a ambos a la vez.
        if self.usuario and self.guest_id:
            raise ValidationError('Un carrito no puede tener un usuario asociado y un guest_id al mismo tiempo.')
        if not self.usuario and not self.guest_id:
            raise ValidationError('Un carrito debe estar asociado a un usuario o a un guest_id.')

    def save(self, *args, **kwargs):
        self.full_clean() # Llama al método clean() para validaciones de modelo.
        super().save(*args, **kwargs)

    def __str__(self):
        if self.usuario:
            return f"Carrito de {self.usuario.username}"
        elif self.guest_id:
            return f"Carrito de Invitado ({self.guest_id[:8]}...)"
        return "Carrito sin propietario" # Caso de fallback, aunque clean() lo evitaría

    @property
    def total_items(self):
        return self.items.count()
    
    @property
    def cantidad_total_productos(self):
        return sum(item.cantidad for item in self.items.all())

    @property
    def subtotal_total(self):
        return sum(item.subtotal for item in self.items.all())


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(
        Carrito,
        on_delete=models.CASCADE,
        related_name='items'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='items_carrito'
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Ítem de Carrito"
        verbose_name_plural = "Ítems de Carrito"
        unique_together = ('carrito', 'producto')
        ordering = ['id']

    def save(self, *args, **kwargs):
        if not self.pk:
            self.precio_unitario = self.producto.precio_efectivo
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en {self.carrito}"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

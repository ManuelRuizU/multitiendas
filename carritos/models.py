# carritos/models.py
from django.db import models
from django.db.models import F, Sum
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from productos.models import Producto
from tiendas.models import Tienda


# ------------------------------------------------------------------
# CONSTANTE: Tiempo de expiración de carritos de invitados
# Los carritos de invitados expiran después de 7 días de inactividad.
# Se puede ajustar según las necesidades del negocio.
# ------------------------------------------------------------------
CARRITO_GUEST_EXPIRACION_DIAS = 7


# ------------------------------------------------------------------
# 1. CARRITO
# ------------------------------------------------------------------
class Carrito(models.Model):

    # --- Propietario del carrito ---
    # Un carrito pertenece a un usuario registrado O a un invitado, nunca a ambos.
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carrito',
        null=True,
        blank=True,
        verbose_name="Usuario registrado"
    )
    guest_id = models.CharField(
        "ID de invitado",
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Identificador único para clientes no registrados. Se gestiona desde el frontend."
    )

    # --- Tienda asociada ---
    # El carrito pertenece a UNA sola tienda.
    # Un cliente no puede mezclar productos de tiendas distintas en el mismo carrito.
    # Si quiere comprar en otra tienda, necesita un carrito distinto.
    tienda = models.ForeignKey(
        Tienda,
        on_delete=models.CASCADE,
        related_name='carritos',
        null=True,
        blank=True,
        verbose_name="Tienda",
        help_text="Tienda a la que pertenecen los productos del carrito."
    )

    # --- Método de pago seleccionado ---
    # Se guarda para calcular el precio correcto (efectivo vs tarjeta).
    METODO_PAGO_CHOICES = [
        ('EFECTIVO',      'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia bancaria'),
        ('LINK_PAGO',     'Link de pago'),
    ]
    metodo_pago = models.CharField(
        "Método de pago",
        max_length=20,
        choices=METODO_PAGO_CHOICES,
        default='EFECTIVO',
        help_text="Método de pago seleccionado. Afecta el precio unitario de los items."
    )

    # --- Fechas ---
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"
        ordering = ['-fecha_creacion']

    # ------------------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------------------
    def clean(self):
        # Un carrito debe pertenecer a un usuario O a un guest_id, nunca a ambos
        if self.usuario and self.guest_id:
            raise ValidationError(
                "Un carrito no puede tener un usuario registrado y un guest_id al mismo tiempo."
            )
        if not self.usuario and not self.guest_id:
            raise ValidationError(
                "Un carrito debe estar asociado a un usuario registrado o a un guest_id."
            )

    def save(self, *args, **kwargs):
        self.full_clean()

        # Detectar cambio de metodo_pago antes de persistir
        metodo_cambio = False
        if self.pk:
            try:
                anterior = Carrito.objects.get(pk=self.pk)
                if anterior.metodo_pago != self.metodo_pago:
                    metodo_cambio = True
            except Carrito.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        if metodo_cambio:
            self.actualizar_precios()

    def __str__(self):
        if self.usuario:
            return f"Carrito de {self.usuario.username} — {self.tienda or 'Sin tienda'}"
        return f"Carrito Invitado ({self.guest_id[:8] if self.guest_id else '?'}...) — {self.tienda or 'Sin tienda'}"

    # ------------------------------------------------------------------
    # PROPIEDADES ÚTILES
    # ------------------------------------------------------------------
    @property
    def total_items(self):
        """Cantidad de productos distintos en el carrito."""
        return self.items.count()

    @property
    def cantidad_total_productos(self):
        """Suma de todas las cantidades de productos en el carrito."""
        result = self.items.aggregate(total=Sum('cantidad'))['total']
        return result or 0

    @property
    def subtotal_total(self):
        """
        Subtotal del carrito usando aggregate con F() para evitar N queries.
        Más eficiente que iterar sobre los items.
        """
        result = self.items.aggregate(
            total=Sum(F('cantidad') * F('precio_unitario'))
        )['total']
        return result or 0

    @property
    def esta_vacio(self):
        """True si el carrito no tiene items."""
        return self.items.count() == 0

    @property
    def es_de_invitado(self):
        """True si el carrito pertenece a un cliente no registrado."""
        return self.guest_id is not None

    @property
    def expirado(self):
        """
        True si el carrito de invitado lleva más de CARRITO_GUEST_EXPIRACION_DIAS
        días sin actividad.
        Los carritos de usuarios registrados nunca expiran.
        """
        if not self.es_de_invitado:
            return False
        limite = timezone.now() - timedelta(days=CARRITO_GUEST_EXPIRACION_DIAS)
        return self.fecha_actualizacion < limite

    # ------------------------------------------------------------------
    # MÉTODOS DE GESTIÓN
    # ------------------------------------------------------------------
    def actualizar_precios(self):
        """
        Actualiza el precio_unitario de todos los items según el método de pago actual.
        Llamar cuando el cliente cambia el método de pago.
        """
        for item in self.items.all():
            if self.metodo_pago in ['EFECTIVO', 'TRANSFERENCIA', 'LINK_PAGO']:
                # Efectivo, transferencia y link de pago usan precio_efectivo
                nuevo_precio = item.producto.precio_efectivo
            else:
                nuevo_precio = item.producto.precio_tarjeta

            if item.precio_unitario != nuevo_precio:
                item.precio_unitario = nuevo_precio
                item.save(update_fields=['precio_unitario'])

    @classmethod
    def limpiar_carritos_expirados(cls):
        """
        Elimina carritos de invitados que llevan más de CARRITO_GUEST_EXPIRACION_DIAS
        días sin actividad.
        Llamar periódicamente desde un cron job o celery beat.

        Ejemplo con django-crontab:
            '0 3 * * *': 'carritos.models.Carrito.limpiar_carritos_expirados'
        """
        limite = timezone.now() - timedelta(days=CARRITO_GUEST_EXPIRACION_DIAS)
        eliminados, _ = cls.objects.filter(
            guest_id__isnull=False,
            fecha_actualizacion__lt=limite
        ).delete()
        return eliminados


# ------------------------------------------------------------------
# 2. ÍTEM DE CARRITO
# ------------------------------------------------------------------
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
    cantidad = models.PositiveIntegerField(
        "Cantidad",
        default=1
    )
    precio_unitario = models.DecimalField(
        "Precio unitario",
        max_digits=10,
        decimal_places=0,
        help_text="Precio al momento de agregar al carrito según el método de pago seleccionado."
    )

    class Meta:
        verbose_name = "Ítem de Carrito"
        verbose_name_plural = "Ítems de Carrito"
        unique_together = ('carrito', 'producto')
        ordering = ['id']

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en {self.carrito}"

    # ------------------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------------------
    def clean(self):
        # Validar que el producto pertenece a la tienda del carrito
        if self.carrito.tienda and self.producto.tienda != self.carrito.tienda:
            raise ValidationError(
                f"El producto '{self.producto.nombre}' no pertenece a la tienda "
                f"'{self.carrito.tienda.nombre}'. No se pueden mezclar productos de distintas tiendas."
            )

        # Validar stock disponible (solo si el producto no tiene stock ilimitado)
        if not self.producto.stock_ilimitado:
            if self.cantidad > self.producto.stock:
                raise ValidationError(
                    f"No hay suficiente stock de '{self.producto.nombre}'. "
                    f"Stock disponible: {self.producto.stock}."
                )

        # Validar que el producto esté disponible
        if not self.producto.disponible:
            raise ValidationError(
                f"El producto '{self.producto.nombre}' no está disponible actualmente."
            )

    def save(self, *args, **kwargs):
        # Asignar tienda al carrito si aún no tiene una
        if not self.carrito.tienda_id:
            self.carrito.tienda = self.producto.tienda
            self.carrito.save(update_fields=['tienda'])

        # Asignar precio según método de pago del carrito
        if not self.pk:
            metodo = self.carrito.metodo_pago
            if metodo in ['EFECTIVO', 'TRANSFERENCIA', 'LINK_PAGO']:
                self.precio_unitario = self.producto.precio_efectivo
            else:
                self.precio_unitario = self.producto.precio_tarjeta

        self.full_clean()
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # PROPIEDADES
    # ------------------------------------------------------------------
    @property
    def subtotal(self):
        """Precio total del ítem: cantidad × precio unitario."""
        return self.cantidad * self.precio_unitario

    @property
    def stock_suficiente(self):
        """
        True si hay stock suficiente para la cantidad solicitada.
        Útil para verificar antes de convertir el carrito en pedido.
        """
        if self.producto.stock_ilimitado:
            return True
        return self.cantidad <= self.producto.stock

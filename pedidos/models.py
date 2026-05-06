# pedidos/models.py
from django.db import models
from django.db.models import F, Sum
from django.utils import timezone
from tiendas.models import Tienda
from productos.models import Producto
from usuarios.models import Cliente, Direccion


# ------------------------------------------------------------------
# 1. PEDIDO (Order)
# ------------------------------------------------------------------
class Order(models.Model):

    # --- Estados del pedido ---
    # El flujo normal es: PENDING → CONFIRMED → PREPARING → ON_THE_WAY → DELIVERED
    # En cualquier momento el emprendedor puede CANCELAR.
    STATUS_CHOICES = [
        ('PENDING',     'Pendiente'),    # Recién creado, mensaje enviado al WhatsApp del emprendedor
        ('CONFIRMED',   'Confirmado'),   # Emprendedor confirmó → se notifica al repartidor
        ('PREPARING',   'Preparando'),   # En preparación en el local
        ('ON_THE_WAY',  'En camino'),    # Repartidor en camino (solo aplica a REPARTO)
        ('DELIVERED',   'Entregado'),    # Entregado o retirado exitosamente
        ('CANCELLED',   'Cancelado'),    # Cancelado por el emprendedor o el cliente
    ]

    # --- Tipo de entrega ---
    TIPO_ENTREGA_CHOICES = [
        ('REPARTO', 'Despacho a domicilio'),
        ('RETIRO',  'Retiro en local'),
    ]

    # --- Método de pago elegido por el cliente ---
    # Debe coincidir con los métodos activos en la tienda.
    METODO_PAGO_CHOICES = [
        ('EFECTIVO',      'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia bancaria'),
        ('LINK_PAGO',     'Link de pago'),
    ]

    # ------------------------------------------------------------------
    # RELACIONES PRINCIPALES
    # ------------------------------------------------------------------
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name="Cliente"
    )
    tienda = models.ForeignKey(
        Tienda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name="Tienda"
    )

    # ------------------------------------------------------------------
    # FECHAS Y ESTADO
    # ------------------------------------------------------------------
    order_date = models.DateTimeField(
        "Fecha del pedido",
        default=timezone.now
    )
    status = models.CharField(
        "Estado",
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    # Fecha en que el emprendedor confirmó el pedido
    confirmed_at = models.DateTimeField(
        "Confirmado el",
        null=True,
        blank=True
    )
    # Fecha en que se marcó como entregado o cancelado
    closed_at = models.DateTimeField(
        "Cerrado el",
        null=True,
        blank=True
    )

    # ------------------------------------------------------------------
    # TIPO DE ENTREGA Y MÉTODO DE PAGO
    # ------------------------------------------------------------------
    tipo_entrega = models.CharField(
        "Tipo de entrega",
        max_length=10,
        choices=TIPO_ENTREGA_CHOICES,
        default='REPARTO',
        help_text="Despacho a domicilio o retiro en el local."
    )
    metodo_pago = models.CharField(
        "Método de pago",
        max_length=20,
        choices=METODO_PAGO_CHOICES,
        default='EFECTIVO',
        help_text="Método de pago seleccionado por el cliente."
    )

    # ------------------------------------------------------------------
    # DIRECCIÓN
    # Obligatoria tanto para REPARTO como RETIRO.
    # Para RETIRO: se usa para el ticket de Loyverse (requerido por el sistema).
    # Para REPARTO: se usa además para calcular el costo de envío y guiar al repartidor.
    # ------------------------------------------------------------------
    delivery_address = models.ForeignKey(
        Direccion,
        on_delete=models.SET_NULL,
        related_name='orders_as_delivery_address',
        null=True,
        blank=True,
        verbose_name="Dirección del cliente",
        help_text=(
            "Dirección del cliente. Obligatoria para REPARTO y RETIRO "
            "(requerida para el ticket de Loyverse)."
        )
    )
    billing_address = models.ForeignKey(
        Direccion,
        on_delete=models.SET_NULL,
        related_name='orders_as_billing_address',
        null=True,
        blank=True,
        verbose_name="Dirección de facturación",
        help_text="Opcional. Solo si la dirección de facturación es distinta a la de envío."
    )

    # ------------------------------------------------------------------
    # MONTOS
    # Precios en pesos chilenos, sin decimales.
    # ------------------------------------------------------------------
    subtotal_amount = models.DecimalField(
        "Subtotal",
        max_digits=10,
        decimal_places=0,
        default=0
    )
    delivery_cost = models.DecimalField(
        "Costo de envío",
        max_digits=10,
        decimal_places=0,
        default=0,
        help_text="0 si es RETIRO en local o si el envío es gratuito según radio o cuadrante."
    )
    total_amount = models.DecimalField(
        "Total",
        max_digits=10,
        decimal_places=0,
        default=0
    )

    # ------------------------------------------------------------------
    # NOTAS
    # ------------------------------------------------------------------
    customer_notes = models.TextField(
        "Notas del cliente",
        blank=True,
        null=True,
        help_text="Instrucciones del cliente. Ej: 'Sin cebolla', 'Timbre roto, llamar al llegar'."
    )
    tienda_notes = models.TextField(
        "Notas internas",
        blank=True,
        null=True,
        help_text="Notas internas del emprendedor sobre este pedido. No las ve el cliente."
    )

    # ------------------------------------------------------------------
    # INTEGRACIÓN CON LOYVERSE
    # Campos preparados para la integración automática en V2.
    # El token de Loyverse se obtiene desde tienda.loyverse_token.
    #
    # IMPORTANTE (V2): loyverse_token en Tienda debe encriptarse
    # usando django-encrypted-model-fields o similar antes de producción.
    # ------------------------------------------------------------------
    loyverse_receipt_id = models.CharField(
        "ID receipt Loyverse",
        max_length=100,
        blank=True,
        null=True,
        help_text="ID del receipt creado en Loyverse para este pedido."
    )
    loyverse_synced = models.BooleanField(
        "Sincronizado con Loyverse",
        default=False,
        help_text="True cuando el pedido fue enviado exitosamente a Loyverse."
    )
    loyverse_synced_at = models.DateTimeField(
        "Sincronizado el",
        null=True,
        blank=True,
        help_text="Fecha y hora en que se sincronizó con Loyverse."
    )
    loyverse_sync_error = models.TextField(
        "Error de sincronización",
        blank=True,
        null=True,
        help_text="Guarda el mensaje de error si la sincronización con Loyverse falló. Útil para debugging."
    )

    # ------------------------------------------------------------------
    # META
    # ------------------------------------------------------------------
    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-order_date']

    def __str__(self):
        cliente_str = str(self.cliente) if self.cliente else "Cliente Eliminado"
        tienda_str = self.tienda.nombre if self.tienda else "Tienda Eliminada"
        return f"Pedido #{self.id} | {tienda_str} | {cliente_str} | {self.get_status_display()}"

    # ------------------------------------------------------------------
    # CÁLCULO DE MONTOS
    # ------------------------------------------------------------------
    def calculate_subtotal(self):
        """
        Calcula el subtotal sumando quantity * price_at_purchase de todos los items.
        Usa F() expressions para operar entre campos del modelo correctamente.
        """
        result = self.items.aggregate(
            total_sum=Sum(F('quantity') * F('price_at_purchase'))
        )['total_sum']
        return result if result is not None else 0

    def calculate_total_amount(self):
        """Total = subtotal + costo de envío."""
        return self.subtotal_amount + self.delivery_cost

    def save(self, *args, **kwargs):
        # RETIRO en local siempre tiene costo de envío 0
        if self.tipo_entrega == 'RETIRO':
            self.delivery_cost = 0

        # Registrar fecha de confirmación
        if self.status == 'CONFIRMED' and not self.confirmed_at:
            self.confirmed_at = timezone.now()

        # Registrar fecha de cierre
        if self.status in ['DELIVERED', 'CANCELLED'] and not self.closed_at:
            self.closed_at = timezone.now()

        if not self.pk:
            # Primera vez que se guarda: necesitamos el pk para acceder a los items
            super().save(*args, **kwargs)
            self.subtotal_amount = self.calculate_subtotal()
            self.total_amount = self.calculate_total_amount()
            super().save(update_fields=['subtotal_amount', 'total_amount'])
        else:
            self.subtotal_amount = self.calculate_subtotal()
            self.total_amount = self.calculate_total_amount()
            super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # PROPIEDADES ÚTILES
    # ------------------------------------------------------------------
    @property
    def es_reparto(self):
        return self.tipo_entrega == 'REPARTO'

    @property
    def loyverse_listo(self):
        """
        Verifica si el pedido tiene todo lo necesario para sincronizar con Loyverse.
        Útil para mostrar el botón de sincronización en el panel del emprendedor.
        """
        return (
            self.status == 'CONFIRMED' and
            not self.loyverse_synced and
            self.tienda and
            self.tienda.loyverse_activo and
            bool(self.tienda.loyverse_token)
        )

    @property
    def resumen_whatsapp(self):
        """
        Genera el texto completo del pedido para enviar al WhatsApp del emprendedor.
        Se llama automáticamente cuando el cliente confirma el pedido.
        """
        tienda = self.tienda
        cliente = self.cliente
        lineas = []

        lineas.append(f"🛒 *NUEVO PEDIDO #{self.id}*")
        lineas.append(f"📅 {self.order_date.strftime('%d/%m/%Y %H:%M')}")
        lineas.append("")

        # Cliente
        lineas.append("👤 *Cliente:*")
        if cliente:
            if cliente.user:
                lineas.append(f"Nombre: {cliente.user.get_full_name() or cliente.user.username}")
                lineas.append(f"Email: {cliente.user.email or 'N/A'}")
            else:
                nombre = f"{cliente.first_name or ''} {cliente.last_name or ''}".strip()
                lineas.append(f"Nombre: {nombre or 'Invitado'}")
                lineas.append(f"Email: {cliente.email or 'N/A'}")
            lineas.append(f"Teléfono: {cliente.telefono or 'N/A'}")
        lineas.append("")

        # Tipo de entrega y dirección
        lineas.append(f"🚚 *Entrega:* {self.get_tipo_entrega_display()}")
        if self.delivery_address:
            d = self.delivery_address
            lineas.append(f"📍 *Dirección:*")
            lineas.append(f"{d.calle} {d.numero}")
            if d.tipo_propiedad in ['Edificio', 'Condominio']:
                if d.nombre_condominio:
                    lineas.append(f"Condominio: {d.nombre_condominio}")
                if d.block:
                    lineas.append(f"Block: {d.block}")
                if d.departamento:
                    lineas.append(f"Depto: {d.departamento}")
            lineas.append(f"{d.comuna}, {d.ciudad}")
            if d.latitud and d.longitud:
                lineas.append(f"📌 Maps: https://maps.google.com/?q={d.latitud},{d.longitud}")
        lineas.append("")

        # Items del pedido
        lineas.append("🧾 *Detalle del pedido:*")
        for item in self.items.all():
            nombre_producto = item.product.nombre if item.product else "Producto eliminado"
            lineas.append(f"• {item.quantity} x {nombre_producto} — ${item.price_at_purchase:,.0f}")
        lineas.append("")

        # Montos
        lineas.append(f"💰 Subtotal: ${self.subtotal_amount:,.0f}")
        if self.es_reparto:
            lineas.append(f"🚗 Envío: ${self.delivery_cost:,.0f}")
        lineas.append(f"✅ *TOTAL: ${self.total_amount:,.0f}*")
        lineas.append("")

        # Método de pago
        lineas.append(f"💳 *Pago:* {self.get_metodo_pago_display()}")
        if self.metodo_pago == 'TRANSFERENCIA' and tienda:
            datos = tienda.datos_transferencia_whatsapp
            if datos:
                lineas.append(datos)
        elif self.metodo_pago == 'LINK_PAGO' and tienda and tienda.link_pago_url:
            lineas.append(f"🔗 Link de pago: {tienda.link_pago_url}")
            if tienda.instrucciones_link_pago:
                lineas.append(f"ℹ️ {tienda.instrucciones_link_pago}")
        lineas.append("")

        # Notas del cliente
        if self.customer_notes:
            lineas.append(f"📝 *Notas del cliente:* {self.customer_notes}")

        return "\n".join(lineas)


# ------------------------------------------------------------------
# 2. ÍTEM DE PEDIDO (OrderItem)
# ------------------------------------------------------------------
class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Pedido"
    )
    product = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Producto"
    )
    quantity = models.PositiveIntegerField(
        "Cantidad",
        default=1
    )
    price_at_purchase = models.DecimalField(
        "Precio al momento de la compra",
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        help_text=(
            "Precio unitario al momento de realizar el pedido. "
            "Se guarda para que cambios futuros en el producto no afecten pedidos históricos."
        )
    )
    # Nombre del producto al momento de la compra
    # Por si el producto se elimina en el futuro, igual queda el nombre en el pedido
    product_name_snapshot = models.CharField(
        "Nombre del producto",
        max_length=150,
        blank=True,
        null=True,
        help_text="Nombre del producto al momento del pedido. Se preserva aunque el producto sea eliminado."
    )

    class Meta:
        verbose_name = "Ítem de Pedido"
        verbose_name_plural = "Ítems de Pedido"

    def __str__(self):
        nombre = self.product_name_snapshot or (self.product.nombre if self.product else "Producto Eliminado")
        return f"{self.quantity} x {nombre} (Pedido #{self.order.id})"

    def get_total_price(self):
        """Precio total del ítem: cantidad × precio unitario."""
        if self.price_at_purchase is not None:
            return self.quantity * self.price_at_purchase
        return 0

    def save(self, *args, **kwargs):
        # Guardar precio actual del producto si no se especificó
        if self.price_at_purchase is None and self.product:
            self.price_at_purchase = self.product.precio_efectivo

        # Guardar snapshot del nombre del producto
        if not self.product_name_snapshot and self.product:
            self.product_name_snapshot = self.product.nombre

        super().save(*args, **kwargs)

# carritos/models.py
from django.db import models
from django.db.models import F, Sum
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from productos.models import Producto
from tiendas.models import Tienda


CARRITO_GUEST_EXPIRACION_DIAS = 7


# ------------------------------------------------------------------
# 1. CARRITO
# El carrito pertenece al cliente (registrado o invitado).
# Puede contener productos de MÚLTIPLES tiendas.
# Cada tienda tiene su propio GrupoCarrito con configuración independiente.
# ------------------------------------------------------------------
class Carrito(models.Model):

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
        help_text="Identificador único para clientes no registrados."
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"
        ordering = ['-fecha_creacion']

    def clean(self):
        if self.usuario and self.guest_id:
            raise ValidationError(
                "Un carrito no puede tener usuario y guest_id al mismo tiempo."
            )
        if not self.usuario and not self.guest_id:
            raise ValidationError(
                "Un carrito debe estar asociado a un usuario o a un guest_id."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.usuario:
            return f"Carrito de {self.usuario.username}"
        return f"Carrito Invitado ({self.guest_id[:8] if self.guest_id else '?'}...)"

    # ------------------------------------------------------------------
    # PROPIEDADES GLOBALES DEL CARRITO (suma de todas las tiendas)
    # ------------------------------------------------------------------
    @property
    def total_tiendas(self):
        """Cantidad de tiendas distintas en el carrito."""
        return self.grupos.count()

    @property
    def esta_vacio(self):
        """True si el carrito no tiene ningún grupo con items."""
        return not self.grupos.filter(items__isnull=False).exists()

    @property
    def subtotal_global(self):
        """Suma de subtotales de todas las tiendas."""
        return sum(g.subtotal for g in self.grupos.all())

    @property
    def costo_envio_global(self):
        """Suma de costos de envío de todas las tiendas."""
        return sum(g.costo_envio or 0 for g in self.grupos.all())

    @property
    def total_global(self):
        """Total general incluyendo todos los envíos."""
        return self.subtotal_global + self.costo_envio_global

    @property
    def es_de_invitado(self):
        return self.guest_id is not None

    @property
    def expirado(self):
        if not self.es_de_invitado:
            return False
        limite = timezone.now() - timedelta(days=CARRITO_GUEST_EXPIRACION_DIAS)
        return self.fecha_actualizacion < limite

    @property
    def tiene_retiros_simultaneos(self):
        """
        Detecta si hay dos o más retiros en local a la misma hora sugerida.
        Útil para advertir al cliente que es físicamente imposible estar en dos lugares.
        """
        retiros = self.grupos.filter(
            tipo_entrega='RETIRO',
            hora_sugerida_cliente__isnull=False
        ).values_list('hora_sugerida_cliente', flat=True)

        horas = list(retiros)
        return len(horas) != len(set(horas))

    @classmethod
    def limpiar_carritos_expirados(cls):
        """Elimina carritos de invitados viejos. Ejecutar con cron job."""
        limite = timezone.now() - timedelta(days=CARRITO_GUEST_EXPIRACION_DIAS)
        eliminados, _ = cls.objects.filter(
            guest_id__isnull=False,
            fecha_actualizacion__lt=limite
        ).delete()
        return eliminados


# ------------------------------------------------------------------
# 2. GRUPO DE CARRITO (una por tienda)
# Cada grupo tiene su propia configuración:
# método de pago, tipo de entrega, hora sugerida, dirección, costo envío.
# ------------------------------------------------------------------
class GrupoCarrito(models.Model):

    METODO_PAGO_CHOICES = [
        ('EFECTIVO',      'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia bancaria'),
        ('LINK_PAGO',     'Link de pago'),
    ]

    TIPO_ENTREGA_CHOICES = [
        ('REPARTO', 'Despacho a domicilio'),
        ('RETIRO',  'Retiro en local'),
    ]

    carrito = models.ForeignKey(
        Carrito,
        on_delete=models.CASCADE,
        related_name='grupos',
        verbose_name="Carrito"
    )
    tienda = models.ForeignKey(
        Tienda,
        on_delete=models.CASCADE,
        related_name='grupos_carrito',
        verbose_name="Tienda"
    )

    # --- Configuración de entrega ---
    tipo_entrega = models.CharField(
        "Tipo de entrega",
        max_length=10,
        choices=TIPO_ENTREGA_CHOICES,
        default='REPARTO'
    )

    # --- Dirección de entrega ---
    # FK a Direccion del cliente — obligatoria para REPARTO y RETIRO
    # (para RETIRO se usa para el ticket de Loyverse)
    from usuarios.models import Direccion
    direccion_entrega = models.ForeignKey(
        Direccion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='grupos_carrito',
        verbose_name="Dirección de entrega"
    )

    # --- Costo de envío calculado ---
    costo_envio = models.DecimalField(
        "Costo de envío",
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        help_text="Se calcula automáticamente según radio/cuadrante. 0 si es retiro o envío gratis."
    )

    # --- Método de pago (independiente por tienda) ---
    metodo_pago = models.CharField(
        "Método de pago",
        max_length=20,
        choices=METODO_PAGO_CHOICES,
        default='EFECTIVO',
        help_text="Cada tienda puede tener un método de pago diferente."
    )

    # --- Hora de entrega ---
    # El cliente sugiere → el emprendedor confirma o modifica via WhatsApp
    hora_sugerida_cliente = models.TimeField(
        "Hora sugerida por el cliente",
        null=True,
        blank=True,
        help_text="Hora preferida de entrega o retiro sugerida por el cliente."
    )
    hora_confirmada = models.TimeField(
        "Hora confirmada por el emprendedor",
        null=True,
        blank=True,
        help_text=(
            "Hora confirmada por el emprendedor via WhatsApp. "
            "Puede diferir de la sugerida si el local tiene alta demanda."
        )
    )

    # --- Notas del cliente para esta tienda ---
    notas_cliente = models.TextField(
        "Notas del cliente",
        blank=True,
        null=True,
        help_text="Instrucciones específicas para esta tienda. Ej: 'Sin cebolla', 'Timbre roto'."
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Grupo de Carrito"
        verbose_name_plural = "Grupos de Carrito"
        unique_together = ('carrito', 'tienda')
        ordering = ['tienda__nombre']

    def __str__(self):
        return f"{self.carrito} → {self.tienda.nombre}"

    # ------------------------------------------------------------------
    # PROPIEDADES
    # ------------------------------------------------------------------
    @property
    def subtotal(self):
        """Subtotal de todos los items de esta tienda."""
        result = self.items.aggregate(
            total=Sum(F('cantidad') * F('precio_unitario'))
        )['total']
        return result or 0

    @property
    def total(self):
        """Total incluyendo costo de envío."""
        return self.subtotal + (self.costo_envio or 0)

    @property
    def total_items(self):
        """Cantidad de productos distintos en este grupo."""
        return self.items.count()

    @property
    def cantidad_total_productos(self):
        """Suma de cantidades de todos los items."""
        result = self.items.aggregate(total=Sum('cantidad'))['total']
        return result or 0

    @property
    def hora_entrega_display(self):
        """
        Retorna la hora confirmada si existe, sino la sugerida.
        Útil para mostrar en la UI del cliente.
        """
        if self.hora_confirmada:
            return self.hora_confirmada
        return self.hora_sugerida_cliente

    @property
    def hora_modificada_por_emprendedor(self):
        """True si el emprendedor modificó la hora sugerida por el cliente."""
        return (
            self.hora_confirmada is not None and
            self.hora_sugerida_cliente is not None and
            self.hora_confirmada != self.hora_sugerida_cliente
        )

    # ------------------------------------------------------------------
    # MÉTODOS
    # ------------------------------------------------------------------
    def actualizar_precios(self):
        """
        Recalcula precios de todos los items según el método de pago actual.
        Llamar cuando el cliente cambia el método de pago del grupo.
        """
        for item in self.items.all():
            if self.metodo_pago == 'TARJETA':
                nuevo_precio = item.producto.precio_tarjeta
            else:
                nuevo_precio = item.producto.precio_efectivo

            if item.precio_unitario != nuevo_precio:
                item.precio_unitario = nuevo_precio
                item.save(update_fields=['precio_unitario'])

    def calcular_costo_envio(self, lat=None, lng=None):
        """
        Calcula y guarda el costo de envío para este grupo.
        Usa la dirección del grupo si no se pasan coordenadas.
        """
        if self.tipo_entrega == 'RETIRO':
            self.costo_envio = 0
            self.save(update_fields=['costo_envio'])
            return 0

        # Usar coordenadas de la dirección si no se pasan
        if not lat or not lng:
            if self.direccion_entrega and \
                    self.direccion_entrega.latitud and \
                    self.direccion_entrega.longitud:
                lat = float(self.direccion_entrega.latitud)
                lng = float(self.direccion_entrega.longitud)
            else:
                return None

        costo = self.tienda.calcular_costo_envio(lat, lng)
        self.costo_envio = costo
        self.save(update_fields=['costo_envio'])
        return costo

    @property
    def resumen_whatsapp(self):
        """
        Genera el mensaje de WhatsApp para esta tienda específica.
        Se llama al confirmar el pedido.
        """
        carrito = self.carrito
        lineas = []

        lineas.append(f"🛒 *NUEVO PEDIDO*")
        lineas.append(f"📅 {timezone.now().strftime('%d/%m/%Y %H:%M')}")
        lineas.append("")

        # Cliente
        lineas.append("👤 *Cliente:*")
        if carrito.usuario:
            u = carrito.usuario
            nombre = u.get_full_name() or u.username
            lineas.append(f"Nombre: {nombre}")
            lineas.append(f"Email: {u.email or 'N/A'}")
            if hasattr(u, 'cliente_data'):
                lineas.append(f"Teléfono: {u.cliente_data.telefono or 'N/A'}")
        else:
            lineas.append(f"Cliente invitado (ID: {str(carrito.guest_id)[:8]}...)")
        lineas.append("")

        # Entrega
        lineas.append(f"🚚 *Entrega:* {self.get_tipo_entrega_display()}")
        if self.hora_sugerida_cliente:
            lineas.append(f"⏰ Hora sugerida: {self.hora_sugerida_cliente.strftime('%H:%M')}")
        if self.direccion_entrega:
            d = self.direccion_entrega
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
                lineas.append(
                    f"📌 Maps: https://maps.google.com/?q={d.latitud},{d.longitud}"
                )
        lineas.append("")

        # Items
        lineas.append("🧾 *Detalle del pedido:*")
        for item in self.items.all():
            lineas.append(
                f"• {item.cantidad} x {item.producto.nombre} — ${item.precio_unitario:,.0f}"
            )
        lineas.append("")

        # Montos
        lineas.append(f"💰 Subtotal: ${self.subtotal:,.0f}")
        if self.tipo_entrega == 'REPARTO':
            costo = self.costo_envio if self.costo_envio is not None else '?'
            lineas.append(f"🚗 Envío: ${costo:,.0f}" if isinstance(costo, (int, float)) else f"🚗 Envío: {costo}")
        lineas.append(f"✅ *TOTAL: ${self.total:,.0f}*")
        lineas.append("")

        # Método de pago
        lineas.append(f"💳 *Pago:* {self.get_metodo_pago_display()}")
        if self.metodo_pago == 'TRANSFERENCIA':
            datos = self.tienda.datos_transferencia_whatsapp
            if datos:
                lineas.append(datos)
        elif self.metodo_pago == 'LINK_PAGO' and self.tienda.link_pago_url:
            lineas.append(f"🔗 Link de pago: {self.tienda.link_pago_url}")
            if self.tienda.instrucciones_link_pago:
                lineas.append(f"ℹ️ {self.tienda.instrucciones_link_pago}")
        lineas.append("")

        # Notas
        if self.notas_cliente:
            lineas.append(f"📝 *Notas:* {self.notas_cliente}")

        return "\n".join(lineas)


# ------------------------------------------------------------------
# 3. ÍTEM DE CARRITO
# Ahora pertenece a un GrupoCarrito (no directamente al Carrito)
# ------------------------------------------------------------------
class ItemCarrito(models.Model):
    grupo = models.ForeignKey(
        GrupoCarrito,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Grupo de carrito"
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='items_carrito'
    )
    cantidad = models.PositiveIntegerField("Cantidad", default=1)
    precio_unitario = models.DecimalField(
        "Precio unitario",
        max_digits=10,
        decimal_places=0,
        help_text="Precio al momento de agregar según el método de pago del grupo."
    )

    class Meta:
        verbose_name = "Ítem de Carrito"
        verbose_name_plural = "Ítems de Carrito"
        unique_together = ('grupo', 'producto')
        ordering = ['id']

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} → {self.grupo.tienda.nombre}"

    def clean(self):
        # Validar que el producto pertenece a la tienda del grupo
        if self.producto.tienda != self.grupo.tienda:
            raise ValidationError(
                f"El producto '{self.producto.nombre}' no pertenece a "
                f"'{self.grupo.tienda.nombre}'."
            )
        # Validar stock
        if not self.producto.stock_ilimitado:
            if self.cantidad > self.producto.stock:
                raise ValidationError(
                    f"Stock insuficiente de '{self.producto.nombre}'. "
                    f"Disponible: {self.producto.stock}."
                )
        # Validar disponibilidad
        if not self.producto.disponible:
            raise ValidationError(
                f"El producto '{self.producto.nombre}' no está disponible."
            )

    def save(self, *args, **kwargs):
        # Asignar precio según método de pago del grupo
        if not self.pk:
            if self.grupo.metodo_pago == 'TARJETA':
                self.precio_unitario = self.producto.precio_tarjeta
            else:
                self.precio_unitario = self.producto.precio_efectivo
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    @property
    def stock_suficiente(self):
        if self.producto.stock_ilimitado:
            return True
        return self.cantidad <= self.producto.stock
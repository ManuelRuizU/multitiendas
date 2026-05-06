# productos/models.py
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from tiendas.models import Tienda

import qrcode
import json
from io import BytesIO
from django.core.files.base import ContentFile


# ------------------------------------------------------------------
# 1. CATEGORÍAS
# ------------------------------------------------------------------
class Categoria(models.Model):
    tienda = models.ForeignKey(
        Tienda,
        on_delete=models.CASCADE,
        related_name="categorias"
    )
    nombre = models.CharField(max_length=100)
    orden_display = models.PositiveIntegerField(
        "Orden de visualización",
        default=0,
        help_text="Controla el orden en que aparece la categoría en la tienda. Menor número = primero."
    )

    class Meta:
        unique_together = ("tienda", "nombre")
        ordering = ["orden_display", "nombre"]
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return f"{self.nombre} ({self.tienda.nombre})"


# ------------------------------------------------------------------
# 2. SUBCATEGORÍAS
# ------------------------------------------------------------------
class SubCategoria(models.Model):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name="subcategorias"
    )
    nombre = models.CharField(max_length=120)
    orden_display = models.PositiveIntegerField(
        "Orden de visualización",
        default=0,
        help_text="Controla el orden en que aparece la subcategoría. Menor número = primero."
    )

    class Meta:
        unique_together = ("categoria", "nombre")
        ordering = ["orden_display", "nombre"]
        verbose_name = "Subcategoría"
        verbose_name_plural = "Subcategorías"

    def __str__(self):
        return f"{self.nombre} ({self.categoria.nombre})"


# ------------------------------------------------------------------
# 3. PRODUCTOS
# ------------------------------------------------------------------
class Producto(models.Model):
    tienda = models.ForeignKey(
        Tienda,
        on_delete=models.CASCADE,
        related_name="productos"
    )
    subcategoria = models.ForeignKey(
        SubCategoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="productos"
    )

    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(
        "Descripción corta",
        blank=True,
        help_text="Aparece en la tarjeta y el modal de producto (máx. 300 caracteres)."
    )

    # --- Identificadores ---
    sku = models.CharField(
        "SKU",
        max_length=50,
        blank=True,
        null=True,
        help_text="Identificador único del producto dentro de la tienda. Ej: SKU_ALF_CHOC_001."
    )
    codigo_barras_oficial = models.CharField(
        "Código de Barras GTIN/EAN/UPC",
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        help_text="Código de barras oficial del producto. Único a nivel global en la plataforma."
    )

    # --- Precios en pesos chilenos, sin decimales ---
    precio_efectivo = models.DecimalField(
        "Precio efectivo / transferencia",
        max_digits=10,
        decimal_places=0,
        help_text="Precio para pagos en efectivo o transferencia."
    )
    precio_tarjeta = models.DecimalField(
        "Precio tarjeta débito/crédito",
        max_digits=10,
        decimal_places=0,
        help_text="Precio con recargo por tarjeta. Si no hay recargo, ingresa el mismo valor que efectivo."
    )

    # --- Stock y disponibilidad ---
    stock = models.PositiveIntegerField(
        "Stock",
        default=0,
        help_text="Cantidad disponible en inventario."
    )
    disponible = models.BooleanField(
        "Disponible",
        default=True,
        help_text=(
            "Controla si el producto se muestra en la tienda. "
            "Se desactiva automáticamente cuando el stock llega a 0."
        )
    )
    stock_ilimitado = models.BooleanField(
        "Stock ilimitado",
        default=False,
        help_text=(
            "Si está activo, el producto nunca se desactiva por falta de stock. "
            "Se activa automáticamente para tiendas de tipo COMIDA o SERVICIOS. "
            "Útil para productos bajo demanda como pizzas, hamburguesas, servicios, etc."
        )
    )

    # --- Imagen y QR ---
    imagen = models.ImageField(
        upload_to="productos/",
        blank=True,
        null=True
    )
    imagen_qr_generado = models.ImageField(
        upload_to="codigos_qr/",
        blank=True,
        null=True,
        help_text="Código QR generado automáticamente por la plataforma para gestión interna."
    )

    # --- Orden de visualización ---
    orden_display = models.PositiveIntegerField(
        "Orden de visualización",
        default=0,
        help_text="Controla el orden en que aparece el producto en la tienda. Menor número = primero."
    )

    # --- Integración con Loyverse (V2) ---
    # Guarda el ID del producto en Loyverse para sincronizar stock automáticamente.
    # IMPORTANTE (V2): al activar la integración, sincronizar productos con Loyverse
    # usando el endpoint POST /v1.0/items de la API de Loyverse.
    loyverse_item_id = models.CharField(
        "ID item en Loyverse",
        max_length=100,
        blank=True,
        null=True,
        help_text="ID del producto en Loyverse. Se completa al sincronizar con la integración."
    )

    class Meta:
        ordering = ["orden_display", "nombre"]
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        unique_together = ("tienda", "sku")

    def __str__(self):
        return f"{self.nombre} — {self.tienda.nombre}"

    # ------------------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------------------
    def clean(self):
        # Precio tarjeta no puede ser menor al precio efectivo
        if self.precio_tarjeta and self.precio_efectivo:
            if self.precio_tarjeta < self.precio_efectivo:
                raise ValidationError({
                    'precio_tarjeta': (
                        "El precio tarjeta no puede ser menor al precio efectivo. "
                        "Si no hay recargo, ingresa el mismo valor."
                    )
                })

    def save(self, *args, **kwargs):
        # Si es un producto nuevo, heredar stock_ilimitado del tipo de negocio de la tienda
        if not self.pk and self.tienda_id:
            # Solo aplicar si no se especificó explícitamente
            # stock_ilimitado viene como False por defecto del modelo,
            # así que solo lo sobreescribimos si la tienda es de tipo COMIDA o SERVICIOS
            if self.tienda.stock_ilimitado_default:
                self.stock_ilimitado = True
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # DISPONIBILIDAD AUTOMÁTICA SEGÚN STOCK
    # ------------------------------------------------------------------
    def actualizar_disponibilidad(self):
        """
        Desactiva el producto automáticamente si el stock llega a 0
        y no tiene stock ilimitado.
        Solo actualiza si es necesario para evitar saves innecesarios.
        """
        if self.stock_ilimitado:
            return

        deberia_estar_disponible = self.stock > 0
        if self.disponible != deberia_estar_disponible:
            self.disponible = deberia_estar_disponible
            self.save(update_fields=['disponible'])

    # ------------------------------------------------------------------
    # GENERACIÓN DE QR
    # ------------------------------------------------------------------
    def _datos_qr(self):
        """Retorna el diccionario de datos a codificar en el QR."""
        return {
            "producto_id": self.pk,
            "tienda_id": self.tienda.pk,
            "sku": self.sku or "N/A",
            "gtin": self.codigo_barras_oficial or "N/A",
        }

    def _qr_necesita_actualizarse(self):
        """
        Verifica si el QR necesita regenerarse comparando los datos actuales
        con los que están guardados en la DB.
        Solo regenera si cambiaron SKU o GTIN — los campos que afectan el QR.
        """
        if not self.pk or not self.imagen_qr_generado:
            return True
        try:
            db_instance = Producto.objects.get(pk=self.pk)
            return (
                db_instance.sku != self.sku or
                db_instance.codigo_barras_oficial != self.codigo_barras_oficial
            )
        except Producto.DoesNotExist:
            return True

    def generate_qr_code(self):
        """
        Genera el código QR del producto y lo guarda en imagen_qr_generado.
        Codifica: producto_id, tienda_id, SKU y GTIN en formato JSON.
        """
        if not self.pk:
            return

        json_data = json.dumps(self._datos_qr(), ensure_ascii=False)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,  # M es más robusto que L
            box_size=10,
            border=4,
        )
        qr.add_data(json_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")

        filename = f'qr_producto_{self.pk}.png'
        self.imagen_qr_generado.save(
            filename,
            ContentFile(buffer.getvalue()),
            save=False
        )
        buffer.close()

    # ------------------------------------------------------------------
    # PROPIEDADES ÚTILES
    # ------------------------------------------------------------------
    @property
    def precio_display(self):
        """Retorna el precio efectivo formateado en pesos chilenos."""
        return f"${self.precio_efectivo:,.0f}"

    @property
    def tiene_recargo_tarjeta(self):
        """True si el precio tarjeta es mayor al precio efectivo."""
        return self.precio_tarjeta > self.precio_efectivo

    @property
    def en_stock(self):
        """True si el producto tiene stock disponible o es de stock ilimitado."""
        return self.stock_ilimitado or self.stock > 0


# ------------------------------------------------------------------
# SEÑALES
# ------------------------------------------------------------------

@receiver(post_save, sender=Producto)
def generar_qr_para_producto(sender, instance, created, **kwargs):
    """
    Genera o regenera el QR del producto:
    - Al crear el producto por primera vez
    - Cuando cambia el SKU o el GTIN (los únicos campos que afectan el QR)
    Evita regeneraciones innecesarias cuando solo cambian otros campos.
    """
    # Evitar bucle infinito — si ya venimos de un update_fields de QR, salimos
    if kwargs.get('update_fields') and 'imagen_qr_generado' in (kwargs.get('update_fields') or []):
        return

    if created or instance._qr_necesita_actualizarse():
        instance.generate_qr_code()
        instance.save(update_fields=['imagen_qr_generado'])


@receiver(post_save, sender=Producto)
def verificar_disponibilidad_por_stock(sender, instance, **kwargs):
    """
    Verifica y actualiza la disponibilidad del producto según su stock
    cada vez que se guarda.
    Evita actuar si ya venimos de un update_fields de disponible.
    """
    if kwargs.get('update_fields') and 'disponible' in (kwargs.get('update_fields') or []):
        return
    instance.actualizar_disponibilidad()
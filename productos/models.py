# productos/models.py
from django.db import models
from django.db.models.signals import post_save # Importamos post_save signal
from django.dispatch import receiver # Para el decorador receiver
from tiendas.models import Tienda

import qrcode # Importa qrcode para generar códigos QR
from io import BytesIO # Necesario para manejar la imagen en memoria
from django.core.files.base import ContentFile # Para guardar la imagen en el ImageField
import uuid # Para generar identificadores únicos si no hay SKU o GTIN

# ------------------------------------------------------------------
# 1. CATEGORÍAS
# ------------------------------------------------------------------
class Categoria(models.Model):
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE, related_name="categorias")
    nombre = models.CharField(max_length=100)

    class Meta:
        unique_together = ("tienda", "nombre") # Nombre de categoría único por tienda
        ordering = ["nombre"]
        verbose_name_plural = "Categorías"

    def __str__(self):
        return f"{self.nombre} ({self.tienda.nombre})"


# ------------------------------------------------------------------
# 2. SUBCATEGORÍAS
# ------------------------------------------------------------------
class SubCategoria(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name="subcategorias")
    nombre = models.CharField(max_length=120)

    class Meta:
        unique_together = ("categoria", "nombre")
        ordering = ["nombre"]
        verbose_name_plural = "Subcategorías"

    def __str__(self):
        return f"{self.nombre} ({self.categoria.nombre})"


# ------------------------------------------------------------------
# 3. PRODUCTOS
# ------------------------------------------------------------------
class Producto(models.Model):
    tienda = models.ForeignKey(
        Tienda, on_delete=models.CASCADE, related_name="productos"
    )
    subcategoria = models.ForeignKey(
        SubCategoria, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="productos"
    )

    nombre = models.CharField(max_length=150)
    
    # Campo SKU - único por tienda
    sku = models.CharField(max_length=50, blank=True, null=True, 
                          help_text="Identificador único del producto dentro de la tienda (ej. SKU_ALF_CHOC_001).") 
    
    # Campo para código de barras oficial (GTIN/EAN/UPC) - Opcional, pero único globalmente si se rellena
    # Es importante que si lo ingresa el vendedor, este sea único para evitar conflictos con productos reales.
    codigo_barras_oficial = models.CharField(
        "Código de Barras GTIN/EAN/UPC",
        max_length=50, 
        blank=True, 
        null=True, 
        unique=True, # Si un GTIN/EAN/UPC se ingresa, debe ser único en toda la plataforma
        help_text="Código de barras oficial (GTIN, EAN, UPC) del producto. Único a nivel global."
    )

    # Campo para almacenar la imagen del Código QR generado por la aplicación (uso interno)
    imagen_qr_generado = models.ImageField(
        upload_to="codigos_qr/", 
        blank=True, 
        null=True,
        help_text="Código QR generado automáticamente por la plataforma para gestión interna."
    )


    descripcion = models.TextField(
        "Descripción corta",
        blank=True,
        help_text="Aparece en la tarjeta y el modal de producto (máx. 300 caracteres)."
    )

    precio_efectivo = models.DecimalField(
        "Precio (efectivo / transferencia)", max_digits=10, decimal_places=0
    )
    precio_tarjeta = models.DecimalField(
        "Precio (tarjeta débito‑crédito)", max_digits=10, decimal_places=0,
        help_text="Si no quieres recargo, pon el mismo valor que en efectivo."
    )

    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)
    disponible = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "Productos"
        unique_together = ("tienda", "sku") # SKU único por tienda

    def __str__(self):
        return f"{self.nombre} — {self.tienda.nombre}"

    # Método para generar el Código QR
    def generate_qr_code(self):
        # Aseguramos que tenemos un ID de producto para codificar
        if not self.pk:
            # Esto no debería pasar si se llama desde un post_save signal
            # o después de la primera guarda, pero es una salvaguarda.
            return 
        
        # El contenido del QR puede ser el SKU, una URL, o un JSON con varios IDs.
        # Una buena práctica es incluir el ID de la tienda y el SKU para unicidad y contexto.
        # Si el SKU es nulo, podemos usar el ID del producto y un UUID para el QR.
        unique_id_for_qr = self.sku if self.sku else str(uuid.uuid4()) # Usamos SKU o UUID como fallback
        
        # Contenido más robusto para el QR:
        data_to_encode = {
            "producto_id": self.pk,
            "tienda_id": self.tienda.pk,
            "sku": self.sku,
            "gtin": self.codigo_barras_oficial or "N/A"
            # Puedes añadir más campos relevantes aquí
        }
        # Codificamos el diccionario como una cadena JSON para el QR
        import json
        json_data = json.dumps(data_to_encode, ensure_ascii=False) # ensure_ascii=False para caracteres especiales

        qr = qrcode.QRCode(
            version=1, # Tamaño del QR, 1 es el más pequeño. Aumenta si codificas muchos datos.
            error_correction=qrcode.constants.ERROR_CORRECT_L, # Nivel de corrección de errores (L, M, Q, H)
            box_size=10, # Tamaño de cada "caja" del QR
            border=4, # Margen alrededor del QR
        )
        qr.add_data(json_data) # Añadimos los datos JSON
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Guardar en un buffer en memoria
        buffer = BytesIO()
        img.save(buffer, format="PNG") # Guarda la imagen PNG en el buffer

        # Guardar la imagen en el campo ImageField
        # Usamos el pk del producto para el nombre del archivo para asegurar unicidad
        filename = f'qr_producto_{self.pk}.png'
        self.imagen_qr_generado.save(filename, ContentFile(buffer.getvalue()), save=False)
        
        buffer.close()

# --- Signal para generar el QR después de guardar el producto ---
# Esto asegura que el producto tenga un ID (pk) asignado para el QR
@receiver(post_save, sender=Producto)
def generar_qr_para_producto(sender, instance, created, **kwargs):
    # Genera el QR solo si se creó el producto, o si el QR aún no existe
    # o si el SKU (que podría ser parte del QR) ha cambiado
    if created or not instance.imagen_qr_generado: # Generar solo si es nuevo o no tiene QR
        instance.generate_qr_code()
        # Guardar la instancia de nuevo, pero solo el campo de imagen_qr_generado
        # para evitar un bucle de guardado infinito.
        instance.save(update_fields=['imagen_qr_generado'])
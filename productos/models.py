# productos/models.py
from django.db import models
from tiendas.models import Tienda # ¡Importamos Tienda desde la app tiendas!

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

    descripcion = models.TextField(
        "Descripción corta",
        blank=True,
        help_text="Aparece en la tarjeta y el modal de producto (máx. 300 caracteres)."
    )

    # Nuevo esquema de precios
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

    def __str__(self):
        return f"{self.nombre} — {self.tienda.nombre}"
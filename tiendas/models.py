# tiendas/models.py
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from usuarios.models import PerfilVendedor # ¡Importamos PerfilVendedor desde la app usuarios!

# ------------------------------------------------------------------
# 1. TIENDA
# ------------------------------------------------------------------
class Tienda(models.Model):
    vendedor = models.ForeignKey(
        PerfilVendedor, on_delete=models.CASCADE, related_name="tiendas"
    )

    nombre = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(unique=True, blank=True, max_length=150)
    descripcion = models.TextField(blank=True)

    # Datos de ubicación
    direccion = models.CharField(max_length=255)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Contacto
    telefono = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    horario_atencion = models.CharField(max_length=255, blank=True, null=True)
    logo = models.ImageField(upload_to="logos_tiendas/", blank=True, null=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "Tiendas"

    # ------------- hooks -------------
    def clean(self):
        """
        Valida que el vendedor tenga su perfil completo ANTES de crear la tienda.
        Se ejecuta desde admin, formularios y save().
        """
        # Solo valida si el vendedor ya existe (para evitar errores en la creación inicial del vendedor)
        if self.vendedor and not self.vendedor.is_complete():
            raise ValidationError(
                "Debes completar todos los datos obligatorios de tu perfil de vendedor "
                "antes de crear una tienda."
            )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nombre)
            slug = base_slug
            counter = 1
            while Tienda.objects.filter(slug=slug).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        
        self.full_clean() # Llama a clean() y a todas las validaciones de campo
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


# ------------------------------------------------------------------
# 2. RADIO DE ENVÍO
# ------------------------------------------------------------------
class RadioEnvio(models.Model):
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE, related_name="radios_envio")
    distancia_max_km = models.DecimalField(max_digits=4, decimal_places=1)
    costo_envio = models.PositiveIntegerField()

    class Meta:
        ordering = ["distancia_max_km"]
        unique_together = ("tienda", "distancia_max_km")
        verbose_name_plural = "Radios de Envío"

    def __str__(self):
        return f"{self.tienda.nombre} → {self.distancia_max_km} km = ${self.costo_envio}"
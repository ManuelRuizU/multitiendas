# usuarios/models.py
from django.db import models
from django.utils.text import slugify # Importado aunque no se usa directamente en este modelo, pero es una buena práctica mantenerlo si se usara en el futuro en otros modelos relacionados con usuarios.
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# ------------------------------------------------------------------
# 1. PERFIL DEL VENDEDOR
# ------------------------------------------------------------------
class PerfilVendedor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_vendedor')
    telefono = models.CharField(max_length=20, blank=True, null=True) # Se permite nulo en BD si no se llena

    # Campos obligatorios ANTES de crear tienda
    rut = models.CharField("RUT / DNI", max_length=12, unique=True, blank=False, null=False) # ¡RUT único y obligatorio!
    razon_social = models.CharField(max_length=150, blank=False, null=False)
    giro = models.CharField("Giro o actividad", max_length=150, blank=False, null=False)
    direccion_fiscal = models.CharField(max_length=255, blank=False, null=False)

    fecha_registro = models.DateTimeField(auto_now_add=True)

    # ---------- utilidades ----------
    OBLIGATORY_FIELDS = ["rut", "razon_social", "giro", "direccion_fiscal", "telefono"]

    def is_complete(self) -> bool:
        """True si todos los campos obligatorios tienen algún valor no vacío/no nulo."""
        return all(getattr(self, f) for f in self.OBLIGATORY_FIELDS if getattr(self, f) is not None and getattr(self, f) != '')

    def clean(self):
        # Validación para campos obligatorios en el modelo mismo, útil para admin/formularios
        for field_name in self.OBLIGATORY_FIELDS:
            if field_name == "telefono" and (self.telefono is None or self.telefono == ''):
                # Si 'telefono' es opcional en el campo pero obligatorio para is_complete,
                # puedes relajar la validación de 'clean' aquí o hacer el campo no blank/null.
                # Para este ejemplo, lo dejaremos como un campo que is_complete revisa.
                pass
            elif not getattr(self, field_name):
                raise ValidationError(f"El campo '{self._meta.get_field(field_name).verbose_name}' es obligatorio.")

    def __str__(self):
        return f"Vendedor: {self.user.username}"


# ------------------------------------------------------------------
# 2. CLIENTE Y DIRECCIÓN
# ------------------------------------------------------------------
class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cliente')
    telefono = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return self.user.username


class Direccion(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="direcciones")
    etiqueta = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.CharField(max_length=255)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    validada = models.BooleanField(default=False)

    class Meta:
        ordering = ["-id"]
        verbose_name_plural = "Direcciones"

    def __str__(self):
        return f"{self.etiqueta or self.direccion} – {self.cliente.user.username}"
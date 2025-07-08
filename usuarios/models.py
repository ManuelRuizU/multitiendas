# usuarios/models.py
from django.db import models
from django.utils.text import slugify 
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# ------------------------------------------------------------------
# 1. PERFIL DEL VENDEDOR
# ------------------------------------------------------------------
class PerfilVendedor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_vendedor')
    telefono = models.CharField(max_length=20, blank=True, null=True) 

    # Campos obligatorios ANTES de crear tienda
    rut = models.CharField("RUT / DNI", max_length=12, unique=True, blank=False, null=False) # ¡RUT único y obligatorio!
    razon_social = models.CharField(max_length=150, blank=False, null=False)
    giro = models.CharField("Giro o actividad", max_length=150, blank=False, null=False)
    direccion_fiscal = models.CharField(max_length=255, blank=False, null=False)

    fecha_registro = models.DateTimeField(auto_now_add=True)

    # ---------- utilidades ----------
    # Incluye 'telefono' aquí si realmente es obligatorio para considerar el perfil "completo"
    # Aunque el campo del modelo permita blank/null, esta lista define la lógica de is_complete
    OBLIGATORY_FIELDS = ["rut", "razon_social", "giro", "direccion_fiscal", "telefono"] 

    def is_complete(self) -> bool:
        """True si todos los campos obligatorios tienen algún valor no vacío/no nulo."""
        # Se asegura de que los campos existan y no estén vacíos (cadenas vacías o None)
        return all(getattr(self, f) for f in self.OBLIGATORY_FIELDS if getattr(self, f) is not None and getattr(self, f) != '')

    def clean(self):
        # Validación en el nivel del modelo, útil para el admin de Django.
        # Asegúrate de que los campos 'blank=False, null=False' no estén vacíos.
        if not self.rut:
            raise ValidationError({'rut': "El RUT / DNI es obligatorio."})
        if not self.razon_social:
            raise ValidationError({'razon_social': "La razón social es obligatoria."})
        if not self.giro:
            raise ValidationError({'giro': "El giro o actividad es obligatorio."})
        if not self.direccion_fiscal:
            raise ValidationError({'direccion_fiscal': "La dirección fiscal es obligatoria."})
        
        # Opcional: Si 'telefono' es obligatorio para el perfil completo, puedes validarlo aquí también.
        # if not self.telefono:
        #     raise ValidationError({'telefono': "El teléfono es obligatorio para completar el perfil."})


    def __str__(self):
        return f"Vendedor: {self.user.username}"


# ------------------------------------------------------------------
# 2. CLIENTE Y DIRECCIÓN (ADAPTADO PARA INVITADOS)
# ------------------------------------------------------------------
class Cliente(models.Model):
    # Relación opcional con el modelo User.
    # Si un cliente es invitado, este campo será NULL.
    # 'related_name' cambia a 'cliente_profile' para evitar un posible conflicto futuro,
    # aunque 'cliente' estaba bien si solo se usa OneToOne.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cliente_profile', null=True, blank=True) 
    
    # Teléfono del cliente. Puede ser proporcionado por invitados o usuarios registrados.
    telefono = models.CharField(max_length=30, blank=True, null=True)

    # Nuevos campos para clientes invitados (o para complementar info de registrados si se desea)
    # Estos campos se llenarán a partir del "formulario de contacto" del carrito.
    email = models.EmailField(max_length=254, blank=True, null=True, unique=False) # Puede no ser único para invitados
    nombre_completo = models.CharField(max_length=100, blank=True, null=True)
    
    # Campo para distinguir fácilmente si es un cliente registrado o invitado
    is_guest = models.BooleanField(default=False) # Se seteará a True si user es null

    class Meta:
        # Añadir un campo de ayuda para la administración o depuración
        # Evitar que un usuario registrado tenga múltiples perfiles de Cliente.
        constraints = [
            models.UniqueConstraint(fields=['user'], condition=models.Q(user__isnull=False), name='unique_cliente_for_user')
        ]
        # Opcional: Para evitar múltiples clientes invitados con el mismo email,
        # aunque es común permitirlo para guest checkout (un invitado podría usar emails de amigos).
        # Si quieres que el email sea único para NO-registrados:
        # models.UniqueConstraint(fields=['email'], condition=models.Q(user__isnull=True), name='unique_guest_email')


    def save(self, *args, **kwargs):
        # Auto-setea is_guest basado en si el campo 'user' está asignado.
        self.is_guest = self.user is None
        # Opcional: Si el email es vacío, establece a None para guardar como NULL en la BD
        if self.email == '':
            self.email = None
        # Opcional: Si el nombre_completo es vacío, establece a None para guardar como NULL en la BD
        if self.nombre_completo == '':
            self.nombre_completo = None
        # Opcional: Si el telefono es vacío, establece a None para guardar como NULL en la BD
        if self.telefono == '':
            self.telefono = None
        
        super().save(*args, **kwargs)

    def __str__(self):
        if self.user:
            return f"Cliente Registrado: {self.user.username} ({self.email or 'N/A'})"
        return f"Cliente Invitado: {self.nombre_completo or self.email or 'N/A'}"


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
        # Ahora el cliente puede no tener un user, así que adaptamos la representación
        cliente_id_str = str(self.cliente.id) 
        if self.cliente.user:
            cliente_id_str = self.cliente.user.username
        elif self.cliente.nombre_completo:
            cliente_id_str = self.cliente.nombre_completo
        elif self.cliente.email:
            cliente_id_str = self.cliente.email
            
        return f"{self.etiqueta or self.direccion} – {cliente_id_str}"
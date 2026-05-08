# usuarios/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
import uuid
import re


# ------------------------------------------------------------------
# 1. USUARIO PERSONALIZADO (CustomUser)
# Un usuario puede tener múltiples roles simultáneamente.
# Los booleanos indican en qué secciones se ha registrado.
#
# Flujo de registro:
#   - Cualquier visitante puede registrarse como cliente (is_cliente=True por defecto)
#   - Si quiere vender → completa el registro de vendedor → is_vendedor=True
#   - Si quiere repartir → completa el registro de repartidor → is_repartidor=True
# ------------------------------------------------------------------
class CustomUser(AbstractUser):
    """
    Modelo de usuario central de la plataforma.
    Un mismo usuario puede ser cliente, vendedor y repartidor al mismo tiempo,
    siempre que haya completado el registro correspondiente en cada sección.
    """

    # --- Email único como identificador principal ---
    email = models.EmailField(
        "Email",
        unique=True,
        help_text="El email es único y se usa para iniciar sesión."
    )

    # --- Roles del usuario ---
    is_cliente = models.BooleanField(
        "Es cliente",
        default=True,
        help_text=(
            "Activo por defecto. El usuario puede comprar en las tiendas de la plataforma."
        )
    )
    is_vendedor = models.BooleanField(
        "Es vendedor",
        default=False,
        help_text=(
            "Se activa cuando el usuario completa el registro como emprendedor."
        )
    )
    is_repartidor = models.BooleanField(
        "Es repartidor",
        default=False,
        help_text=(
            "Se activa cuando el usuario completa el registro como repartidor."
        )
    )

    # --- Grupos y permisos ---
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='Grupos',
        blank=True,
        related_name="custom_user_groups",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='Permisos',
        blank=True,
        related_name="custom_user_permissions",
        related_query_name="custom_user",
    )

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        roles = []
        if self.is_cliente:
            roles.append('Cliente')
        if self.is_vendedor:
            roles.append('Vendedor')
        if self.is_repartidor:
            roles.append('Repartidor')
        roles_str = ', '.join(roles) if roles else 'Sin rol'
        return f"{self.username} ({roles_str})"

    @property
    def roles_activos(self):
        """Lista de roles activos del usuario."""
        roles = []
        if self.is_cliente:
            roles.append('cliente')
        if self.is_vendedor:
            roles.append('vendedor')
        if self.is_repartidor:
            roles.append('repartidor')
        return roles


# ------------------------------------------------------------------
# 2. PERFIL DE CLIENTE (BuyerProfile)
# Se crea automáticamente al registrarse cualquier usuario.
# ------------------------------------------------------------------
class BuyerProfile(models.Model):
    """
    Perfil de cliente. Se crea automáticamente al registrarse.
    Todos los usuarios son clientes por defecto.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='buyer_profile',
        verbose_name="Usuario"
    )
    telefono = models.CharField(
        "Teléfono",
        max_length=20,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Perfil de Cliente"
        verbose_name_plural = "Perfiles de Clientes"

    def __str__(self):
        return f"Cliente: {self.user.username}"


# ------------------------------------------------------------------
# 3. PERFIL DE VENDEDOR (SellerProfile)
# Se crea cuando el usuario completa el registro como emprendedor.
# ------------------------------------------------------------------
class SellerProfile(models.Model):
    """
    Perfil de vendedor/emprendedor.
    Se crea cuando el usuario completa el registro en la sección de emprendedores.
    Al crearse activa is_vendedor=True en el CustomUser.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='seller_profile',
        verbose_name="Usuario"
    )

    # --- Contacto ---
    telefono = models.CharField(
        "Teléfono",
        max_length=20,
        blank=True,
        null=True
    )
    whatsapp = models.CharField(
        "WhatsApp",
        max_length=15,
        blank=False,
        null=False,
        default='',
        help_text="Formato internacional. Ej: +56912345678"
    )

    # --- Datos fiscales ---
    rut = models.CharField(
        "RUT",
        max_length=12,
        unique=True,
        help_text="RUT de la empresa o persona natural. Ej: 12345678-9"
    )
    razon_social = models.CharField(
        "Razón Social",
        max_length=150,
        help_text="Nombre legal de la empresa o persona natural."
    )
    giro = models.CharField(
        "Giro o actividad",
        max_length=150,
        help_text="Actividad económica principal."
    )
    direccion_fiscal = models.CharField(
        "Dirección Fiscal",
        max_length=255,
        help_text="Dirección registrada para fines tributarios."
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)

    OBLIGATORY_FIELDS = ["rut", "razon_social", "giro", "direccion_fiscal", "whatsapp"]

    def is_complete(self) -> bool:
        """True si todos los campos obligatorios están completos."""
        return all(
            getattr(self, f)
            for f in self.OBLIGATORY_FIELDS
            if getattr(self, f) is not None and getattr(self, f) != ''
        )

    def clean(self):
        if not self.rut:
            raise ValidationError({'rut': "El RUT es obligatorio."})
        if not self.razon_social:
            raise ValidationError({'razon_social': "La razón social es obligatoria."})
        if not self.giro:
            raise ValidationError({'giro': "El giro o actividad es obligatorio."})
        if not self.direccion_fiscal:
            raise ValidationError({'direccion_fiscal': "La dirección fiscal es obligatoria."})
        if not self.whatsapp:
            raise ValidationError({'whatsapp': "El WhatsApp es obligatorio."})
        pattern = r'^\+56[2-9]\d{8}$'
        if not re.match(pattern, self.whatsapp):
            raise ValidationError({
                'whatsapp': "Número inválido. Usa formato +56912345678"
            })

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Activar rol de vendedor en el usuario
        if not self.user.is_vendedor:
            self.user.is_vendedor = True
            self.user.save(update_fields=['is_vendedor'])

    @property
    def whatsapp_url(self):
        """URL wa.me/ lista para usar en el mensaje del pedido."""
        return f"https://wa.me/{self.whatsapp.replace('+', '')}"

    class Meta:
        verbose_name = "Perfil de Vendedor"
        verbose_name_plural = "Perfiles de Vendedores"

    def __str__(self):
        return f"Vendedor: {self.user.username} ({self.razon_social or 'N/A'})"


# ------------------------------------------------------------------
# 4. SEÑALES
# ------------------------------------------------------------------
@receiver(post_save, sender=CustomUser)
def create_buyer_profile(sender, instance, created, **kwargs):
    """
    Crea automáticamente el BuyerProfile al registrarse.
    El SellerProfile y RepartidorProfile se crean manualmente
    cuando el usuario completa el registro en esas secciones.
    """
    if created and instance.is_cliente:
        BuyerProfile.objects.get_or_create(user=instance)


# ------------------------------------------------------------------
# 5. CLIENTE
# Maneja tanto usuarios registrados como invitados (guests).
# Es el modelo que se vincula a pedidos y carritos.
# ------------------------------------------------------------------
class Cliente(models.Model):
    """
    Representa a quien realiza una compra.
    Puede ser un usuario registrado (CustomUser) o un invitado (guest).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cliente_data',
        null=True,
        blank=True,
        verbose_name="Usuario registrado"
    )
    first_name = models.CharField("Nombre", max_length=150, blank=True, null=True)
    last_name = models.CharField("Apellido", max_length=150, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)

    is_guest = models.BooleanField(
        "Es invitado",
        default=False,
        help_text="True si el cliente no tiene cuenta registrada."
    )
    guest_uuid = models.UUIDField(
        default=uuid.uuid4,
        null=True,
        blank=True,
        unique=True,
        help_text="Identificador único para clientes invitados."
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        constraints = [
            models.CheckConstraint(
                check=(
                    Q(user__isnull=False, guest_uuid__isnull=True) |
                    Q(user__isnull=True, guest_uuid__isnull=False)
                ),
                name='user_or_guest_uuid_not_both'
            ),
            models.UniqueConstraint(
                fields=['user'],
                condition=Q(user__isnull=False),
                name='unique_cliente_for_user'
            )
        ]

    def clean(self):
        self.is_guest = self.user is None
        # Registrado → guest_uuid debe ser NULL (el default lo rellena, hay que limpiarlo)
        if self.user is not None:
            self.guest_uuid = None
        for field in ['email', 'first_name', 'last_name', 'telefono']:
            if getattr(self, field) == '':
                setattr(self, field, None)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.user:
            return f"Cliente: {self.user.username} ({self.user.email or 'N/A'})"
        full_name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return f"Invitado: {full_name or self.email or str(self.guest_uuid)[:8]}..."


# ------------------------------------------------------------------
# 6. DIRECCIÓN
# ------------------------------------------------------------------
class Direccion(models.Model):
    """
    Direcciones de los clientes (registrados o invitados).
    Un cliente puede tener múltiples direcciones, una marcada como principal.
    """
    TIPO_PROPIEDAD_CHOICES = [
        ('Casa', 'Casa'),
        ('Edificio', 'Edificio'),
        ('Condominio', 'Condominio'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="direcciones",
        verbose_name="Cliente"
    )
    etiqueta = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="Ej: Casa, Oficina"
    )
    calle = models.CharField(max_length=255)
    numero = models.CharField(max_length=20)
    tipo_propiedad = models.CharField(
        max_length=20,
        choices=TIPO_PROPIEDAD_CHOICES,
        default='Casa'
    )
    departamento = models.CharField(max_length=20, blank=True, null=True)
    block = models.CharField(max_length=50, blank=True, null=True)
    nombre_condominio = models.CharField(max_length=100, blank=True, null=True)
    comuna = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=10, blank=True, null=True)

    latitud = models.DecimalField(
        max_digits=9, decimal_places=6,
        null=True, blank=True,
        help_text="Latitud obtenida de Google Maps."
    )
    longitud = models.DecimalField(
        max_digits=9, decimal_places=6,
        null=True, blank=True,
        help_text="Longitud obtenida de Google Maps."
    )
    validada = models.BooleanField(
        default=False,
        help_text="True si fue validada por Google Maps."
    )
    tipo_direccion = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="Ej: 'Envío', 'Facturación'."
    )
    principal = models.BooleanField(
        default=False,
        help_text="Dirección principal del cliente."
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Dirección"
        verbose_name_plural = "Direcciones"
        constraints = [
            models.UniqueConstraint(
                fields=['cliente'],
                condition=Q(principal=True),
                name='unique_principal_address_per_client'
            )
        ]

    def __str__(self):
        parts = [f"{self.calle} {self.numero}"]
        if self.tipo_propiedad in ['Edificio', 'Condominio']:
            if self.nombre_condominio:
                parts.append(f"Condominio {self.nombre_condominio}")
            if self.block:
                parts.append(f"Block {self.block}")
            if self.departamento:
                parts.append(f"Depto. {self.departamento}")
        parts.extend([self.comuna, self.ciudad, self.region])
        full_address = ", ".join(filter(None, parts))
        return f"{self.etiqueta or 'Dirección'}: {full_address} — {self.cliente}"

    def save(self, *args, **kwargs):
        if self.principal:
            Direccion.objects.filter(
                cliente=self.cliente,
                principal=True
            ).exclude(pk=self.pk).update(principal=False)
        super().save(*args, **kwargs)
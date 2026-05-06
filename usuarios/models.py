# usuarios/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings 
import uuid 
import re
from django.core.exceptions import ValidationError 
from django.db.models import Q 

# ------------------------------------------------------------------
# 1. USUARIO PERSONALIZADO (CustomUser)
# ------------------------------------------------------------------

class UserType(models.TextChoices):
    """
    Define los tipos de usuario disponibles en la plataforma.
    Esto permite diferenciar claramente entre compradores y vendedores.
    """
    BUYER = 'BUYER', 'Comprador'
    SELLER = 'SELLER', 'Vendedor/Comerciante'

class CustomUser(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser.
    Incluye un campo 'user_type' para categorizar al usuario.
    """
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.BUYER, 
        verbose_name="Tipo de Usuario",
        help_text="Define si el usuario es un comprador o un vendedor."
    )

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='Los grupos a los que pertenece este usuario. Un usuario obtendrá todos los permisos concedidos a cada uno de sus grupos.',
        related_name="custom_user_groups", 
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Permisos específicos para este usuario.',
        related_name="custom_user_permissions", 
        related_query_name="custom_user",
    )

    class Meta:
        verbose_name = "Usuario Personalizado"
        verbose_name_plural = "Usuarios Personalizados"

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

# ------------------------------------------------------------------
# 2. PERFILES DE USUARIO ESPECÍFICOS (BuyerProfile y SellerProfile)
# ------------------------------------------------------------------

class BuyerProfile(models.Model):
    """
    Perfil específico para usuarios compradores.
    Este perfil se crea automáticamente para usuarios con user_type='BUYER'.
    Contendrá información adicional relevante solo para compradores.
    """
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        primary_key=True, 
        related_name='buyer_profile',
        verbose_name="Usuario Asociado"
    )
    
    class Meta:
        verbose_name = "Perfil de Comprador"
        verbose_name_plural = "Perfiles de Compradores"

    def __str__(self):
        return f"Perfil de Comprador: {self.user.username}"


class SellerProfile(models.Model):
    """
    Perfil específico para usuarios vendedores/comerciantes.
    Este perfil se crea automáticamente para usuarios con user_type='SELLER'.
    Contiene la información fiscal y de contacto del vendedor.
    """
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        primary_key=True, 
        related_name='seller_profile',
        verbose_name="Usuario Asociado"
    )
    
    # --- Campos obligatorios del perfil de vendedor ---
    telefono = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="Teléfono de Contacto",
        help_text="Teléfono de contacto general (opcional)."
    ) 

    whatsapp = models.CharField(
        "WhatsApp",
        max_length=15,
        blank=False,
        null=False,
        default='',
        help_text="Número de WhatsApp en formato internacional. Ej: +56912345678"
    )

    rut = models.CharField(
        "RUT / DNI", 
        max_length=12, 
        unique=True, 
        blank=False, 
        null=False, 
        help_text="Rol Único Tributario de la empresa o persona natural."
    ) 
    razon_social = models.CharField(
        max_length=150, 
        blank=False, 
        null=False, 
        verbose_name="Razón Social", 
        help_text="Nombre legal de la empresa o persona natural."
    )
    giro = models.CharField(
        "Giro o actividad", 
        max_length=150, 
        blank=False, 
        null=False, 
        help_text="Actividad económica principal del vendedor."
    )
    direccion_fiscal = models.CharField(
        max_length=255, 
        blank=False, 
        null=False, 
        verbose_name="Dirección Fiscal", 
        help_text="Dirección registrada para fines tributarios."
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)

    # ---------- utilidades ----------
    OBLIGATORY_FIELDS = ["rut", "razon_social", "giro", "direccion_fiscal", "whatsapp"]

    def is_complete(self) -> bool:
        """
        Retorna True si todos los campos obligatorios del perfil de vendedor
        tienen un valor no vacío/no nulo.
        """
        return all(
            getattr(self, f) 
            for f in self.OBLIGATORY_FIELDS 
            if getattr(self, f) is not None and getattr(self, f) != ''
        )

    def clean(self):
        """
        Realiza validaciones adicionales para los campos del perfil de vendedor.
        """
        if not self.rut:
            raise ValidationError({'rut': "El RUT / DNI es obligatorio."})
        if not self.razon_social:
            raise ValidationError({'razon_social': "La razón social es obligatoria."})
        if not self.giro:
            raise ValidationError({'giro': "El giro o actividad es obligatorio."})
        if not self.direccion_fiscal:
            raise ValidationError({'direccion_fiscal': "La dirección fiscal es obligatoria."})
        
        # Validación del número de WhatsApp chileno en formato internacional
        if not self.whatsapp:
            raise ValidationError({'whatsapp': "El número de WhatsApp es obligatorio."})
        
        pattern = r'^\+56[2-9]\d{8}$'
        if not re.match(pattern, self.whatsapp):
            raise ValidationError({
                'whatsapp': "Ingresa un número chileno válido en formato internacional. Ej: +56912345678"
            })

    class Meta:
        verbose_name = "Perfil de Vendedor"
        verbose_name_plural = "Perfiles de Vendedores"

    def __str__(self):
        return f"Vendedor: {self.user.username} ({self.razon_social or 'N/A'})"

    @property
    def whatsapp_url(self):
        """
        Retorna la URL de WhatsApp lista para usar en links wa.me/
        Útil para generar el link de envío del pedido al emprendedor.
        """
        numero_limpio = self.whatsapp.replace('+', '')
        return f"https://wa.me/{numero_limpio}"


# ------------------------------------------------------------------
# 3. SEÑALES PARA CREAR Y GUARDAR PERFILES AUTOMÁTICAMENTE
# ------------------------------------------------------------------

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Crea un perfil de comprador o vendedor automáticamente cuando se crea un CustomUser,
    basándose en el 'user_type' asignado.
    """
    if created:
        if instance.user_type == UserType.BUYER:
            BuyerProfile.objects.create(user=instance)
        elif instance.user_type == UserType.SELLER:
            SellerProfile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """
    Guarda el perfil de comprador o vendedor asociado al CustomUser
    cuando el CustomUser se guarda.
    """
    try:
        if instance.user_type == UserType.BUYER and hasattr(instance, 'buyer_profile'):
            instance.buyer_profile.save()
        elif instance.user_type == UserType.SELLER and hasattr(instance, 'seller_profile'):
            instance.seller_profile.save()
    except (BuyerProfile.DoesNotExist, SellerProfile.DoesNotExist):
        pass

# ------------------------------------------------------------------
# 4. MODELOS DE CLIENTE Y DIRECCIÓN (Adaptados para CustomUser)
# ------------------------------------------------------------------

class Cliente(models.Model):
    """
    Representa un cliente, que puede ser un usuario registrado (CustomUser) o un invitado.
    Este modelo es clave para manejar el flujo de pedidos y direcciones.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='cliente_data', 
        null=True,
        blank=True,
        verbose_name="Usuario Registrado"
    )
    
    first_name = models.CharField("Nombre", max_length=150, blank=True, null=True)
    last_name = models.CharField("Apellido", max_length=150, blank=True, null=True)
    email = models.EmailField(blank=True, null=True, unique=False) 
    telefono = models.CharField(max_length=30, blank=True, null=True)

    is_guest = models.BooleanField(
        default=False, 
        help_text="Indica si este cliente es un invitado (no tiene cuenta de usuario)."
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

        if self.email == '':
            self.email = None
        if self.first_name == '':
            self.first_name = None
        if self.last_name == '':
            self.last_name = None
        if self.telefono == '':
            self.telefono = None

    def save(self, *args, **kwargs):
        self.full_clean() 
        super().save(*args, **kwargs)

    def __str__(self):
        if self.user:
            return f"Cliente Registrado: {self.user.username} ({self.user.email or 'N/A'})"
        elif self.guest_uuid:
            full_name = f"{self.first_name or ''} {self.last_name or ''}".strip()
            return f"Cliente Invitado: {full_name or self.email or str(self.guest_uuid)[:8]}..."
        return f"Cliente ID: {self.id}"


class Direccion(models.Model):
    """
    Modelo para almacenar las direcciones de los clientes (registrados o invitados).
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
        verbose_name="Cliente Asociado"
    )
    etiqueta = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="Ej: Casa, Oficina, Principal"
    )
    
    calle = models.CharField(max_length=255, help_text="Nombre de la calle o avenida.")
    numero = models.CharField(max_length=20, help_text="Número de la dirección.")
    
    tipo_propiedad = models.CharField(
        max_length=20, 
        choices=TIPO_PROPIEDAD_CHOICES, 
        default='Casa', 
        help_text="Selecciona el tipo de propiedad (Casa, Edificio, Condominio)."
    )

    departamento = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        help_text="Número de departamento, oficina, etc."
    )
    block = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="Número o nombre del bloque/torre dentro del complejo (ej: Bloque A, Torre 3)."
    )
    nombre_condominio = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text="Nombre del condominio o complejo."
    )

    comuna = models.CharField(max_length=100, help_text="Comuna o distrito.")
    ciudad = models.CharField(max_length=100, help_text="Ciudad.")
    region = models.CharField(max_length=100, help_text="Región o estado.")
    codigo_postal = models.CharField(max_length=10, blank=True, null=True, help_text="Código postal.")
    
    latitud = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True, 
        help_text="Latitud obtenida de la validación."
    )
    longitud = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True, 
        help_text="Longitud obtenida de la validación."
    )
    validada = models.BooleanField(
        default=False, 
        help_text="Indica si la dirección ha sido validada por una API de mapas."
    )

    tipo_direccion = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="Tipo de dirección (ej. 'Envío', 'Facturación')."
    ) 
    principal = models.BooleanField(
        default=False, 
        help_text="Define si es la dirección principal para este cliente."
    )

    class Meta:
        ordering = ["-id"]
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

        cliente_info = ""
        if self.cliente.user:
            cliente_info = self.cliente.user.username
        elif self.cliente.first_name or self.cliente.last_name:
            cliente_info = f"{self.cliente.first_name or ''} {self.cliente.last_name or ''}".strip()
        elif self.cliente.email:
            cliente_info = self.cliente.email
            
        return f"{self.etiqueta or 'Dirección'}: {full_address} – Cliente: {cliente_info}"
    
    def save(self, *args, **kwargs):
        if self.principal:
            Direccion.objects.filter(
                cliente=self.cliente, 
                principal=True
            ).exclude(pk=self.pk).update(principal=False)
        super().save(*args, **kwargs)
        




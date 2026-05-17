# plataforma_config/models.py
from django.db import models
from django.core.exceptions import ValidationError
import re


# ------------------------------------------------------------------
# UTILIDAD: Validador de color HEX
# ------------------------------------------------------------------
def validar_color_hex(value):
    """
    Valida que el valor sea un color HEX válido.
    Acepta formatos: #FFF o #FFFFFF (con o sin #).
    """
    if value and not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', value):
        raise ValidationError(
            f"'{value}' no es un color HEX válido. Usa el formato #RRGGBB. Ej: #FF5733"
        )


# ------------------------------------------------------------------
# CONFIGURACIÓN GLOBAL DE LA PLATAFORMA (Singleton)
# Solo puede existir UNA instancia de este modelo.
# Se gestiona desde el panel de administración.
# ------------------------------------------------------------------
class PlatformSetting(models.Model):

    # --- Identidad de la plataforma ---
    platform_name = models.CharField(
        "Nombre de la plataforma",
        max_length=100,
        default="Mi Plataforma",
        help_text="Nombre que aparece en el encabezado, título del navegador y emails."
    )
    platform_description = models.CharField(
        "Descripción breve",
        max_length=255,
        blank=True,
        null=True,
        help_text="Descripción corta de la plataforma. Aparece en el SEO y página de inicio."
    )
    platform_logo = models.ImageField(
        "Logo de la plataforma",
        upload_to='platform_assets/',
        blank=True,
        null=True,
        help_text="Logo principal de la plataforma. Recomendado: PNG transparente, 200x60px."
    )
    hero_banner = models.ImageField(
        "Banner de la página principal",
        upload_to='platform_assets/',
        blank=True,
        null=True,
        help_text="Imagen hero de la página de inicio. Recomendado: 1200x400px."
    )
    favicon = models.ImageField(
        "Favicon",
        upload_to='platform_assets/',
        blank=True,
        null=True,
        help_text="Ícono del navegador. Recomendado: PNG o ICO, 32x32px."
    )

    # --- Colores globales ---
    # Se usan para personalizar el look de la plataforma sin tocar CSS.
    primary_color_hex = models.CharField(
        "Color primario (HEX)",
        max_length=7,
        blank=True,
        null=True,
        validators=[validar_color_hex],
        help_text="Color principal de botones y encabezados. Ej: #FF5733"
    )
    secondary_color_hex = models.CharField(
        "Color secundario (HEX)",
        max_length=7,
        blank=True,
        null=True,
        validators=[validar_color_hex],
        help_text="Color de acento o secundario. Ej: #33C1FF"
    )

    # --- Diseño de listado de tiendas ---
    store_card_layout = models.CharField(
        "Diseño de tarjetas de tienda",
        max_length=10,
        choices=[
            ('grid', 'Cuadrícula'),
            ('list', 'Lista'),
        ],
        default='grid',
        help_text="Define cómo se muestran las tiendas en la página principal."
    )

    # --- Textos legales ---
    terms_and_conditions = models.TextField(
        "Términos y Condiciones",
        blank=True,
        null=True,
        help_text="Texto completo de los términos y condiciones de uso de la plataforma."
    )
    privacy_policy = models.TextField(
        "Política de Privacidad",
        blank=True,
        null=True,
        help_text="Texto completo de la política de privacidad."
    )

    # --- Contacto de soporte de la plataforma ---
    soporte_email = models.EmailField(
        "Email de soporte",
        blank=True,
        null=True,
        help_text="Email de contacto para soporte de la plataforma."
    )
    soporte_whatsapp = models.CharField(
        "WhatsApp de soporte",
        max_length=15,
        blank=True,
        null=True,
        help_text="Número de WhatsApp de soporte en formato internacional. Ej: +56912345678"
    )

    # --- Control ---
    last_updated = models.DateTimeField(
        "Última actualización",
        auto_now=True
    )

    # ------------------------------------------------------------------
    # SINGLETON: Solo puede existir una instancia
    # ------------------------------------------------------------------
    def save(self, *args, **kwargs):
        if not self.pk and PlatformSetting.objects.exists():
            raise ValidationError(
                "Solo puede existir una configuración global de la plataforma. "
                "Edita la existente en lugar de crear una nueva."
            )
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """
        Retorna la instancia única de configuración.
        Si no existe, la crea con valores por defecto.
        Usar esto en lugar de PlatformSetting.objects.first() en el código.

        Ejemplo de uso en una vista:
            config = PlatformSetting.get_settings()
            print(config.platform_name)
        """
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance

    def __str__(self):
        return f"Configuración Global — {self.platform_name}"

    class Meta:
        verbose_name = "Configuración de Plataforma"
        verbose_name_plural = "Configuración de Plataforma"


# ------------------------------------------------------------------
# CATEGORÍAS DE TIENDA (para el orbital del frontend)
# Gestionadas desde el admin — el frontend las consume vía API.
# ------------------------------------------------------------------
class CategoriaTienda(models.Model):

    TIPO_NEGOCIO_CHOICES = [
        ('COMIDA',    'Comida y Bebidas'),
        ('RETAIL',    'Tienda / Retail'),
        ('SERVICIOS', 'Servicios'),
        ('OTRO',      'Otro'),
    ]

    nombre = models.CharField("Nombre", max_length=100, unique=True)
    emoji  = models.CharField("Emoji",  max_length=20)
    tipo_negocio = models.CharField(
        "Tipo de negocio",
        max_length=20,
        choices=TIPO_NEGOCIO_CHOICES,
        default='COMIDA',
        help_text="Filtra las tiendas de este tipo al seleccionar la categoría."
    )
    orden  = models.PositiveIntegerField("Orden", default=0)
    activo = models.BooleanField("Activo", default=True)

    class Meta:
        ordering = ['orden', 'nombre']
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return f"{self.emoji} {self.nombre}"
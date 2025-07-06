# plataforma_config/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save # Importar para el "singleton"
from django.dispatch import receiver # Importar para el "singleton"

class PlatformSetting(models.Model):
    # Campos para el logo de la plataforma
    platform_logo = models.ImageField(upload_to='platform_assets/', blank=True, null=True,
                                      verbose_name="Logo de la Plataforma")

    # Campos para colores o estilos globales (ej. CSS custom)
    primary_color_hex = models.CharField(max_length=7, blank=True, null=True, verbose_name="Color Primario (HEX)")
    secondary_color_hex = models.CharField(max_length=7, blank=True, null=True, verbose_name="Color Secundario (HEX)")
    
    # Campo para los términos y condiciones (usaremos TextField para texto largo)
    terms_and_conditions = models.TextField(blank=True, null=True, verbose_name="Términos y Condiciones")
    privacy_policy = models.TextField(blank=True, null=True, verbose_name="Política de Privacidad")

    # Configuración de cómo se muestran las tiendas (ej. "grid" o "list")
    store_card_layout = models.CharField(
        max_length=10,
        choices=[('grid', 'Cuadrícula'), ('list', 'Lista')],
        default='grid',
        verbose_name="Diseño de Tarjetas de Tienda"
    )
    
    # Marca de tiempo para saber cuándo fue la última actualización
    last_updated = models.DateTimeField(auto_now=True)

    # Un Singleton Model: Solo debe haber una instancia de este modelo
    class Meta:
        verbose_name = "Configuración de Plataforma"
        verbose_name_plural = "Configuración de Plataforma" # Asegúrate de que el plural sea claro

    def save(self, *args, **kwargs):
        # Asegura que solo haya una instancia de este modelo
        if not self.pk and PlatformSetting.objects.exists():
            raise ValidationError("Solo puede haber una instancia de la configuración de la plataforma.")
        super().save(*args, **kwargs)

    def __str__(self):
        return "Configuración Global de la Plataforma"

# Signal para asegurar la creación de una instancia única si no existe
@receiver(post_save, sender=PlatformSetting)
def create_platform_setting_singleton(sender, instance, created, **kwargs):
    if not created and PlatformSetting.objects.count() == 0: # Si no se acaba de crear y no hay ninguna
        PlatformSetting.objects.create() # Crea una instancia
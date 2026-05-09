# plataforma_config/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.forms import TextInput
from .models import PlatformSetting, CategoriaTienda

# ------------------------------------------------------------------
# CONFIGURACIÓN DE PLATAFORMA (SINGLETON)
# ------------------------------------------------------------------
@admin.register(PlatformSetting)
class PlatformSettingAdmin(admin.ModelAdmin):
    # Seguridad Singleton
    def has_add_permission(self, request):
        return not PlatformSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    # Visualización en la lista
    list_display = ('platform_name', 'show_logo_thumbnail', 'store_card_layout', 'last_updated')
    readonly_fields = ('last_updated', 'show_logo_preview', 'show_favicon_preview')

    # Inyectar widgets de color (tipo color picker del navegador)
    formfield_overrides = {
        # Esto hace que en el admin aparezca el selector de colores nativo
        None: {'widget': TextInput(attrs={'type': 'color', 'style': 'width: 100px; padding: 0; border: none; height: 40px;'})}
    }

    fieldsets = (
        ('Identidad Visual', {
            'fields': (
                'platform_name', 
                'platform_description',
                ('platform_logo', 'show_logo_preview'),
                ('favicon', 'show_favicon_preview'),
            )
        }),
        ('Personalización de Estilo', {
            'fields': (
                ('primary_color_hex', 'secondary_color_hex'),
                'store_card_layout',
            ),
            'description': 'Configura los colores corporativos y la disposición visual de las tiendas.'
        }),
        ('Información Legal', {
            'fields': ('terms_and_conditions', 'privacy_policy'),
            'classes': ('collapse',),
        }),
        ('Soporte y Contacto', {
            'fields': (('soporte_email', 'soporte_whatsapp'),),
        }),
        ('Metadatos', {
            'fields': ('last_updated',),
            'classes': ('collapse',),
        }),
    )

    # --- Helpers para previsualizar imágenes ---
    def show_logo_preview(self, obj):
        if obj.platform_logo:
            return format_html('<img src="{}" style="max-height: 50px; background: #eee; padding: 5px; border-radius: 4px;"/>', obj.platform_logo.url)
        return "Sin logo"
    show_logo_preview.short_description = "Vista previa logo"

    def show_logo_thumbnail(self, obj):
        if obj.platform_logo:
            return format_html('<img src="{}" style="height: 30px;"/>', obj.platform_logo.url)
        return "-"
    show_logo_thumbnail.short_description = "Logo"

    def show_favicon_preview(self, obj):
        if obj.favicon:
            return format_html('<img src="{}" style="height: 32px;"/>', obj.favicon.url)
        return "Sin favicon"
    show_favicon_preview.short_description = "Vista previa favicon"


# ------------------------------------------------------------------
# CATEGORÍAS DE TIENDA
# ------------------------------------------------------------------
@admin.register(CategoriaTienda)
class CategoriaTiendaAdmin(admin.ModelAdmin):
    # Mejora: mostramos el emoji más grande en la lista
    list_display = ('render_emoji', 'nombre', 'tipo_negocio', 'orden', 'activo')
    list_display_links = ('render_emoji', 'nombre')
    list_editable = ('orden', 'activo', 'tipo_negocio')
    list_filter = ('tipo_negocio', 'activo')
    search_fields = ('nombre',)
    ordering = ('orden', 'nombre')

    def render_emoji(self, obj):
        return format_html('<span style="font-size: 20px;">{}</span>', obj.emoji)
    render_emoji.short_description = "Ícono"

    # Agrupar campos en el formulario de edición
    fieldsets = (
        (None, {
            'fields': (('nombre', 'emoji'), 'tipo_negocio')
        }),
        ('Estado y Orden', {
            'fields': ('activo', 'orden'),
        }),
    )
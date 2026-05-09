# plataforma_config/admin.py
from django.contrib import admin
from .models import PlatformSetting


@admin.register(PlatformSetting)
class PlatformSettingAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return not PlatformSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ('platform_name', 'store_card_layout', 'last_updated')
    readonly_fields = ('last_updated',)

    fieldsets = (
        ('Identidad', {
            'fields': (
                'platform_name', 'platform_description',
                'platform_logo', 'favicon',
            )
        }),
        ('Colores', {
            'fields': ('primary_color_hex', 'secondary_color_hex'),
            'description': 'Usa formato HEX. Ej: #FF5733'
        }),
        ('Diseño', {
            'fields': ('store_card_layout',)
        }),
        ('Textos legales', {
            'fields': ('terms_and_conditions', 'privacy_policy'),
            'classes': ('collapse',),
        }),
        ('Soporte', {
            'fields': ('soporte_email', 'soporte_whatsapp'),
            'description': 'Datos de contacto del soporte de la plataforma.'
        }),
        ('Control', {
            'fields': ('last_updated',),
            'classes': ('collapse',),
        }),
    )
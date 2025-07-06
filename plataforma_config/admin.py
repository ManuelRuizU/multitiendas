# plataforma_config/admin.py
from django.contrib import admin
from .models import PlatformSetting

@admin.register(PlatformSetting)
class PlatformSettingAdmin(admin.ModelAdmin):
    # No queremos que se pueda añadir o borrar más de una instancia desde el admin
    def has_add_permission(self, request):
        # Permite añadir solo si no existe ninguna instancia aún
        return not PlatformSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False # No permitir eliminar la única instancia

    list_display = ('__str__', 'last_updated', 'store_card_layout')
    # fields = ('platform_logo', 'primary_color_hex', 'secondary_color_hex',
    #           'terms_and_conditions', 'privacy_policy', 'store_card_layout')
    # Puedes personalizar los campos que se muestran para edición
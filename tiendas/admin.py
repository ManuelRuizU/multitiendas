# tiendas/admin.py
from django.contrib import admin
from .models import Tienda, RadioEnvio # Estos sí están en tiendas.models

# ¡¡¡CORRECCIÓN CLAVE AQUÍ!!!
# Importa los modelos de usuario y perfiles desde la app 'usuarios'
from usuarios.models import CustomUser, SellerProfile # Solo importa los que realmente necesitas aquí

# Inline para Radios de Envío dentro del admin de Tienda
class RadioEnvioInline(admin.TabularInline):
    model = RadioEnvio
    extra = 1 
    # fields = ('distancia_max_km', 'costo_envio', 'envio_gratis')


@admin.register(Tienda)
class TiendaAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'nombre', 
        'propietario_perfil_display', 
        'activo', 'direccion', 
        'latitud', 'longitud', 
        'telefono', 'fecha_creacion'
    )
    list_filter = ('activo', 'propietario_perfil',) 
    search_fields = ('nombre', 'propietario_perfil__user__username', 'direccion') 
    prepopulated_fields = {'slug': ('nombre',)}
    inlines = [RadioEnvioInline] 

    fieldsets = (
        (None, {
            'fields': ('propietario_perfil', 'nombre', 'slug', 'descripcion', 'activo') 
        }),
        ('Información de Contacto', {
            'fields': ('telefono', 'email', 'url', 'horario_atencion')
        }),
        ('Ubicación de la Tienda', {
            'fields': ('direccion', 'latitud', 'longitud') 
        }),
        ('Imágenes', {
            'fields': ('logo',)
        }),
    )
    
    def propietario_perfil_display(self, obj):
        if obj.propietario_perfil:
            return obj.propietario_perfil.user.username
        return "N/A"
    propietario_perfil_display.short_description = 'Propietario'

    def save_model(self, request, obj, form, change):
        if not obj.pk: 
            if hasattr(request.user, 'seller_profile'):
                obj.propietario_perfil = request.user.seller_profile
        super().save_model(request, obj, form, change)


@admin.register(RadioEnvio) 
class RadioEnvioAdmin(admin.ModelAdmin):
    list_display = ('id', 'tienda', 'distancia_max_km', 'costo_envio', 'envio_gratis')
    list_filter = ('tienda', 'envio_gratis')
    search_fields = ('tienda__nombre',)

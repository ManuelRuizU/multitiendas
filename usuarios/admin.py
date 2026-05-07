# usuarios/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode

from .models import CustomUser, BuyerProfile, SellerProfile, Cliente, Direccion

# ------------------------------------------------------------------
# 1. INLINES PARA CUSTOMUSER
# ------------------------------------------------------------------
class SellerProfileInline(admin.StackedInline):
    model = SellerProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Vendedor'
    fk_name = 'user'
    # 'whatsapp' se mantiene si lo tienes en el modelo, 'fecha_registro' es readonly
    fields = ['telefono', 'whatsapp', 'rut', 'razon_social', 'giro', 'direccion_fiscal', 'fecha_registro']
    readonly_fields = ['fecha_registro']
    extra = 0 # No mostrar formularios vacíos extra

class BuyerProfileInline(admin.StackedInline):
    model = BuyerProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Cliente'
    fk_name = 'user'
    fields = ['telefono']
    extra = 0

# ------------------------------------------------------------------
# 2. CUSTOM USER ADMIN
# ------------------------------------------------------------------
try:
    admin.site.unregister(CustomUser)
except admin.sites.NotRegistered:
    pass

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    inlines = (BuyerProfileInline, SellerProfileInline)

    # Quitamos 'user_type' (si estaba) y dejamos los booleanos
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_vendedor',
        'is_cliente',
        'is_repartidor',
        'is_staff',
        'cliente_main_address',
    )
    
    list_filter = ('is_vendedor', 'is_cliente', 'is_repartidor', 'is_staff', 'is_superuser', 'is_active')
    
    search_fields = ('username', 'email', 'first_name', 'last_name', 'seller_profile__rut', 'seller_profile__razon_social')

    # Agregamos los nuevos campos de roles al formulario de edición de Django
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Roles en la plataforma', {
            'fields': ('is_cliente', 'is_vendedor', 'is_repartidor'),
            'description': (
                'Los roles se activan automáticamente según el perfil creado. '
                'Modifique manualmente solo en casos excepcionales.'
            )
        }),
    )

    def cliente_main_address(self, obj):
        # Usamos cliente_data que es el related_name en tu modelo Cliente
        if hasattr(obj, 'cliente_data'):
            main_address = obj.cliente_data.direcciones.filter(principal=True).first()
            if main_address:
                url = reverse('admin:usuarios_direccion_change', args=[main_address.pk])
                return format_html(
                    '<a href="{}">{}</a>',
                    url, main_address.calle
                )
        return "Sin dirección"
    cliente_main_address.short_description = 'Dirección Principal'


# ------------------------------------------------------------------
# 3. ADMIN PARA BUYERPROFILE
# ------------------------------------------------------------------
@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'telefono')
    search_fields = ('user__username', 'user__email', 'telefono')
    readonly_fields = ('user',)

    def user_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:usuarios_customuser_change', args=[obj.user.pk]),
            obj.user.username
        )
    user_link.short_description = 'Usuario'


# ------------------------------------------------------------------
# 4. ADMIN PARA SELLERPROFILE
# ------------------------------------------------------------------
@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user_link', 'rut', 'razon_social', 'giro',
        'whatsapp', 'telefono', 'fecha_registro', 'perfil_completo'
    )
    search_fields = ('user__username', 'user__email', 'rut', 'razon_social', 'giro')
    list_filter = ('fecha_registro',)
    readonly_fields = ('fecha_registro', 'user')

    fieldsets = (
        ('Usuario Relacionado', {'fields': ('user',)}),
        ('Contacto Comercial', {'fields': ('telefono', 'whatsapp')}),
        ('Datos Legales/Fiscales', {'fields': ('rut', 'razon_social', 'giro', 'direccion_fiscal')}),
        ('Registro', {'fields': ('fecha_registro',)}),
    )

    def user_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:usuarios_customuser_change', args=[obj.user.pk]),
            obj.user.username
        )
    user_link.short_description = 'Usuario'

    def perfil_completo(self, obj):
        return obj.is_complete()
    perfil_completo.boolean = True
    perfil_completo.short_description = '¿Completo?'


# ------------------------------------------------------------------
# 5. ADMIN PARA CLIENTE
# ------------------------------------------------------------------
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_display', 'first_name', 'last_name', 'email', 'is_guest', 'count_addresses')
    list_filter = ('is_guest',)
    search_fields = ('first_name', 'last_name', 'email', 'user__username')
    readonly_fields = ('guest_uuid',)

    def user_display(self, obj):
        if obj.user:
            return format_html('<a href="{}">{}</a>', 
                               reverse('admin:usuarios_customuser_change', args=[obj.user.pk]), 
                               obj.user.username)
        return "Invitado"
    user_display.short_description = 'Usuario'

    def count_addresses(self, obj):
        count = obj.direcciones.count()
        return count
    count_addresses.short_description = 'Direcciones'


# ------------------------------------------------------------------
# 6. ADMIN PARA DIRECCIÓN
# ------------------------------------------------------------------
@admin.register(Direccion)
class DireccionAdmin(admin.ModelAdmin):
    list_display = ('etiqueta', 'calle', 'numero', 'comuna', 'ciudad', 'cliente', 'principal', 'validada')
    list_filter = ('principal', 'validada', 'comuna')
    search_fields = ('calle', 'cliente__email', 'cliente__user__username')
    raw_id_fields = ('cliente',)
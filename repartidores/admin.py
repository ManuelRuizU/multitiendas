# repartidores/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin 
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import urlencode

# Importa tus modelos personalizados
from .models import CustomUser, BuyerProfile, SellerProfile, Cliente, Direccion, UserType

# ------------------------------------------------------------------
# 1. INLINE PARA SELLERPROFILE (en la vista de CustomUser)
# ------------------------------------------------------------------
class SellerProfileInline(admin.StackedInline):
    model = SellerProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Vendedor'
    fk_name = 'user' 
    fields = ['telefono', 'rut', 'razon_social', 'giro', 'direccion_fiscal', 'fecha_registro']
    readonly_fields = ['fecha_registro']

# ------------------------------------------------------------------
# 2. INLINE PARA BUYERPROFILE (en la vista de CustomUser)
# ------------------------------------------------------------------
class BuyerProfileInline(admin.StackedInline):
    model = BuyerProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Comprador'
    fk_name = 'user' 

# ------------------------------------------------------------------
# 3. CUSTOM USER ADMIN
# ------------------------------------------------------------------
try:
    admin.site.unregister(CustomUser) 
except admin.sites.NotRegistered:
    pass

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    inlines = (BuyerProfileInline, SellerProfileInline) 
    # Aquí agregamos 'cliente_main_address' a la lista para facilitar la visualización de la dirección principal del cliente para pruebas
    list_display = BaseUserAdmin.list_display + ('user_type', 'is_seller_display', 'is_buyer_display', 'is_cliente_data_display', 'cliente_main_address')
    list_filter = BaseUserAdmin.list_filter + ('user_type',)
    search_fields = list(BaseUserAdmin.search_fields) + [
        'seller_profile__rut', 
        'seller_profile__razon_social', 
        'buyer_profile__user__email', 
        'cliente_data__first_name', 
        'cliente_data__last_name',
        'cliente_data__email',
        'cliente_data__guest_uuid',
    ]
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Tipo de Usuario', {'fields': ('user_type',)}),
    )

    def is_seller_display(self, obj):
        return hasattr(obj, 'seller_profile')
    is_seller_display.boolean = True
    is_seller_display.short_description = 'Es Vendedor (Perfil)'

    def is_buyer_display(self, obj):
        return hasattr(obj, 'buyer_profile')
    is_buyer_display.boolean = True
    is_buyer_display.short_description = 'Es Comprador (Perfil)'

    def is_cliente_data_display(self, obj):
        return hasattr(obj, 'cliente_data')
    is_cliente_data_display.boolean = True
    is_cliente_data_display.short_description = 'Es Cliente (Pedidos)'

    # Este método muestra la dirección principal del cliente. Útil para encontrar IDs de prueba.
    def cliente_main_address(self, obj):
        if hasattr(obj, 'cliente_data'):
            main_address = obj.cliente_data.direcciones.filter(principal=True).first()
            if main_address:
                url = reverse('admin:usuarios_direccion_change', args=[main_address.pk])
                return format_html('<a href="{}">ID: {} ({})</a>', url, main_address.pk, main_address.calle)
        return "N/A"
    cliente_main_address.short_description = 'Dirección Principal de Cliente'


# ------------------------------------------------------------------
# 4. ADMIN PARA BUYERPROFILE (Vista independiente del perfil de comprador)
# ------------------------------------------------------------------
@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ('user_link',) 
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user',)

    def user_link(self, obj):
        return format_html('<a href="{}">{}</a>',
                           reverse('admin:usuarios_customuser_change', args=[obj.user.pk]),
                           obj.user.username)
    user_link.short_description = 'Usuario'

# ------------------------------------------------------------------
# 5. ADMIN PARA SELLERPROFILE (Vista independiente del perfil de vendedor)
# ------------------------------------------------------------------
@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'rut', 'razon_social', 'giro', 'telefono', 'fecha_registro', 'is_complete')
    search_fields = ('user__username', 'rut', 'razon_social', 'giro', 'telefono')
    list_filter = ('fecha_registro', 'giro')
    readonly_fields = ('fecha_registro', 'user') 

    def user_link(self, obj):
        return format_html('<a href="{}">{}</a>',
                           reverse('admin:usuarios_customuser_change', args=[obj.user.pk]),
                           obj.user.username)
    user_link.short_description = 'Usuario'

    def is_complete(self, obj):
        return obj.is_complete()
    is_complete.boolean = True
    is_complete.short_description = 'Perfil Completo'


# ------------------------------------------------------------------
# 6. ADMIN PARA CLIENTE (Vista independiente del modelo Cliente)
# ------------------------------------------------------------------
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_display', 'first_name', 'last_name', 'email', 'telefono', 'is_guest', 'view_main_address', 'count_addresses')
    search_fields = ('user__username', 'first_name', 'last_name', 'email', 'telefono', 'guest_uuid')
    list_filter = ('is_guest',)
    readonly_fields = ('user', 'is_guest', 'guest_uuid') 

    def user_display(self, obj):
        if obj.user:
            return format_html('<a href="{}">{}</a>',
                               reverse('admin:usuarios_customuser_change', args=[obj.user.pk]),
                               obj.user.username)
        return "Invitado"
    user_display.short_description = 'Usuario (Registrado)'

    def view_main_address(self, obj):
        main_address = obj.direcciones.filter(principal=True).first()
        if main_address:
            return format_html('<a href="{}">{}</a>',
                               reverse('admin:usuarios_direccion_change', args=[main_address.pk]),
                               str(main_address))
        return "N/A"
    view_main_address.short_description = 'Dir. Principal'

    def count_addresses(self, obj):
        count = obj.direcciones.count()
        url = (
            reverse("admin:usuarios_direccion_changelist")
            + "?"
            + urlencode({"cliente__id": f"{obj.pk}"})
        )
        return format_html('<a href="{}">{}</a>', url, count)
    count_addresses.short_description = 'Nº Direcciones'

# ------------------------------------------------------------------
# 7. ADMIN PARA DIRECCIÓN (Vista independiente del modelo Dirección)
# ------------------------------------------------------------------
@admin.register(Direccion)
class DireccionAdmin(admin.ModelAdmin):
    list_display = ('etiqueta', 'calle', 'numero', 'comuna', 'ciudad', 'region', 'cliente_display', 'principal')
    search_fields = ('calle', 'numero', 'comuna', 'ciudad', 'region', 'cliente__user__username', 'cliente__first_name', 'cliente__last_name', 'cliente__email', 'cliente__guest_uuid')
    list_filter = ('principal', 'tipo_propiedad', 'comuna', 'ciudad', 'region')
    raw_id_fields = ('cliente',) 

    def cliente_display(self, obj):
        if obj.cliente.user:
            return format_html('<a href="{}">{}</a>',
                               reverse('admin:usuarios_customuser_change', args=[obj.cliente.user.pk]),
                               obj.cliente.user.username)
        elif obj.cliente.guest_uuid:
            return format_html('<a href="{}">{} (Invitado)</a>',
                               reverse('admin:usuarios_cliente_change', args=[obj.cliente.pk]),
                               str(obj.cliente.guest_uuid)[:8] + '...')
        return "N/A"
    cliente_display.short_description = 'Cliente'

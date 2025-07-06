# usuarios/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import PerfilVendedor, Cliente, Direccion

# Inline para PerfilVendedor en el admin de User
class PerfilVendedorInline(admin.StackedInline):
    model = PerfilVendedor
    can_delete = False
    verbose_name_plural = 'Perfil de Vendedor'
    fields = ('telefono', 'rut', 'razon_social', 'giro', 'direccion_fiscal')

# Inline para Cliente en el admin de User
class ClienteInline(admin.StackedInline):
    model = Cliente
    can_delete = False
    verbose_name_plural = 'Datos de Cliente'
    fields = ('telefono',)

# Primero, desregistra el modelo User de Django si ya está registrado
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass # No hacer nada si ya no está registrado

# Ahora, registra tu UserAdmin personalizado
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (PerfilVendedorInline, ClienteInline,)
    list_display = BaseUserAdmin.list_display + ('has_seller_profile', 'has_customer_profile')

    def has_seller_profile(self, obj):
        return hasattr(obj, 'perfil_vendedor') and obj.perfil_vendedor is not None
    has_seller_profile.boolean = True
    has_seller_profile.short_description = 'Es Vendedor'

    def has_customer_profile(self, obj):
        return hasattr(obj, 'cliente') and obj.cliente is not None
    has_customer_profile.boolean = True
    has_customer_profile.short_description = 'Es Cliente'

# Registra los modelos directamente
admin.site.register(Direccion)
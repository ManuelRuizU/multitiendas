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
    # readonly_fields = ('fecha_registro',) # Si quieres que la fecha de registro no sea editable

# Inline para Direccion dentro del admin de Cliente
# Esto permite ver y añadir direcciones directamente desde la vista de detalle de un Cliente
class DireccionInline(admin.TabularInline): # TabularInline es más compacto
    model = Direccion
    extra = 0 # No mostrar campos extra vacíos por defecto
    fields = [
        'etiqueta', 'calle', 'numero', 'departamento', 'block', 'nombre_condominio',
        'comuna', 'ciudad', 'region', 'codigo_postal', 'tipo_propiedad',
        'latitud', 'longitud', 'validada', 'tipo_direccion', 'principal'
    ]
    # Si quieres que la dirección principal solo pueda ser una por cliente,
    # deberás añadir validación en el serializador o en el modelo Direccion's clean method.

# Admin para el modelo Cliente
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    # Campos a mostrar en la lista de clientes
    list_display = (
        'id',
        'get_username',         # Método para mostrar el username si existe
        'nombre_completo',
        'email',
        'telefono',
        'is_guest',             # Para ver rápidamente si es un invitado
        'get_direccion_principal_display', # Nuevo método para mostrar la dirección principal
        'numero_direcciones',   # Nuevo método para contar direcciones
    )
    # Filtros para la lista de clientes
    list_filter = ('is_guest',)
    # Campos de búsqueda
    search_fields = (
        'user__username',
        'nombre_completo',
        'email',
        'telefono',
    )
    # Campos de solo lectura en el formulario de detalle
    readonly_fields = ('is_guest',) # 'is_guest' se calcula automáticamente
    
    # Inlines para mostrar las direcciones del cliente
    inlines = [DireccionInline]

    # Métodos personalizados para list_display
    def get_username(self, obj):
        return obj.user.username if obj.user else "-"
    get_username.short_description = "Usuario (Registrado)"
    get_username.admin_order_field = 'user__username' # Permite ordenar por este campo

    def numero_direcciones(self, obj):
        return obj.direcciones.count()
    numero_direcciones.short_description = "Nº Direcciones"

    def get_direccion_principal_display(self, obj):
        # Busca la dirección principal del cliente
        principal_address = obj.direcciones.filter(principal=True).first()
        if principal_address:
            # Reconstruye la dirección legiblemente (similar a Direccion.__str__)
            parts = [f"{principal_address.calle} {principal_address.numero}"]
            if principal_address.departamento:
                parts.append(f"Depto. {principal_address.departamento}")
            parts.extend([principal_address.comuna, principal_address.ciudad])
            return ", ".join(filter(None, parts))
        return "N/A"
    get_direccion_principal_display.short_description = "Dir. Principal"


# Admin para el modelo Direccion
@admin.register(Direccion)
class DireccionAdmin(admin.ModelAdmin):
    # Campos a mostrar en la lista de direcciones
    list_display = (
        'id',
        'get_cliente_display', # Método para mostrar a qué cliente pertenece
        'etiqueta',
        'calle',
        'numero',
        'comuna',
        'ciudad',
        'principal',
        'validada',
    )
    # Filtros para la lista de direcciones
    list_filter = ('principal', 'validada', 'tipo_propiedad', 'tipo_direccion')
    # Campos de búsqueda
    search_fields = (
        'cliente__user__username', # Busca por el usuario registrado asociado
        'cliente__nombre_completo', # Busca por el nombre completo del cliente
        'etiqueta',
        'calle',
        'numero',
        'comuna',
        'ciudad',
        'region',
        'codigo_postal',
    )
    # Campos de solo lectura en el formulario de detalle
    readonly_fields = ('latitud', 'longitud',) # Estos vienen de la API de mapas

    # Método personalizado para mostrar el cliente en la lista de direcciones
    def get_cliente_display(self, obj):
        if obj.cliente.user:
            return obj.cliente.user.username
        return obj.cliente.nombre_completo or obj.cliente.email or "Invitado"
    get_cliente_display.short_description = "Cliente"


# Desregistra el modelo User de Django si ya está registrado para registrarlo con tu Admin personalizado
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# Registra tu UserAdmin personalizado
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (PerfilVendedorInline,) # Quitamos ClienteInline de aquí, ahora Cliente tiene su propio admin
    list_display = BaseUserAdmin.list_display + ('has_seller_profile', 'has_customer_profile')

    def has_seller_profile(self, obj):
        return hasattr(obj, 'perfil_vendedor') and obj.perfil_vendedor is not None
    has_seller_profile.boolean = True
    has_seller_profile.short_description = 'Es Vendedor'

    def has_customer_profile(self, obj):
        return hasattr(obj, 'cliente_profile') and obj.cliente_profile is not None # Usar 'cliente_profile'
    has_customer_profile.boolean = True
    has_customer_profile.short_description = 'Es Cliente'

# Ya no necesitas admin.site.register(Direccion) porque usamos @admin.register para DireccionAdmin
# Y Cliente ya está registrado con @admin.register(Cliente)
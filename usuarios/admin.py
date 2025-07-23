# usuarios/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import PerfilVendedor, Cliente, Direccion
# Importa el modelo Tienda para poder referenciarlo en el admin
from tiendas.models import Tienda # ¡Importado para usar en PerfilVendedorAdmin!

# Inline para PerfilVendedor en el admin de User
# Permite editar el PerfilVendedor directamente desde la página de edición de un User
class PerfilVendedorInline(admin.StackedInline):
    model = PerfilVendedor
    can_delete = False # Evita que el PerfilVendedor se borre si se desasocia del User
    verbose_name_plural = 'Perfil de Vendedor'
    fields = ('telefono', 'rut', 'razon_social', 'giro', 'direccion_fiscal')
    # Si 'fecha_registro' existe en tu modelo PerfilVendedor y no debe ser editable:
    # readonly_fields = ('fecha_registro',) 

# Inline para Direccion dentro del admin de Cliente
# Permite ver y añadir direcciones directamente desde la vista de detalle de un Cliente
class DireccionInline(admin.TabularInline): # TabularInline es más compacto
    model = Direccion
    extra = 0 # No mostrar campos extra vacíos por defecto
    fields = [
        'etiqueta', 'calle', 'numero', 'departamento', 'block', 'nombre_condominio',
        'comuna', 'ciudad', 'region', 'codigo_postal', 'tipo_propiedad',
        'latitud', 'longitud', 'validada', 'tipo_direccion', 'principal'
    ]

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
        principal_address = obj.direcciones.filter(principal=True).first()
        if principal_address:
            parts = [f"{principal_address.calle} {principal_address.numero}"]
            if principal_address.departamento:
                parts.append(f"Depto. {principal_address.departamento}")
            parts.extend(filter(None, [principal_address.comuna, principal_address.ciudad]))
            return ", ".join(parts)
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


# --- CLASE ADMIN PARA PERFILVENDEDOR INDEPENDIENTE ---
@admin.register(PerfilVendedor)
class PerfilVendedorAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user', 
        'get_tiendas_nombres', # <-- ¡CAMBIADO! Método para mostrar los nombres de las tiendas
        'giro',
        'telefono',
        'razon_social',
    )
    # Ajuste search_fields para buscar por el nombre de las tiendas asociadas
    search_fields = (
        'user__username',
        'razon_social',
        'rut',
        'giro',
        'tiendas__nombre', # <-- Permite buscar por el nombre de la tienda relacionada
    )
    list_filter = ('giro',) 
    raw_id_fields = ('user',) 

    def get_tiendas_nombres(self, obj):
        # Un vendedor puede tener múltiples tiendas, así que listamos sus nombres
        # El related_name para Tienda a PerfilVendedor es 'tiendas'
        tiendas = obj.tiendas.all()
        if tiendas.exists():
            return ", ".join([tienda.nombre for tienda in tiendas])
        return "N/A"
    get_tiendas_nombres.short_description = 'Nombres de Tiendas'
    # Opcional: ordenar por el nombre de la primera tienda o por la cantidad de tiendas
    # get_tiendas_nombres.admin_order_field = 'tiendas__nombre' # Esto puede ser complicado con múltiples tiendas

# Desregistra el modelo User de Django si ya está registrado (para evitar errores)
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# Registra tu UserAdmin personalizado
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (PerfilVendedorInline,) # PerfilVendedor se sigue mostrando como inline en la vista de User
    list_display = BaseUserAdmin.list_display + ('has_seller_profile', 'has_customer_profile')

    def has_seller_profile(self, obj):
        return hasattr(obj, 'perfil_vendedor') and obj.perfil_vendedor is not None
    has_seller_profile.boolean = True
    has_seller_profile.short_description = 'Es Vendedor'

    def has_customer_profile(self, obj):
        # Asumiendo que el related_name en tu Cliente.user OneToOneField es 'cliente_profile'
        return hasattr(obj, 'cliente_profile') and obj.cliente_profile is not None 
    has_customer_profile.boolean = True
    has_customer_profile.short_description = 'Es Cliente'
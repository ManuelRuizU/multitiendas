# pedidos/admin.py
from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    # Los campos 'product', 'quantity', 'price_at_purchase' deben ser editables para el admin
    # si no calculas get_total_price en el admin. Si get_total_price es calculado,
    # entonces solo ese es readonly. Si no, todos son editables por defecto.
    # Vamos a añadir 'get_total_price' como readonly para que lo muestre.
    fields = ['product', 'quantity', 'price_at_purchase', 'get_total_price']
    readonly_fields = ['get_total_price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # ¡Campos actualizados para list_display!
    # 'user' ha sido reemplazado por 'cliente'
    # 'delivery_address' (Charfield) ha sido reemplazado por un ForeignKey a Direccion
    # Por eso, usaremos un método para mostrarla de forma legible.
    list_display = (
        'id',
        'tienda',
        'get_cliente_display', # Nuevo método para mostrar el cliente (usuario o invitado)
        'order_date',
        'total_amount',
        'delivery_cost',
        'status',
        'get_delivery_address_display', # Nuevo método para la dirección de envío
        'get_billing_address_display',  # Nuevo método para la dirección de facturación
    )
    
    list_filter = ('status', 'tienda', 'order_date')
    
    # ¡Campos de búsqueda actualizados!
    # Los campos 'user__username', 'delivery_address', 'customer_address' ya no existen
    search_fields = (
        'id__exact',
        'cliente__user__username',      # Busca por username si es un cliente registrado
        'cliente__nombre_completo',     # Busca por nombre completo del cliente (invitado o registrado)
        'cliente__email',               # Busca por email del cliente (invitado o registrado)
        'tienda__nombre',               # Busca por nombre de la tienda (asumo 'nombre' en Tienda)
        'delivery_address__calle',      # Busca por calle de la dirección de envío
        'billing_address__calle',       # Busca por calle de la dirección de facturación
    )
    
    date_hierarchy = 'order_date'
    inlines = [OrderItemInline]
    
    # ¡Campos de solo lectura actualizados!
    # 'user', 'delivery_address' (el CharField antiguo), 'delivery_latitude',
    # 'delivery_longitude', 'customer_address' ya no existen en el modelo Order.
    # Ahora 'delivery_address' y 'billing_address' son ForeignKeys a Direccion.
    readonly_fields = (
        'order_date',
        'subtotal_amount',
        'delivery_cost',
        'total_amount',
        # Si quieres que la dirección no se pueda modificar desde el admin
        # una vez que el pedido está hecho, podrías poner 'delivery_address', 'billing_address' aquí.
        # Sin embargo, a menudo es útil poder corregirlas.
        # Mantendremos los métodos display en readonly para mostrarlos de forma legible sin editar.
        'get_cliente_display',
        'get_delivery_address_display',
        'get_billing_address_display',
    )

    # --- Nuevos métodos para mostrar información en list_display y readonly_fields ---
    
    def get_cliente_display(self, obj):
        # Muestra el nombre de usuario si existe, de lo contrario, el nombre_completo/email del cliente invitado
        if obj.cliente:
            if obj.cliente.user:
                return obj.cliente.user.username
            return obj.cliente.nombre_completo or obj.cliente.email or "Invitado"
        return "Cliente Eliminado"
    get_cliente_display.short_description = "Cliente"


    def get_delivery_address_display(self, obj):
        if obj.delivery_address:
            # Reconstruye la dirección de envío de forma legible
            parts = [f"{obj.delivery_address.calle} {obj.delivery_address.numero}"]
            if obj.delivery_address.departamento:
                parts.append(f"Depto. {obj.delivery_address.departamento}")
            if obj.delivery_address.block:
                parts.append(f"Block {obj.delivery_address.block}")
            if obj.delivery_address.nombre_condominio:
                parts.append(f"Condominio {obj.delivery_address.nombre_condominio}")
            parts.extend([obj.delivery_address.comuna, obj.delivery_address.ciudad])
            return ", ".join(filter(None, parts))
        return "N/A"
    get_delivery_address_display.short_description = "Dirección de Envío"


    def get_billing_address_display(self, obj):
        if obj.billing_address:
            # Reconstruye la dirección de facturación de forma legible
            parts = [f"{obj.billing_address.calle} {obj.billing_address.numero}"]
            if obj.billing_address.departamento:
                parts.append(f"Depto. {obj.billing_address.departamento}")
            if obj.billing_address.block:
                parts.append(f"Block {obj.billing_address.block}")
            if obj.billing_address.nombre_condominio:
                parts.append(f"Condominio {obj.billing_address.nombre_condominio}")
            parts.extend([obj.billing_address.comuna, obj.billing_address.ciudad])
            return ", ".join(filter(None, parts))
        return "N/A"
    get_billing_address_display.short_description = "Dirección de Facturación"

# admin.site.register(OrderItem) # Esta línea es redundante si ya usas OrderItemInline

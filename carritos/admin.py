# carritos/admin.py
from django.contrib import admin
from .models import Carrito, GrupoCarrito, ItemCarrito


# ------------------------------------------------------------------
# INLINES
# ------------------------------------------------------------------
class ItemCarritoInline(admin.TabularInline):
    model = ItemCarrito
    extra = 0
    raw_id_fields = ['producto']
    fields = ('producto', 'cantidad', 'precio_unitario', 'subtotal_display')
    readonly_fields = ('subtotal_display',)

    def subtotal_display(self, obj):
        return f"${obj.subtotal:,.0f}" if obj.pk else "-"
    subtotal_display.short_description = 'Subtotal'


class GrupoCarritoInline(admin.TabularInline):
    model = GrupoCarrito
    extra = 0
    fields = (
        'tienda', 'metodo_pago', 'tipo_entrega',
        'hora_sugerida_cliente', 'hora_confirmada',
        'costo_envio', 'subtotal_display', 'total_display'
    )
    readonly_fields = ('subtotal_display', 'total_display')

    def subtotal_display(self, obj):
        return f"${obj.subtotal:,.0f}" if obj.pk else "-"
    subtotal_display.short_description = 'Subtotal'

    def total_display(self, obj):
        return f"${obj.total:,.0f}" if obj.pk else "-"
    total_display.short_description = 'Total'


# ------------------------------------------------------------------
# CARRITO ADMIN
# ------------------------------------------------------------------
@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'propietario_display',
        'total_tiendas', 'subtotal_global_display',
        'total_global_display', 'expirado',
        'fecha_creacion', 'fecha_actualizacion',
    )
    search_fields = ('usuario__username', 'guest_id')
    list_filter = ('fecha_creacion',)
    readonly_fields = (
        'fecha_creacion', 'fecha_actualizacion',
        'subtotal_global_display', 'costo_envio_global_display',
        'total_global_display',
    )
    inlines = [GrupoCarritoInline]

    def propietario_display(self, obj):
        return obj.usuario.username if obj.usuario else f"Invitado ({obj.guest_id[:8] if obj.guest_id else '?'}...)"
    propietario_display.short_description = 'Propietario'

    def subtotal_global_display(self, obj):
        return f"${obj.subtotal_global:,.0f}"
    subtotal_global_display.short_description = 'Subtotal global'

    def costo_envio_global_display(self, obj):
        return f"${obj.costo_envio_global:,.0f}"
    costo_envio_global_display.short_description = 'Costo envío global'

    def total_global_display(self, obj):
        return f"${obj.total_global:,.0f}"
    total_global_display.short_description = 'Total global'


# ------------------------------------------------------------------
# GRUPO CARRITO ADMIN
# ------------------------------------------------------------------
@admin.register(GrupoCarrito)
class GrupoCarritoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'carrito_display', 'tienda',
        'metodo_pago', 'tipo_entrega',
        'hora_sugerida_cliente', 'hora_confirmada',
        'costo_envio', 'subtotal_display', 'total_display',
        'total_items',
    )
    search_fields = (
        'carrito__usuario__username',
        'carrito__guest_id',
        'tienda__nombre',
    )
    list_filter = ('metodo_pago', 'tipo_entrega', 'tienda')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    inlines = [ItemCarritoInline]

    def carrito_display(self, obj):
        if obj.carrito.usuario:
            return f"User: {obj.carrito.usuario.username}"
        return f"Guest: {obj.carrito.guest_id[:8] if obj.carrito.guest_id else '?'}..."
    carrito_display.short_description = 'Carrito'

    def subtotal_display(self, obj):
        return f"${obj.subtotal:,.0f}"
    subtotal_display.short_description = 'Subtotal'

    def total_display(self, obj):
        return f"${obj.total:,.0f}"
    total_display.short_description = 'Total'


# ------------------------------------------------------------------
# ITEM CARRITO ADMIN
# ------------------------------------------------------------------
@admin.register(ItemCarrito)
class ItemCarritoAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'grupo_display',
        'producto', 'cantidad',
        'precio_unitario', 'subtotal_display',
        'stock_suficiente',
    )
    list_filter = ('grupo__tienda', 'grupo__metodo_pago')
    search_fields = (
        'producto__nombre',
        'grupo__carrito__usuario__username',
        'grupo__carrito__guest_id',
        'grupo__tienda__nombre',
    )
    raw_id_fields = ['producto']

    def grupo_display(self, obj):
        carrito = obj.grupo.carrito
        propietario = carrito.usuario.username if carrito.usuario else f"Guest {carrito.guest_id[:8] if carrito.guest_id else '?'}..."
        return f"{propietario} → {obj.grupo.tienda.nombre}"
    grupo_display.short_description = 'Grupo'

    def subtotal_display(self, obj):
        return f"${obj.subtotal:,.0f}"
    subtotal_display.short_description = 'Subtotal'

    def stock_suficiente(self, obj):
        return obj.stock_suficiente
    stock_suficiente.boolean = True
    stock_suficiente.short_description = 'Stock OK'
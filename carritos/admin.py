# carritos/admin.py
from django.contrib import admin
from .models import Carrito, ItemCarrito

# Opcional: Personalizar la vista en el admin
class ItemCarritoInline(admin.TabularInline):
    model = ItemCarrito
    extra = 0 # No mostrar campos extra vacíos por defecto
    raw_id_fields = ['producto'] # Útil si tienes muchos productos para buscar por ID

@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario_display', 'guest_id', 'fecha_creacion', 'fecha_actualizacion', 'total_items', 'subtotal_total')
    search_fields = ('usuario__username', 'guest_id')
    list_filter = ('fecha_creacion', 'fecha_actualizacion')
    inlines = [ItemCarritoInline] # Muestra los ítems del carrito directamente en la vista del carrito

    def usuario_display(self, obj):
        return obj.usuario.username if obj.usuario else "Invitado"
    usuario_display.short_description = 'Usuario'

@admin.register(ItemCarrito)
class ItemCarritoAdmin(admin.ModelAdmin):
    list_display = ('id', 'carrito_display', 'producto', 'cantidad', 'precio_unitario', 'subtotal')
    list_filter = ('carrito__fecha_creacion',)
    search_fields = ('producto__nombre', 'carrito__usuario__username', 'carrito__guest_id')
    raw_id_fields = ['carrito', 'producto'] # Útil para buscar carritos/productos por ID

    def carrito_display(self, obj):
        if obj.carrito.usuario:
            return f"User: {obj.carrito.usuario.username}"
        elif obj.carrito.guest_id:
            return f"Guest: {obj.carrito.guest_id[:8]}..."
        return "N/A"
    carrito_display.short_description = 'Carrito'

# pedidos/admin.py
from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price_at_purchase']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'tienda', 'user', 'order_date', 'total_amount', 'delivery_cost', 'status', 'delivery_address')
    list_filter = ('status', 'tienda', 'order_date')
    search_fields = ('id__exact', 'user__username', 'tienda__name', 'delivery_address')
    date_hierarchy = 'order_date'
    inlines = [OrderItemInline]
    readonly_fields = (
        'user', 'tienda', 'order_date', 'subtotal_amount', 'delivery_cost', 'total_amount',
        'delivery_address', 'delivery_latitude', 'delivery_longitude', 'customer_address'
    )

admin.site.register(OrderItem)
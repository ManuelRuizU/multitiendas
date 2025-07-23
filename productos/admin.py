# productos/admin.py
from django.contrib import admin
from django.utils.html import format_html # Importa para renderizar HTML (para la imagen del QR)
from .models import Categoria, SubCategoria, Producto

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id','nombre', 'tienda')
    list_filter = ('tienda',)
    search_fields = ('nombre',)

@admin.register(SubCategoria)
class SubCategoriaAdmin(admin.ModelAdmin):
    list_display = ('id','nombre', 'categoria', 'tienda')
    list_filter = ('categoria__tienda', 'categoria',)
    search_fields = ('nombre',)

    def tienda(self, obj):
        return obj.categoria.tienda.nombre
    tienda.short_description = 'Tienda'

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nombre',
        'tienda',
        'subcategoria',
        'sku', # <--- Añadido SKU a la vista de lista
        'codigo_barras_oficial', # <--- Añadido código de barras oficial a la vista de lista
        'precio_efectivo',
        'precio_tarjeta',
        'stock',
        'disponible',
        'display_qr_code', # <--- Añadido método para mostrar la imagen del QR
    )
    list_filter = ('tienda', 'subcategoria', 'disponible')
    search_fields = ('nombre', 'descripcion', 'tienda__nombre', 'sku', 'codigo_barras_oficial') # <--- Añadidos para búsqueda
    list_editable = ('precio_efectivo', 'precio_tarjeta', 'stock', 'disponible')
    raw_id_fields = ('tienda', 'subcategoria',)

    # Campos que se mostrarán en el formulario de edición/creación del producto
    fieldsets = (
        (None, {
            'fields': ('nombre', 'tienda', 'subcategoria', 'descripcion', 'imagen', 'disponible')
        }),
        ('Información de Precios y Stock', {
            'fields': ('precio_efectivo', 'precio_tarjeta', 'stock')
        }),
        ('Identificadores de Producto', {
            'fields': ('sku', 'codigo_barras_oficial', 'display_qr_code_form_field',) # <--- Muestra la imagen en el formulario
        }),
    )

    readonly_fields = ('display_qr_code', 'display_qr_code_form_field',) # <--- El QR es generado, no editable

    # Método para mostrar la imagen del QR en la lista de productos
    def display_qr_code(self, obj):
        if obj.imagen_qr_generado:
            return format_html('<img src="{}" width="50" height="50" />', obj.imagen_qr_generado.url)
        return "N/A"
    display_qr_code.short_description = 'Código QR'

    # Método para mostrar la imagen del QR en el formulario de edición (más grande)
    def display_qr_code_form_field(self, obj):
        if obj.imagen_qr_generado:
            return format_html('<img src="{}" width="150" height="150" />', obj.imagen_qr_generado.url)
        return "QR se generará al guardar"
    display_qr_code_form_field.short_description = 'Código QR Generado'
# productos/admin.py
from django.contrib import admin
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
    list_display = ('id','nombre', 'tienda', 'subcategoria', 'precio_efectivo', 'precio_tarjeta', 'stock', 'disponible')
    list_filter = ('tienda', 'subcategoria', 'disponible')
    search_fields = ('nombre', 'descripcion', 'tienda__nombre')
    list_editable = ('precio_efectivo', 'precio_tarjeta', 'stock', 'disponible')
    raw_id_fields = ('tienda', 'subcategoria',)
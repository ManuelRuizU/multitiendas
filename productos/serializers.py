# productos/serializers.py

from rest_framework import serializers
from .models import Categoria, SubCategoria, Producto


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'tienda', 'nombre', 'orden_display']
        read_only_fields = ['id']


class SubCategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategoria
        fields = ['id', 'categoria', 'nombre', 'orden_display']
        read_only_fields = ['id']


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = [
            'id', 'tienda', 'subcategoria',
            'nombre', 'descripcion',
            'sku', 'codigo_barras_oficial',
            'precio_efectivo', 'precio_tarjeta',
            'stock', 'disponible', 'stock_ilimitado',
            'imagen', 'imagen_qr_generado',
            'orden_display', 'loyverse_item_id',
        ]
        read_only_fields = ['id', 'imagen_qr_generado']

# productos/serializers.py
from rest_framework import serializers
from .models import Categoria, SubCategoria, Producto
from tiendas.serializers import TiendaSerializer # Para anidar la información de la tienda si es necesario

# Serializador para Categoria
class CategoriaSerializer(serializers.ModelSerializer):
    tienda_id = serializers.PrimaryKeyRelatedField(queryset=Categoria.objects.all(), source='tienda', write_only=True) # O Tienda.objects.all()

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'tienda', 'tienda_id']
        read_only_fields = ['id']
        extra_kwargs = {
            'tienda': {'read_only': True}
        }

# Serializador para SubCategoria
class SubCategoriaSerializer(serializers.ModelSerializer):
    categoria_id = serializers.PrimaryKeyRelatedField(queryset=SubCategoria.objects.all(), source='categoria', write_only=True) # O Categoria.objects.all()

    class Meta:
        model = SubCategoria
        fields = ['id', 'nombre', 'categoria', 'categoria_id']
        read_only_fields = ['id']
        extra_kwargs = {
            'categoria': {'read_only': True}
        }

# Serializador para Producto
class ProductoSerializer(serializers.ModelSerializer):
    tienda_id = serializers.PrimaryKeyRelatedField(queryset=Producto.objects.all(), source='tienda', write_only=True) # O Tienda.objects.all()
    subcategoria_id = serializers.PrimaryKeyRelatedField(queryset=Producto.objects.all(), source='subcategoria', allow_null=True, required=False, write_only=True) # O SubCategoria.objects.all()

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion', 'precio_efectivo', 'precio_tarjeta',
            'stock', 'imagen', 'disponible', 'tienda', 'tienda_id', 'subcategoria', 'subcategoria_id'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'tienda': {'read_only': True},
            'subcategoria': {'read_only': True}
        }
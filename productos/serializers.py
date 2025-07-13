# productos/serializers.py
from rest_framework import serializers
from .models import Categoria, SubCategoria, Producto
from tiendas.serializers import TiendaSerializer
from tiendas.models import Tienda 

# Serializador para Categoria
class CategoriaSerializer(serializers.ModelSerializer):
    tienda = serializers.PrimaryKeyRelatedField(queryset=Tienda.objects.all())

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'tienda']
        extra_kwargs = {
            'id': {'read_only': True},
        }

# Serializador para SubCategoria
class SubCategoriaSerializer(serializers.ModelSerializer):
    categoria = serializers.PrimaryKeyRelatedField(queryset=Categoria.objects.all())

    class Meta:
        model = SubCategoria
        fields = ['id', 'nombre', 'categoria']
        read_only_fields = ['id']

# Serializador para Producto (¡AQUÍ ESTÁN LOS CAMBIOS!)
class ProductoSerializer(serializers.ModelSerializer):
    tienda = serializers.PrimaryKeyRelatedField(queryset=Tienda.objects.all())
    subcategoria = serializers.PrimaryKeyRelatedField(queryset=SubCategoria.objects.all(), allow_null=True, required=False)

    # ¡ESTAS SON LAS LÍNEAS QUE DEBES AÑADIR O MODIFICAR!
    # Define explícitamente los campos de precio para controlar los decimales.
    precio_efectivo = serializers.DecimalField(max_digits=10, decimal_places=0) # <--- CAMBIO AQUÍ
    precio_tarjeta = serializers.DecimalField(max_digits=10, decimal_places=0)   # <--- CAMBIO AQUÍ

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion', 'precio_efectivo', 'precio_tarjeta',
            'stock', 'imagen', 'disponible',
            'tienda', 
            'subcategoria'
        ]
        read_only_fields = ['id']
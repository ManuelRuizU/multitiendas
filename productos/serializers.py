# productos/serializers.py
from rest_framework import serializers
from .models import Categoria, SubCategoria, Producto
from tiendas.serializers import TiendaSerializer
from tiendas.models import Tienda # Asegúrate de que esta importación esté

# Serializador para Categoria
class CategoriaSerializer(serializers.ModelSerializer):
    # Definimos 'tienda' explícitamente como un PrimaryKeyRelatedField
    # Esto le dice al serializador que espere un ID para este campo
    # Quitamos read_only_fields = ['id'] y usamos extra_kwargs para 'id'
    # y aseguramos que 'tienda' no esté en read_only_fields
    tienda = serializers.PrimaryKeyRelatedField(queryset=Tienda.objects.all())

    class Meta:
        model = Categoria
        # Incluimos 'tienda' directamente en los campos
        fields = ['id', 'nombre', 'tienda']
        # Definimos 'id' como solo lectura aquí
        extra_kwargs = {
            'id': {'read_only': True},
        }
        # Aseguramos que 'tienda' NO esté en read_only_fields si lo estuvo antes

# Serializador para SubCategoria (Aplicando el mismo patrón que CategoriaSerializer)
class SubCategoriaSerializer(serializers.ModelSerializer):
    # ¡CORREGIDO para usar 'categoria' directamente como PrimaryKeyRelatedField!
    categoria = serializers.PrimaryKeyRelatedField(queryset=Categoria.objects.all())

    class Meta:
        model = SubCategoria
        # Solo incluimos 'categoria', no 'categoria_id'
        fields = ['id', 'nombre', 'categoria']
        read_only_fields = ['id']
        # extra_kwargs para 'categoria' ya no es necesario aquí

# Serializador para Producto (Aplicando el mismo patrón)
class ProductoSerializer(serializers.ModelSerializer):
    # ¡CORREGIDO para usar 'tienda' directamente como PrimaryKeyRelatedField!
    tienda = serializers.PrimaryKeyRelatedField(queryset=Tienda.objects.all())
    # ¡CORREGIDO para usar 'subcategoria' directamente como PrimaryKeyRelatedField!
    subcategoria = serializers.PrimaryKeyRelatedField(queryset=SubCategoria.objects.all(), allow_null=True, required=False)

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion', 'precio_efectivo', 'precio_tarjeta',
            'stock', 'imagen', 'disponible',
            'tienda', # Solo 'tienda', no 'tienda_id'
            'subcategoria' # Solo 'subcategoria', no 'subcategoria_id'
        ]
        read_only_fields = ['id']
        # extra_kwargs ya no es necesario aquí para 'tienda' ni 'subcategoria'
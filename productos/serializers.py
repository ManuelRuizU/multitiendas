# productos/serializers.py
from rest_framework import serializers
from .models import Categoria, SubCategoria, Producto
from tiendas.models import Tienda # Importamos Tienda para queryset en CategoriaSerializer

# ------------------------------------------------------------------
# 1. CATEGORÍA SERIALIZER
# ------------------------------------------------------------------
class CategoriaSerializer(serializers.ModelSerializer):
    # Permite enviar el ID de la tienda al crear/actualizar
    tienda = serializers.PrimaryKeyRelatedField(queryset=Tienda.objects.all())
    # Campo de solo lectura para mostrar el nombre de la tienda en las respuestas GET
    tienda_nombre = serializers.ReadOnlyField(source='tienda.nombre')

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'tienda', 'tienda_nombre']
        read_only_fields = ['id', 'tienda_nombre'] # ID y nombre de tienda son de solo lectura

# ------------------------------------------------------------------
# 2. SUBCATEGORÍA SERIALIZER
# ------------------------------------------------------------------
class SubCategoriaSerializer(serializers.ModelSerializer):
    # Permite enviar el ID de la categoría al crear/actualizar
    categoria = serializers.PrimaryKeyRelatedField(queryset=Categoria.objects.all())
    # Campo de solo lectura para mostrar el nombre de la categoría en las respuestas GET
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')

    class Meta:
        model = SubCategoria
        fields = ['id', 'nombre', 'categoria', 'categoria_nombre']
        read_only_fields = ['id', 'categoria_nombre'] # ID y nombre de categoría son de solo lectura

# ------------------------------------------------------------------
# 3. PRODUCTO SERIALIZER
# ------------------------------------------------------------------
class ProductoSerializer(serializers.ModelSerializer):
    # Permite enviar el ID de la tienda y subcategoría al crear/actualizar
    tienda = serializers.PrimaryKeyRelatedField(queryset=Tienda.objects.all())
    subcategoria = serializers.PrimaryKeyRelatedField(queryset=SubCategoria.objects.all(), allow_null=True, required=False)

    # Campos de solo lectura para mostrar nombres legibles en las respuestas GET
    tienda_nombre = serializers.ReadOnlyField(source='tienda.nombre')
    subcategoria_nombre = serializers.ReadOnlyField(source='subcategoria.nombre')
    
    # Los campos de precio ya están definidos en el modelo como DecimalField.
    # Definirlos explícitamente aquí con decimal_places=0 es redundante a menos que
    # necesites validación o comportamiento específico que difiera del modelo.
    # Si tus precios son enteros, esto es correcto.
    precio_efectivo = serializers.DecimalField(max_digits=10, decimal_places=0) 
    precio_tarjeta = serializers.DecimalField(max_digits=10, decimal_places=0) 

    class Meta:
        model = Producto
        fields = [
            'id',
            'nombre',
            'descripcion',
            'precio_efectivo',
            'precio_tarjeta',
            'stock',
            'imagen',
            'disponible',
            'tienda',
            'tienda_nombre', # Campo de solo lectura para el nombre de la tienda
            'subcategoria',
            'subcategoria_nombre', # Campo de solo lectura para el nombre de la subcategoría
            # --- ¡Nuevos campos de identificación y QR! ---
            'sku', # Campo de lectura/escritura
            'codigo_barras_oficial', # Campo de lectura/escritura
            'imagen_qr_generado', # URL de la imagen del QR (solo lectura)
        ]
        read_only_fields = [
            'id',
            'tienda_nombre',
            'subcategoria_nombre',
            'imagen_qr_generado', # Este campo es generado por el modelo, no se envía en la petición
        ]



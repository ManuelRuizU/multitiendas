# productos/serializers.py
from rest_framework import serializers
from .models import Categoria, SubCategoria, Producto
from tiendas.models import Tienda


# ------------------------------------------------------------------
# 1. CATEGORÍA
# ------------------------------------------------------------------
class CategoriaSerializer(serializers.ModelSerializer):
    tienda = serializers.PrimaryKeyRelatedField(queryset=Tienda.objects.all())
    tienda_nombre = serializers.ReadOnlyField(source='tienda.nombre')

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'tienda', 'tienda_nombre', 'orden_display']
        read_only_fields = ['id', 'tienda_nombre']


# ------------------------------------------------------------------
# 2. SUBCATEGORÍA
# ------------------------------------------------------------------
class SubCategoriaSerializer(serializers.ModelSerializer):
    categoria = serializers.PrimaryKeyRelatedField(queryset=Categoria.objects.all())
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')

    class Meta:
        model = SubCategoria
        fields = ['id', 'nombre', 'categoria', 'categoria_nombre', 'orden_display']
        read_only_fields = ['id', 'categoria_nombre']


# ------------------------------------------------------------------
# 3. PRODUCTO — versión pública (para clientes)
# Sin datos internos como loyverse_item_id o SKU
# ------------------------------------------------------------------
class ProductoPublicoSerializer(serializers.ModelSerializer):
    tienda_nombre = serializers.ReadOnlyField(source='tienda.nombre')
    subcategoria_nombre = serializers.ReadOnlyField(source='subcategoria.nombre')
    precio_display = serializers.ReadOnlyField()
    tiene_recargo_tarjeta = serializers.ReadOnlyField()
    en_stock = serializers.ReadOnlyField()

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion',
            'precio_efectivo', 'precio_tarjeta',
            'precio_display', 'tiene_recargo_tarjeta',
            'stock', 'stock_ilimitado', 'en_stock',
            'imagen', 'imagen_qr_generado',
            'disponible', 'orden_display',
            'tienda', 'tienda_nombre',
            'subcategoria', 'subcategoria_nombre',
        ]
        read_only_fields = fields


# ------------------------------------------------------------------
# 4. PRODUCTO — versión completa (para el panel del vendedor)
# ------------------------------------------------------------------
class ProductoSerializer(serializers.ModelSerializer):
    tienda = serializers.PrimaryKeyRelatedField(queryset=Tienda.objects.all())
    subcategoria = serializers.PrimaryKeyRelatedField(
        queryset=SubCategoria.objects.all(),
        allow_null=True,
        required=False
    )
    tienda_nombre = serializers.ReadOnlyField(source='tienda.nombre')
    subcategoria_nombre = serializers.ReadOnlyField(source='subcategoria.nombre')
    precio_display = serializers.ReadOnlyField()
    tiene_recargo_tarjeta = serializers.ReadOnlyField()
    en_stock = serializers.ReadOnlyField()

    precio_efectivo = serializers.DecimalField(max_digits=10, decimal_places=0)
    precio_tarjeta = serializers.DecimalField(max_digits=10, decimal_places=0)

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion',
            'precio_efectivo', 'precio_tarjeta',
            'precio_display', 'tiene_recargo_tarjeta',
            'stock', 'stock_ilimitado', 'en_stock',
            'imagen', 'imagen_qr_generado',
            'disponible', 'orden_display',
            'sku', 'codigo_barras_oficial',
            'loyverse_item_id',
            'tienda', 'tienda_nombre',
            'subcategoria', 'subcategoria_nombre',
        ]
        read_only_fields = [
            'id', 'tienda_nombre', 'subcategoria_nombre',
            'imagen_qr_generado', 'precio_display',
            'tiene_recargo_tarjeta', 'en_stock',
        ]

    def validate(self, data):
        precio_efectivo = data.get('precio_efectivo')
        precio_tarjeta = data.get('precio_tarjeta')
        if precio_efectivo and precio_tarjeta:
            if precio_tarjeta < precio_efectivo:
                raise serializers.ValidationError({
                    'precio_tarjeta': (
                        "El precio tarjeta no puede ser menor al precio efectivo. "
                        "Si no hay recargo, ingresa el mismo valor."
                    )
                })
        return data
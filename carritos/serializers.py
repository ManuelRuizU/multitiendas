# carritos/serializers.py
from rest_framework import serializers
from .models import Carrito, GrupoCarrito, ItemCarrito
from productos.models import Producto
from tiendas.models import Tienda
from usuarios.models import Direccion


# ------------------------------------------------------------------
# 1. ITEM DE CARRITO
# ------------------------------------------------------------------
class ItemCarritoSerializer(serializers.ModelSerializer):
    # Lectura
    nombre_producto = serializers.CharField(source='producto.nombre', read_only=True)
    imagen_producto = serializers.ImageField(source='producto.imagen', read_only=True)
    precio_unitario = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    stock_suficiente = serializers.ReadOnlyField()
    precio_actual_efectivo = serializers.DecimalField(
        max_digits=10, decimal_places=0,
        read_only=True, source='producto.precio_efectivo'
    )
    precio_actual_tarjeta = serializers.DecimalField(
        max_digits=10, decimal_places=0,
        read_only=True, source='producto.precio_tarjeta'
    )

    # Lectura: expone el ID del producto para que el frontend pueda actualizar/eliminar
    producto = serializers.IntegerField(source='producto.id', read_only=True)

    # Escritura
    producto_id = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(),
        source='producto',
        write_only=True
    )

    class Meta:
        model = ItemCarrito
        fields = [
            'id',
            'producto',
            'producto_id',
            'nombre_producto',
            'imagen_producto',
            'cantidad',
            'precio_unitario',
            'subtotal',
            'precio_actual_efectivo',
            'precio_actual_tarjeta',
            'stock_suficiente',
        ]
        read_only_fields = [
            'id', 'nombre_producto', 'imagen_producto',
            'precio_unitario', 'subtotal',
            'precio_actual_efectivo', 'precio_actual_tarjeta',
            'stock_suficiente',
        ]

    def validate(self, data):
        if 'cantidad' in data and data['cantidad'] < 0:
            raise serializers.ValidationError("La cantidad no puede ser negativa.")
        return data


# ------------------------------------------------------------------
# 2. GRUPO DE CARRITO
# ------------------------------------------------------------------
class GrupoCarritoSerializer(serializers.ModelSerializer):
    items = ItemCarritoSerializer(many=True, read_only=True)

    # Info de la tienda
    tienda_id = serializers.IntegerField(source='tienda.id', read_only=True)
    tienda_nombre = serializers.CharField(source='tienda.nombre', read_only=True)
    tienda_logo = serializers.ImageField(source='tienda.logo', read_only=True)
    tienda_whatsapp_url = serializers.CharField(
        source='tienda.propietario_perfil.whatsapp_url',
        read_only=True
    )
    metodos_pago_tienda = serializers.ListField(
        source='tienda.metodos_pago_activos',
        read_only=True
    )

    # Propiedades calculadas
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    cantidad_total_productos = serializers.IntegerField(read_only=True)
    hora_entrega_display = serializers.TimeField(read_only=True, allow_null=True)
    hora_modificada_por_emprendedor = serializers.BooleanField(read_only=True)

    # Campos editables
    metodo_pago = serializers.ChoiceField(
        choices=GrupoCarrito.METODO_PAGO_CHOICES,
        required=False
    )
    tipo_entrega = serializers.ChoiceField(
        choices=GrupoCarrito.TIPO_ENTREGA_CHOICES,
        required=False
    )
    hora_sugerida_cliente = serializers.TimeField(required=False, allow_null=True)
    notas_cliente = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    direccion_entrega = serializers.PrimaryKeyRelatedField(
        queryset=Direccion.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = GrupoCarrito
        fields = [
            'id',
            'tienda_id', 'tienda_nombre', 'tienda_logo',
            'tienda_whatsapp_url', 'metodos_pago_tienda',
            'metodo_pago', 'tipo_entrega',
            'hora_sugerida_cliente', 'hora_confirmada',
            'hora_entrega_display', 'hora_modificada_por_emprendedor',
            'direccion_entrega',
            'costo_envio', 'notas_cliente',
            'subtotal', 'total',
            'total_items', 'cantidad_total_productos',
            'items',
            'fecha_creacion', 'fecha_actualizacion',
        ]
        read_only_fields = [
            'id', 'tienda_id', 'tienda_nombre', 'tienda_logo',
            'tienda_whatsapp_url', 'metodos_pago_tienda',
            'hora_confirmada', 'hora_entrega_display',
            'hora_modificada_por_emprendedor',
            'costo_envio', 'subtotal', 'total',
            'total_items', 'cantidad_total_productos',
            'fecha_creacion', 'fecha_actualizacion',
        ]


# ------------------------------------------------------------------
# 3. CARRITO COMPLETO
# ------------------------------------------------------------------
class CarritoSerializer(serializers.ModelSerializer):
    grupos = GrupoCarritoSerializer(many=True, read_only=True)

    # Propiedades globales
    total_tiendas = serializers.IntegerField(read_only=True)
    subtotal_global = serializers.DecimalField(
        max_digits=10, decimal_places=0, read_only=True
    )
    costo_envio_global = serializers.DecimalField(
        max_digits=10, decimal_places=0, read_only=True
    )
    total_global = serializers.DecimalField(
        max_digits=10, decimal_places=0, read_only=True
    )
    esta_vacio = serializers.ReadOnlyField()
    expirado = serializers.ReadOnlyField()
    tiene_retiros_simultaneos = serializers.ReadOnlyField()

    # Info del propietario
    usuario_username = serializers.CharField(
        source='usuario.username',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = Carrito
        fields = [
            'id',
            'usuario_username',
            'guest_id',
            'fecha_creacion',
            'fecha_actualizacion',
            'total_tiendas',
            'subtotal_global',
            'costo_envio_global',
            'total_global',
            'esta_vacio',
            'expirado',
            'tiene_retiros_simultaneos',
            'grupos',
        ]
        read_only_fields = [
            'id', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_username', 'guest_id',
            'total_tiendas', 'subtotal_global',
            'costo_envio_global', 'total_global',
            'esta_vacio', 'expirado', 'tiene_retiros_simultaneos',
        ]
# carritos/serializers.py
from rest_framework import serializers
from .models import Carrito, ItemCarrito
from productos.models import Producto # Necesario para validar productos
from productos.serializers import ProductoSerializer # Para anidar detalles del producto

class ItemCarritoSerializer(serializers.ModelSerializer):
    # Campo para mostrar el nombre del producto (solo lectura)
    nombre_producto = serializers.CharField(source='producto.nombre', read_only=True)
    # Campo para el ID del producto, que se usará para crear/actualizar el item
    producto_id = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(), source='producto', write_only=True
    )
    # Campo para mostrar el precio unitario actual del producto (solo lectura)
    # Esto es útil para que el frontend sepa el precio que se está aplicando.
    precio_unitario_actual = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source='producto.precio_efectivo' # O el precio que decidas mostrar por defecto
    )
    # Puedes añadir precio_tarjeta_actual si el frontend lo necesita para sincronizar

    class Meta:
        model = ItemCarrito
        fields = [
            'id', 'producto_id', 'nombre_producto', 'cantidad', 'precio_unitario',
            'subtotal', 'precio_unitario_actual'
        ]
        read_only_fields = ['id', 'precio_unitario', 'subtotal'] # precio_unitario se setea en el save del modelo

    def validate(self, data):
        # Asegurarse de que la cantidad sea positiva
        if data['cantidad'] <= 0:
            raise serializers.ValidationError("La cantidad debe ser un número positivo.")
        return data

class CarritoSerializer(serializers.ModelSerializer):
    # Anidar los ítems del carrito para que se muestren junto con el carrito
    items = ItemCarritoSerializer(many=True, read_only=True)
    # Propiedades calculadas del modelo Carrito
    total_items = serializers.IntegerField(read_only=True)
    cantidad_total_productos = serializers.IntegerField(read_only=True)
    subtotal_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    # El campo 'usuario' es de solo lectura y mostrará el username
    usuario = serializers.CharField(source='usuario.username', read_only=True)
    
    class Meta:
        model = Carrito
        fields = [
            'id', 'usuario', 'guest_id', 'fecha_creacion', 'fecha_actualizacion',
            'items', 'total_items', 'cantidad_total_productos', 'subtotal_total'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion', 'usuario']

    def validate(self, data):
        # Validación para asegurar que al menos 'usuario' o 'guest_id' estén presentes
        # Esto es redundante con el clean() del modelo, pero es una buena práctica validarlo también en el serializador.
        if not data.get('usuario') and not data.get('guest_id'):
            raise serializers.ValidationError("Un carrito debe estar asociado a un usuario o a un guest_id.")
        if data.get('usuario') and data.get('guest_id'):
            raise serializers.ValidationError("Un carrito no puede tener un usuario y un guest_id al mismo tiempo.")
        return data
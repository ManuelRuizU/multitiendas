# carritos/serializers.py
from rest_framework import serializers
from .models import Carrito, ItemCarrito
from productos.models import Producto

class ItemCarritoSerializer(serializers.ModelSerializer):
    nombre_producto = serializers.CharField(source='producto.nombre', read_only=True)
    producto_id = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(), source='producto', write_only=True
    )
    precio_unitario_actual = serializers.DecimalField(
        max_digits=10, decimal_places=0, read_only=True, source='producto.precio_efectivo'
    )
    precio_unitario = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)

    # ¡AÑADE O MODIFICA ESTA LÍNEA!
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True) # <--- CAMBIO AQUÍ

    class Meta:
        model = ItemCarrito
        fields = [
            'id', 'producto_id', 'nombre_producto', 'cantidad', 
            'precio_unitario', 
            'subtotal', 
            'precio_unitario_actual'
        ]
        # 'subtotal' ya es read_only=True en su definición, así que no necesita estar aquí.
        read_only_fields = ['id', 'nombre_producto', 'precio_unitario_actual'] 

    def validate(self, data):
        if data['cantidad'] <= 0:
            raise serializers.ValidationError("La cantidad debe ser un número positivo.")
        return data

class CarritoSerializer(serializers.ModelSerializer):
    items = ItemCarritoSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    cantidad_total_productos = serializers.IntegerField(read_only=True)
    # ¡AÑADE O MODIFICA ESTA LÍNEA!
    subtotal_total = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True) # <--- CAMBIO AQUÍ

    usuario = serializers.CharField(source='usuario.username', read_only=True)
    
    class Meta:
        model = Carrito
        fields = [
            'id', 'usuario', 'guest_id', 'fecha_creacion', 'fecha_actualizacion',
            'items', 'total_items', 'cantidad_total_productos', 'subtotal_total'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion', 'usuario']

    def validate(self, data):
        if not data.get('usuario') and not data.get('guest_id'):
            raise serializers.ValidationError("Un carrito debe estar asociado a un usuario o a un guest_id.")
        if data.get('usuario') and data.get('guest_id'):
            raise serializers.ValidationError("Un carrito no puede tener un usuario y un guest_id al mismo tiempo.")
        return data
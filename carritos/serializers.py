# carritos/serializers.py
from rest_framework import serializers
from .models import Carrito, ItemCarrito
from productos.models import Producto

class ItemCarritoSerializer(serializers.ModelSerializer):
    # Campo de solo lectura para mostrar el nombre del producto
    nombre_producto = serializers.CharField(source='producto.nombre', read_only=True)
    # Campo de escritura para recibir el ID del producto
    producto_id = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(), source='producto', write_only=True
    )
    # Campo de solo lectura para mostrar el precio actual del producto (desde el modelo Producto)
    precio_unitario_actual = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, source='producto.precio_efectivo' # Asegúrate que decimal_places coincida
    )
    # Campo de solo lectura para el precio unitario guardado en el ItemCarrito
    precio_unitario = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True) # Asegúrate que decimal_places coincida

    # Campo de solo lectura para el subtotal calculado del ítem
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True) # Asegúrate que decimal_places coincida

    class Meta:
        model = ItemCarrito
        fields = [
            'id', 'producto_id', 'nombre_producto', 'cantidad', 
            'precio_unitario', # Precio al que se añadió el producto al carrito
            'subtotal',        # Subtotal de este ítem (cantidad * precio_unitario)
            'precio_unitario_actual' # Precio actual del producto en el catálogo
        ]
        read_only_fields = ['id', 'nombre_producto', 'precio_unitario', 'subtotal', 'precio_unitario_actual'] 

    def validate(self, data):
        # La validación de cantidad <= 0 se moverá a la vista para manejar la eliminación.
        # Aquí solo validamos que la cantidad sea positiva para la creación/actualización normal.
        if 'cantidad' in data and data['cantidad'] < 0:
            raise serializers.ValidationError("La cantidad no puede ser negativa.")
        return data

class CarritoSerializer(serializers.ModelSerializer):
    # Serializador anidado para los ítems del carrito (solo lectura)
    items = ItemCarritoSerializer(many=True, read_only=True)
    # Propiedades calculadas del carrito (solo lectura)
    total_items = serializers.IntegerField(read_only=True)
    cantidad_total_productos = serializers.IntegerField(read_only=True)
    subtotal_total = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True) # Asegúrate que decimal_places coincida

    # Campo de solo lectura para mostrar el username del usuario asociado
    usuario = serializers.CharField(source='usuario.username', read_only=True)
    
    class Meta:
        model = Carrito
        fields = [
            'id', 'usuario', 'guest_id', 'fecha_creacion', 'fecha_actualizacion',
            'items', 'total_items', 'cantidad_total_productos', 'subtotal_total'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion', 'usuario']

    def validate(self, data):
        # Esta validación es crucial para el modelo de Carrito
        if data.get('usuario') and data.get('guest_id'):
            raise serializers.ValidationError("Un carrito no puede tener un usuario asociado y un guest_id al mismo tiempo.")
        # No es necesario validar 'not data.get('usuario') and not data.get('guest_id')' aquí,
        # ya que la vista se encarga de crear el carrito con uno u otro.
        return data


    
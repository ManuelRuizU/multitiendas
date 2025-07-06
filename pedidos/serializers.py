# pedidos/serializers.py
from rest_framework import serializers 

# Importamos los MODELOS que se necesitan para las relaciones de los serializadores
from .models import Order, OrderItem # Modelos de la propia app 'pedidos'
from django.contrib.auth.models import User # Modelo User de Django
from tiendas.models import Tienda # Modelo Tienda de la app 'tiendas'
from productos.models import Producto # ¡IMPORTACIÓN CRUCIAL DEL MODELO PRODUCTO!
from usuarios.models import Direccion # Modelo Direccion de la app 'usuarios'

# Importamos los SERIALIZADORES anidados o para campos relacionados (si se usan)
from usuarios.serializers import DireccionSerializer, UserSerializer
from tiendas.serializers import TiendaSerializer
from productos.serializers import ProductoSerializer


# Serializador para OrderItem (anidado en OrderSerializer)
class OrderItemSerializer(serializers.ModelSerializer):
    # 'product' aquí es para mostrar los detalles del producto al LEER el pedido
    # Se usa ProductoSerializer para que retorne un objeto JSON del producto, no solo su ID
    product = ProductoSerializer(read_only=True)

    # 'product_id' es para ESCRIBIR (crear/actualizar) un OrderItem.
    # Permite enviar solo el ID del producto. La queryset apunta al MODELO Producto.
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(), # Aquí necesitas el MODELO Producto
        source='product',
        write_only=True
    )

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'price_at_purchase']
        read_only_fields = ['id', 'price_at_purchase'] # price_at_purchase se captura al momento de la compra

# Serializador para Order
class OrderSerializer(serializers.ModelSerializer):
    # Para LEER (GET), mostramos los detalles completos del usuario, tienda y dirección
    user = UserSerializer(read_only=True)
    tienda = TiendaSerializer(read_only=True)
    customer_address = DireccionSerializer(read_only=True) # Detalles de la dirección guardada del cliente

    # Para ESCRIBIR (POST/PUT), permitimos enviar solo los IDs
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    tienda_id = serializers.PrimaryKeyRelatedField(
        queryset=Tienda.objects.all(),
        source='tienda',
        write_only=True
    )
    customer_address_id = serializers.PrimaryKeyRelatedField(
        queryset=Direccion.objects.all(), # Aquí necesitas el MODELO Direccion
        source='customer_address',
        write_only=True,
        allow_null=True,
        required=False
    )

    # Para los ítems del pedido. Usamos OrderItemSerializer.
    # 'many=True' porque un pedido tiene muchos ítems.
    # 'read_only=True' significa que no se pueden crear/actualizar ítems directamente a través de este campo
    # en la creación del OrderSerializer. La lógica de creación de items se maneja en la vista.
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_id', 'tienda', 'tienda_id', 'order_date', 'status',
            'subtotal_amount', 'delivery_cost', 'total_amount',
            'delivery_address', 'delivery_latitude', 'delivery_longitude',
            'customer_notes', 'tienda_notes', 'customer_address', 'customer_address_id',
            'items' # Incluimos los ítems para la respuesta GET
        ]
        read_only_fields = [
            'id', 'order_date', 'subtotal_amount', 'delivery_cost', 'total_amount',
            # 'user', 'tienda', 'customer_address' se mantienen como read_only_fields si sus versiones
            # *_id son las que se usarán para escritura.
            # Los que ya están como read_only=True en sus definiciones de campo no necesitan estar aquí.
            # Puedes dejar 'user', 'tienda', 'customer_address' aquí si quieres asegurarte.
        ]
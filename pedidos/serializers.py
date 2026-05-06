# pedidos/serializers.py
# versión ajustada y corregida con cálculo de envío 16/8/2025

from rest_framework import serializers 
from rest_framework.serializers import ValidationError
from django.db import transaction 
from decimal import Decimal
import requests
import os

# Importamos los MODELOS que se necesitan para las relaciones de los serializadores
from .models import Order, OrderItem 
from tiendas.models import Tienda 
from productos.models import Producto 
from usuarios.models import Cliente, Direccion # Importamos Cliente y Direccion

# Importamos los SERIALIZADORES anidados o para campos relacionados (si se usan)
from usuarios.serializers import DireccionSerializer, ClienteSerializer 
from tiendas.serializers import TiendaSerializer
from productos.serializers import ProductoSerializer


# Función auxiliar para calcular la distancia con la API de Google Maps
def get_google_maps_distance(origin_lat, origin_lng, destination_lat, destination_lng):
    """
    Calcula la distancia en kilómetros entre dos puntos geográficos usando la
    API de Google Maps Distance Matrix.
    """
    # IMPORTANTE: Asegúrate de tener la variable de entorno GOOGLE_MAPS_API_KEY configurada
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY no está configurada en las variables de entorno.")

    origin = f"{origin_lat},{origin_lng}"
    destination = f"{destination_lat},{destination_lng}"
    
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&units=metric&key={api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status() # Lanza un error si la solicitud no es exitosa
        data = response.json()
        
        # Validamos que la respuesta contenga los datos esperados
        if data['status'] == 'OK' and data['rows'][0]['elements'][0]['status'] == 'OK':
            distance_meters = data['rows'][0]['elements'][0]['distance']['value']
            return distance_meters / 1000.0 # Retorna la distancia en kilómetros
        else:
            print("Error en la respuesta de la API de Google Maps:", data)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error al llamar a la API de Google Maps: {e}")
        return None
    except (KeyError, IndexError) as e:
        print(f"Estructura de respuesta inesperada de la API de Google Maps: {e}")
        return None


# Serializador para OrderItem (anidado en OrderSerializer)
class OrderItemSerializer(serializers.ModelSerializer):
    # 'product' aquí es para mostrar los detalles del producto al LEER el pedido
    product = ProductoSerializer(read_only=True)

    # 'product_id' es para ESCRIBIR (crear/actualizar) un OrderItem.
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(), 
        source='product',
        write_only=True
    )
    
    # Campo para la cantidad del producto
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'price_at_purchase']
        read_only_fields = ['id', 'price_at_purchase'] 


# Serializador para Order - Version Principal (para usuarios registrados)
class OrderSerializer(serializers.ModelSerializer):
    # Para LEER (GET), mostramos los detalles completos del cliente, tienda y direcciones
    # Usamos ClienteSerializer para obtener más detalles del cliente si es necesario
    cliente = ClienteSerializer(read_only=True) 
    tienda = TiendaSerializer(read_only=True)
    delivery_address = DireccionSerializer(read_only=True) # Detalles de la dirección de envío
    billing_address = DireccionSerializer(read_only=True) # Detalles de la dirección de facturación (opcional)

    # Para ESCRIBIR (POST/PUT), permitimos enviar solo los IDs
    # El cliente_id no se envía, se toma del usuario autenticado en la vista.
    tienda_id = serializers.PrimaryKeyRelatedField(
        queryset=Tienda.objects.all(),
        source='tienda',
        write_only=True
    )
    delivery_address_id = serializers.PrimaryKeyRelatedField(
        queryset=Direccion.objects.all(), 
        source='delivery_address',
        write_only=True
    )
    billing_address_id = serializers.PrimaryKeyRelatedField(
        queryset=Direccion.objects.all(), 
        source='billing_address',
        write_only=True,
        allow_null=True,
        required=False
    )
    
    # Usamos este campo de escritura para procesar los ítems del pedido
    items = OrderItemSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'cliente', 'tienda', 'tienda_id', 'order_date', 'status',
            'subtotal_amount', 'delivery_cost', 'total_amount',
            'delivery_address', 'delivery_address_id', 'billing_address', 
            'billing_address_id', 'customer_notes', 'tienda_notes', 'items'
        ]
        read_only_fields = [
            'id', 'order_date', 'status', 'cliente',
            'subtotal_amount', 'delivery_cost', 'total_amount',
        ]
        
    def validate_items(self, items_data):
        if not items_data:
            raise serializers.ValidationError("El pedido debe contener al menos un ítem.")
        return items_data

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        with transaction.atomic():
            tienda_obj = validated_data['tienda']
            delivery_address_obj = validated_data['delivery_address']
            
            subtotal_amount = Decimal('0.00')
            items_to_create = []

            # 1. Validar ítems, calcular subtotal y verificar stock
            for item_data in items_data:
                product = item_data['product']
                quantity = item_data['quantity']

                if product.tienda != tienda_obj:
                    raise serializers.ValidationError(
                        f"El producto con ID {product.id} no pertenece a la tienda seleccionada."
                    )
                
                if product.stock < quantity:
                    raise serializers.ValidationError(
                        f"Stock insuficiente para {product.nombre}. Disponible: {product.stock}"
                    )
                
                price_at_purchase = product.precio_efectivo
                subtotal_amount += price_at_purchase * quantity
                
                items_to_create.append(
                    {'product': product, 'quantity': quantity, 'price_at_purchase': price_at_purchase}
                )
            
            # --- Lógica para el cálculo del costo de envío ---
            # 2. Calcular la distancia usando las coordenadas de la tienda y la dirección de entrega
            if tienda_obj.latitud and tienda_obj.longitud and delivery_address_obj.latitud and delivery_address_obj.longitud:
                distance_in_km = get_google_maps_distance(
                    tienda_obj.latitud, tienda_obj.longitud,
                    delivery_address_obj.latitud, delivery_address_obj.longitud
                )
            else:
                # Si falta alguna coordenada, asignamos 0 y un costo de envío predeterminado o un error
                distance_in_km = 0
                print("ADVERTENCIA: Faltan coordenadas de latitud/longitud para el cálculo de envío.")

            delivery_cost = Decimal('0.00')

            # 3. Recorrer los radios de envío de la tienda para encontrar el costo adecuado
            # Asumimos que `radios_envio` es un campo ManyToMany o similar
            # Primero, ordenamos los radios por distancia para encontrar el primero que cumple la condición
            if distance_in_km is not None and tienda_obj.radios_envio.exists():
                radios_ordenados = tienda_obj.radios_envio.order_by('distancia_max_km')
                for radio in radios_ordenados:
                    if distance_in_km <= float(radio.distancia_max_km):
                        delivery_cost = radio.costo_envio
                        break
                else:
                    # Si la distancia es mayor que todos los radios, podemos lanzar un error
                    raise ValidationError("La dirección de entrega está fuera del radio de envío de la tienda.")
            # --- Fin de la lógica para el cálculo del costo de envío ---

            total_amount = subtotal_amount + delivery_cost
            
            # 4. Crear el objeto Order
            order = Order.objects.create(
                subtotal_amount=subtotal_amount,
                delivery_cost=delivery_cost,
                total_amount=total_amount,
                **validated_data
            )
            
            # 5. Crear los OrderItems y reducir stock
            for item_to_create in items_to_create:
                OrderItem.objects.create(order=order, **item_to_create)
                item_to_create['product'].stock -= item_to_create['quantity']
                item_to_create['product'].save()
                
            return order

# Serializador para Order - Version para invitados
class OrderInvitadoSerializer(OrderSerializer):
    # Campos adicionales requeridos para usuarios invitados
    guest_nombre = serializers.CharField(max_length=100, write_only=True)
    guest_telefono = serializers.CharField(max_length=20, write_only=True)
    guest_email = serializers.EmailField(write_only=True, required=False)

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + ['guest_nombre', 'guest_telefono', 'guest_email']
        read_only_fields = OrderSerializer.Meta.read_only_fields + ['cliente']

    def create(self, validated_data):
        guest_nombre = validated_data.pop('guest_nombre')
        guest_telefono = validated_data.pop('guest_telefono')
        guest_email = validated_data.pop('guest_email', '')
        
        validated_data['customer_notes'] = (
            f"Pedido de Invitado: {guest_nombre} ({guest_telefono}) - Email: {guest_email}. "
            f"Notas originales: {validated_data.get('customer_notes', '')}"
        )
        
        return super().create(validated_data)




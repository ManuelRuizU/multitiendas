# pedidos/serializers.py

from rest_framework import serializers
from rest_framework.serializers import ValidationError
from django.db import transaction
from django.db.models import F
from decimal import Decimal

from .models import Order, OrderItem
from tiendas.models import Tienda
from productos.models import Producto
from usuarios.models import Cliente, Direccion

from usuarios.serializers import DireccionSerializer, ClienteSerializer
from tiendas.serializers import TiendaSerializer
from productos.serializers import ProductoSerializer


# ------------------------------------------------------------------
# SERIALIZADOR DE ÍTEM DE PEDIDO
# ------------------------------------------------------------------
class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductoSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(),
        source='product',
        write_only=True
    )
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'price_at_purchase']
        read_only_fields = ['id', 'price_at_purchase']


# ------------------------------------------------------------------
# SERIALIZADOR PRINCIPAL DE PEDIDO (usuarios registrados)
# ------------------------------------------------------------------
class OrderSerializer(serializers.ModelSerializer):
    # Lectura: representaciones completas
    cliente = ClienteSerializer(read_only=True)
    tienda = TiendaSerializer(read_only=True)
    delivery_address = DireccionSerializer(read_only=True)
    billing_address = DireccionSerializer(read_only=True)

    # Escritura: solo IDs
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
    items = OrderItemSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'cliente', 'tienda', 'tienda_id', 'order_date', 'status',
            'subtotal_amount', 'delivery_cost', 'total_amount',
            'delivery_address', 'delivery_address_id',
            'billing_address', 'billing_address_id',
            'customer_notes', 'tienda_notes', 'items',
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

            # FIX 4 — Validar tienda activa
            if not tienda_obj.activo:
                raise serializers.ValidationError(
                    "La tienda no está disponible actualmente."
                )

            # FIX 3 — Bloquear filas de productos con SELECT FOR UPDATE
            # Previene condición de carrera: dos pedidos simultáneos leen el
            # mismo stock, ambos pasan la validación y dejan stock negativo.
            product_ids = [item['product'].id for item in items_data]
            productos_locked = {
                p.id: p
                for p in Producto.objects.select_for_update().filter(id__in=product_ids)
            }

            subtotal_amount = Decimal('0')
            items_to_create = []

            for item_data in items_data:
                product = productos_locked[item_data['product'].id]
                quantity = item_data['quantity']

                if product.tienda != tienda_obj:
                    raise serializers.ValidationError(
                        f"El producto '{product.nombre}' no pertenece a la tienda seleccionada."
                    )

                # FIX 3 — Respetar stock_ilimitado al validar stock
                if not product.stock_ilimitado and product.stock < quantity:
                    raise serializers.ValidationError(
                        f"Stock insuficiente para '{product.nombre}'. "
                        f"Disponible: {product.stock}."
                    )

                price_at_purchase = product.precio_efectivo
                subtotal_amount += price_at_purchase * quantity
                items_to_create.append({
                    'product': product,
                    'quantity': quantity,
                    'price_at_purchase': price_at_purchase,
                })

            # FIX 2 — Cálculo de envío centralizado en Tienda.calcular_costo_envio()
            # Usa Haversine + cuadrantes con prioridad correcta.
            # Se elimina la llamada a Google Maps Distance Matrix API.
            delivery_cost = Decimal('0')
            if delivery_address_obj.latitud and delivery_address_obj.longitud:
                costo = tienda_obj.calcular_costo_envio(
                    delivery_address_obj.latitud,
                    delivery_address_obj.longitud,
                )
                if costo is None:
                    raise serializers.ValidationError(
                        "La dirección de entrega está fuera del área de despacho de esta tienda."
                    )
                delivery_cost = costo
            # Si faltan coordenadas se deja delivery_cost = 0 (sin despacho calculable)

            total_amount = subtotal_amount + delivery_cost

            # Crear el Order con montos ya calculados.
            # Order.save() NO recalcula en la creación inicial (ver pedidos/models.py).
            order = Order.objects.create(
                subtotal_amount=subtotal_amount,
                delivery_cost=delivery_cost,
                total_amount=total_amount,
                **validated_data
            )

            # FIX 3 — Crear OrderItems y descontar stock de forma atómica con F()
            # F('stock') - quantity se ejecuta en una sola sentencia UPDATE en BD,
            # sin leer el valor a Python, garantizando atomicidad real.
            for item_to_create in items_to_create:
                OrderItem.objects.create(order=order, **item_to_create)
                if not item_to_create['product'].stock_ilimitado:
                    Producto.objects.filter(id=item_to_create['product'].id).update(
                        stock=F('stock') - item_to_create['quantity']
                    )

            # FIX 1 — Vaciar el carrito del usuario autenticado si pertenece a esta tienda
            request = self.context.get('request')
            if request and request.user.is_authenticated:
                try:
                    carrito = request.user.carrito
                    if carrito.tienda_id == tienda_obj.id:
                        carrito.items.all().delete()
                except Exception:
                    pass  # Sin carrito activo: no es un error

            return order


# ------------------------------------------------------------------
# SERIALIZADOR DE PEDIDO PARA INVITADOS
# ------------------------------------------------------------------
class OrderInvitadoSerializer(OrderSerializer):
    # Datos del cliente invitado
    guest_nombre = serializers.CharField(max_length=150, write_only=True)
    guest_apellido = serializers.CharField(max_length=150, write_only=True, required=False, allow_blank=True)
    guest_telefono = serializers.CharField(max_length=30, write_only=True)
    guest_email = serializers.EmailField(write_only=True, required=False, allow_null=True)

    # Dirección inline — obligatoria para invitados (no tienen direcciones guardadas)
    calle = serializers.CharField(max_length=255, write_only=True)
    numero = serializers.CharField(max_length=20, write_only=True)
    comuna = serializers.CharField(max_length=100, write_only=True)
    ciudad = serializers.CharField(max_length=100, write_only=True)
    region = serializers.CharField(max_length=100, write_only=True)
    latitud = serializers.DecimalField(max_digits=9, decimal_places=6, write_only=True, required=False, allow_null=True)
    longitud = serializers.DecimalField(max_digits=9, decimal_places=6, write_only=True, required=False, allow_null=True)

    # delivery_address_id es opcional para invitados: se crea inline desde los campos de dirección
    delivery_address_id = serializers.PrimaryKeyRelatedField(
        queryset=Direccion.objects.all(),
        source='delivery_address',
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + [
            'guest_nombre', 'guest_apellido', 'guest_telefono', 'guest_email',
            'calle', 'numero', 'comuna', 'ciudad', 'region', 'latitud', 'longitud',
        ]
        read_only_fields = OrderSerializer.Meta.read_only_fields + ['cliente']

    def create(self, validated_data):
        guest_nombre = validated_data.pop('guest_nombre')
        guest_apellido = validated_data.pop('guest_apellido', None) or None
        guest_telefono = validated_data.pop('guest_telefono')
        guest_email = validated_data.pop('guest_email', None)
        calle = validated_data.pop('calle')
        numero = validated_data.pop('numero')
        comuna = validated_data.pop('comuna')
        ciudad = validated_data.pop('ciudad')
        region = validated_data.pop('region')
        latitud = validated_data.pop('latitud', None)
        longitud = validated_data.pop('longitud', None)

        with transaction.atomic():
            guest_cliente = Cliente.objects.create(
                user=None,
                first_name=guest_nombre,
                last_name=guest_apellido,
                telefono=guest_telefono,
                email=guest_email,
            )

            direccion = Direccion.objects.create(
                cliente=guest_cliente,
                calle=calle,
                numero=numero,
                comuna=comuna,
                ciudad=ciudad,
                region=region,
                latitud=latitud,
                longitud=longitud,
                principal=True,
            )

            validated_data['cliente'] = guest_cliente
            validated_data['delivery_address'] = direccion

            return super().create(validated_data)

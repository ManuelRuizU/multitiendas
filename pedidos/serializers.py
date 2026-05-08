# pedidos/serializers.py
from rest_framework import serializers
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from decimal import Decimal

from .models import Order, OrderItem
from tiendas.models import Tienda
from productos.models import Producto
from usuarios.models import Cliente, Direccion
from carritos.models import Carrito, GrupoCarrito


# ------------------------------------------------------------------
# 1. SERIALIZER DE ÍTEM DE PEDIDO
# ------------------------------------------------------------------
class OrderItemSerializer(serializers.ModelSerializer):
    nombre_producto = serializers.CharField(
        source='product_name_snapshot',
        read_only=True
    )
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Producto.objects.all(),
        source='product',
        write_only=True,
        allow_null=True,
        required=False
    )

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_id', 'nombre_producto',
            'quantity', 'price_at_purchase',
            'get_total_price',
        ]
        read_only_fields = ['id', 'nombre_producto', 'price_at_purchase', 'get_total_price']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['total_item'] = instance.get_total_price()
        return data


# ------------------------------------------------------------------
# 2. SERIALIZER DE PEDIDO (lectura)
# ------------------------------------------------------------------
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    tienda_nombre = serializers.CharField(source='tienda.nombre', read_only=True)
    tienda_whatsapp = serializers.CharField(
        source='tienda.propietario_perfil.whatsapp_url',
        read_only=True
    )
    cliente_nombre = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tipo_entrega_display = serializers.CharField(source='get_tipo_entrega_display', read_only=True)
    metodo_pago_display = serializers.CharField(source='get_metodo_pago_display', read_only=True)
    loyverse_listo = serializers.ReadOnlyField()
    resumen_whatsapp = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_date', 'status', 'status_display',
            'tipo_entrega', 'tipo_entrega_display',
            'metodo_pago', 'metodo_pago_display',
            'tienda', 'tienda_nombre', 'tienda_whatsapp',
            'cliente', 'cliente_nombre',
            'delivery_address',
            'subtotal_amount', 'delivery_cost', 'total_amount',
            'customer_notes', 'tienda_notes',
            'confirmed_at', 'closed_at',
            'loyverse_receipt_id', 'loyverse_synced',
            'loyverse_synced_at', 'loyverse_sync_error',
            'loyverse_listo',
            'resumen_whatsapp',
            'items',
        ]
        read_only_fields = fields

    def get_cliente_nombre(self, obj):
        if not obj.cliente:
            return "Cliente eliminado"
        if obj.cliente.user:
            return obj.cliente.user.get_full_name() or obj.cliente.user.username
        nombre = f"{obj.cliente.first_name or ''} {obj.cliente.last_name or ''}".strip()
        return nombre or obj.cliente.email or "Invitado"


# ------------------------------------------------------------------
# 3. SERIALIZER DE CHECKOUT MULTITIENDA
# Convierte el carrito completo en múltiples Orders (uno por tienda)
# ------------------------------------------------------------------
class CheckoutSerializer(serializers.Serializer):
    """
    Serializer para el checkout multitienda.
    Recibe el carrito del usuario y genera un Order por cada GrupoCarrito.

    Campos opcionales globales que se aplican a todos los grupos
    si no están configurados en el GrupoCarrito:
    """
    # Dirección global (se usa si el grupo no tiene dirección configurada)
    direccion_id = serializers.PrimaryKeyRelatedField(
        queryset=Direccion.objects.all(),
        required=False,
        allow_null=True
    )

    # Notas globales
    notas_globales = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    # Para invitados
    guest_id = serializers.CharField(required=False, allow_null=True)

    # Datos del cliente invitado (si aplica)
    guest_nombre = serializers.CharField(required=False, allow_blank=True)
    guest_apellido = serializers.CharField(required=False, allow_blank=True)
    guest_telefono = serializers.CharField(required=False, allow_blank=True)
    guest_email = serializers.EmailField(required=False, allow_null=True)

    # Dirección inline para invitados
    calle = serializers.CharField(required=False, allow_blank=True)
    numero = serializers.CharField(required=False, allow_blank=True)
    comuna = serializers.CharField(required=False, allow_blank=True)
    ciudad = serializers.CharField(required=False, allow_blank=True)
    region = serializers.CharField(required=False, allow_blank=True)
    latitud = serializers.DecimalField(
        max_digits=9, decimal_places=6,
        required=False, allow_null=True
    )
    longitud = serializers.DecimalField(
        max_digits=9, decimal_places=6,
        required=False, allow_null=True
    )

    def validate(self, data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        # Obtener carrito
        if user is not None and user.is_authenticated:
            try:
                carrito = Carrito.objects.get(usuario=user)
            except Carrito.DoesNotExist:
                raise serializers.ValidationError("No tienes un carrito activo.")
        else:
            guest_id = data.get('guest_id')
            if not guest_id:
                raise serializers.ValidationError(
                    "guest_id es requerido para invitados."
                )
            try:
                carrito = Carrito.objects.get(
                    guest_id=guest_id,
                    usuario__isnull=True
                )
            except Carrito.DoesNotExist:
                raise serializers.ValidationError("Carrito de invitado no encontrado.")

        if carrito.esta_vacio:
            raise serializers.ValidationError("El carrito está vacío.")

        data['carrito'] = carrito
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        carrito = validated_data['carrito']
        direccion_global = validated_data.get('direccion_id')
        notas_globales = validated_data.get('notas_globales', '')

        orders_creados = []

        with transaction.atomic():
            # Obtener o crear cliente
            if user is not None and user.is_authenticated:
                try:
                    cliente = Cliente.objects.get(user=user)
                except Cliente.DoesNotExist:
                    raise serializers.ValidationError(
                        "El usuario no tiene perfil de cliente."
                    )
                direccion_default = direccion_global or (
                    cliente.direcciones.filter(principal=True).first()
                )
            else:
                # Crear cliente invitado
                cliente = Cliente.objects.create(
                    user=None,
                    first_name=validated_data.get('guest_nombre', ''),
                    last_name=validated_data.get('guest_apellido', ''),
                    telefono=validated_data.get('guest_telefono', ''),
                    email=validated_data.get('guest_email'),
                )
                # Crear dirección del invitado
                direccion_default = Direccion.objects.create(
                    cliente=cliente,
                    calle=validated_data.get('calle', ''),
                    numero=validated_data.get('numero', ''),
                    comuna=validated_data.get('comuna', ''),
                    ciudad=validated_data.get('ciudad', ''),
                    region=validated_data.get('region', ''),
                    latitud=validated_data.get('latitud'),
                    longitud=validated_data.get('longitud'),
                    principal=True,
                )

            # Crear un Order por cada GrupoCarrito
            for grupo in carrito.grupos.prefetch_related('items__producto').all():
                if not grupo.items.exists():
                    continue

                tienda = grupo.tienda

                # Validar tienda activa
                if not tienda.activo:
                    raise serializers.ValidationError(
                        f"La tienda '{tienda.nombre}' no está disponible actualmente."
                    )

                # Dirección para este pedido
                direccion_entrega = (
                    grupo.direccion_entrega or
                    direccion_global or
                    direccion_default
                )

                if not direccion_entrega:
                    raise serializers.ValidationError(
                        f"No hay dirección configurada para el pedido de '{tienda.nombre}'."
                    )

                # Calcular costo de envío
                delivery_cost = Decimal('0')
                if grupo.tipo_entrega == 'REPARTO':
                    if direccion_entrega.latitud and direccion_entrega.longitud:
                        costo = tienda.calcular_costo_envio(
                            float(direccion_entrega.latitud),
                            float(direccion_entrega.longitud)
                        )
                        if costo is None:
                            raise serializers.ValidationError(
                                f"La dirección está fuera del área de cobertura de '{tienda.nombre}'."
                            )
                        delivery_cost = Decimal(str(costo))
                    else:
                        delivery_cost = grupo.costo_envio or Decimal('0')

                # Bloquear productos con SELECT FOR UPDATE
                product_ids = [item.producto.id for item in grupo.items.all()]
                productos_locked = {
                    p.id: p
                    for p in Producto.objects.select_for_update().filter(id__in=product_ids)
                }

                subtotal = Decimal('0')
                items_to_create = []

                for item in grupo.items.all():
                    product = productos_locked[item.producto.id]
                    quantity = item.cantidad

                    # Validar stock
                    if not product.stock_ilimitado and product.stock < quantity:
                        raise serializers.ValidationError(
                            f"Stock insuficiente para '{product.nombre}' "
                            f"en '{tienda.nombre}'. Disponible: {product.stock}."
                        )

                    price = item.precio_unitario
                    subtotal += price * quantity
                    items_to_create.append({
                        'product': product,
                        'quantity': quantity,
                        'price_at_purchase': price,
                        'product_name_snapshot': product.nombre,
                    })

                total = subtotal + delivery_cost

                # Crear el Order
                order = Order.objects.create(
                    cliente=cliente,
                    tienda=tienda,
                    tipo_entrega=grupo.tipo_entrega,
                    metodo_pago=grupo.metodo_pago,
                    delivery_address=direccion_entrega,
                    subtotal_amount=subtotal,
                    delivery_cost=delivery_cost,
                    total_amount=total,
                    customer_notes=grupo.notas_cliente or notas_globales or '',
                )

                # Crear OrderItems y descontar stock
                for item_data in items_to_create:
                    OrderItem.objects.create(order=order, **item_data)
                    if not item_data['product'].stock_ilimitado:
                        Producto.objects.filter(
                            id=item_data['product'].id
                        ).update(stock=F('stock') - item_data['quantity'])

                orders_creados.append(order)

            # Vaciar el carrito
            carrito.grupos.all().delete()

        return orders_creados


# ------------------------------------------------------------------
# 4. SERIALIZER PARA CAMBIO DE ESTADO
# ------------------------------------------------------------------
class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES)
    tienda_notes = serializers.CharField(required=False, allow_blank=True)
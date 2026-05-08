# pedidos/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.serializers import ValidationError
from django.utils import timezone

from .models import Order, OrderItem
from .serializers import (
    OrderSerializer,
    OrderItemSerializer,
    CheckoutSerializer,
    OrderStatusSerializer,
)
from usuarios.permissions import IsRepartidor


# ------------------------------------------------------------------
# MÁQUINA DE ESTADOS
# ------------------------------------------------------------------
VALID_TRANSITIONS = {
    'PENDING':    ['CONFIRMED', 'CANCELLED'],
    'CONFIRMED':  ['PREPARING', 'CANCELLED'],
    'PREPARING':  ['ON_THE_WAY', 'CANCELLED'],
    'ON_THE_WAY': ['DELIVERED', 'CANCELLED'],
    'DELIVERED':  [],
    'CANCELLED':  [],
}


# ------------------------------------------------------------------
# PERMISO: Dueño del pedido o vendedor de la tienda
# ------------------------------------------------------------------
class IsOrderOwnerOrSeller(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        order = obj if isinstance(obj, Order) else obj.order
        # Es el cliente del pedido
        if hasattr(request.user, 'cliente_data') and \
                order.cliente == request.user.cliente_data:
            return True
        # Es el vendedor de la tienda
        if hasattr(request.user, 'seller_profile') and \
                order.tienda and \
                order.tienda.propietario_perfil == request.user.seller_profile:
            return True
        return False


# ------------------------------------------------------------------
# 1. ORDER VIEWSET
# ------------------------------------------------------------------
class OrderViewSet(viewsets.ModelViewSet):
    """
    Gestión de pedidos.

    GET  /api/pedidos/                    → mis pedidos (cliente o vendedor)
    GET  /api/pedidos/{id}/               → detalle de un pedido
    POST /api/pedidos/checkout/           → crear pedidos desde el carrito
    POST /api/pedidos/{id}/change_status/ → cambiar estado (vendedor)
    POST /api/pedidos/{id}/asignar_repartidor/ → asignar repartidor
    GET  /api/pedidos/panel_vendedor/     → pedidos pendientes del vendedor
    GET  /api/pedidos/{id}/whatsapp/      → obtener mensaje de WhatsApp
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderOwnerOrSeller]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        if hasattr(user, 'cliente_data'):
            return Order.objects.filter(cliente=user.cliente_data)
        if hasattr(user, 'seller_profile'):
            return Order.objects.filter(
                tienda__propietario_perfil=user.seller_profile
            )
        if hasattr(user, 'repartidor_profile'):
            return Order.objects.filter(
                repartidor=user.repartidor_profile
            )
        return Order.objects.none()

    # ------------------------------------------------------------------
    # CHECKOUT MULTITIENDA
    # ------------------------------------------------------------------
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[permissions.AllowAny]
    )
    def checkout(self, request):
        """
        Convierte el carrito completo en pedidos.
        Genera un Order por cada tienda del carrito.
        Envía el resumen de WhatsApp de cada pedido.

        Body para usuario autenticado:
        {
            "direccion_id": 1,          // opcional, usa la principal si no se envía
            "notas_globales": "..."     // opcional
        }

        Body para invitado:
        {
            "guest_id": "uuid",
            "guest_nombre": "Juan",
            "guest_telefono": "+56912345678",
            "calle": "Los Aromos",
            "numero": "123",
            "comuna": "Angol",
            "ciudad": "Angol",
            "region": "La Araucanía"
        }
        """
        serializer = CheckoutSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        orders = serializer.save()

        # Serializar los pedidos creados
        response_data = {
            "mensaje": f"✅ Se generaron {len(orders)} pedido(s) correctamente.",
            "pedidos": OrderSerializer(orders, many=True).data,
            "whatsapp_links": [
                {
                    "tienda": order.tienda.nombre,
                    "whatsapp_url": order.tienda.propietario_perfil.whatsapp_url,
                    "mensaje": order.resumen_whatsapp,
                }
                for order in orders
            ]
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------
    # PANEL DEL VENDEDOR
    # ------------------------------------------------------------------
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def panel_vendedor(self, request):
        """
        Retorna los pedidos del vendedor organizados por estado.
        Útil para el panel de gestión del emprendedor.
        """
        if not hasattr(request.user, 'seller_profile'):
            return Response(
                {"detail": "Solo los vendedores pueden acceder al panel."},
                status=status.HTTP_403_FORBIDDEN
            )

        pedidos = Order.objects.filter(
            tienda__propietario_perfil=request.user.seller_profile
        ).order_by('-order_date')

        response = {
            "pendientes": OrderSerializer(
                pedidos.filter(status='PENDING'), many=True
            ).data,
            "confirmados": OrderSerializer(
                pedidos.filter(status='CONFIRMED'), many=True
            ).data,
            "en_preparacion": OrderSerializer(
                pedidos.filter(status='PREPARING'), many=True
            ).data,
            "en_camino": OrderSerializer(
                pedidos.filter(status='ON_THE_WAY'), many=True
            ).data,
            "entregados_hoy": OrderSerializer(
                pedidos.filter(
                    status='DELIVERED',
                    closed_at__date=timezone.now().date()
                ),
                many=True
            ).data,
        }
        return Response(response)

    # ------------------------------------------------------------------
    # CAMBIO DE ESTADO
    # ------------------------------------------------------------------
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """
        Cambia el estado del pedido siguiendo la máquina de estados.
        Solo el vendedor o staff puede cambiar el estado.

        Body: {
            "status": "CONFIRMED",
            "hora_entrega_est": "2024-01-01T19:00:00",  // opcional
            "tienda_notes": "..."                         // opcional
        }
        """
        order = self.get_object()

        # Solo vendedor o staff
        if not request.user.is_staff and not (
            hasattr(request.user, 'seller_profile') and
            order.tienda and
            order.tienda.propietario_perfil == request.user.seller_profile
        ):
            return Response(
                {"detail": "Solo el vendedor puede cambiar el estado del pedido."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = OrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        allowed = VALID_TRANSITIONS.get(order.status, [])

        if new_status not in allowed:
            return Response(
                {
                    "detail": f"Transición no permitida: {order.status} → {new_status}.",
                    "transiciones_validas": allowed or ["ninguna"],
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = new_status

        # Notas internas del vendedor
        tienda_notes = serializer.validated_data.get('tienda_notes')
        if tienda_notes:
            order.tienda_notes = tienda_notes

        order.save()

        return Response(
            {
                "detail": f"Estado cambiado a {order.get_status_display()}.",
                "pedido": OrderSerializer(order).data,
            }
        )

    # ------------------------------------------------------------------
    # ASIGNAR REPARTIDOR
    # ------------------------------------------------------------------
    @action(detail=True, methods=['post'])
    def asignar_repartidor(self, request, pk=None):
        """
        Asigna un repartidor al pedido.
        Solo el vendedor puede asignar repartidores.

        Body: {
            "repartidor_id": 1,
            "modo_asignacion": "CERRADO"  // opcional
        }
        """
        order = self.get_object()

        if not hasattr(request.user, 'seller_profile') or \
                order.tienda.propietario_perfil != request.user.seller_profile:
            return Response(
                {"detail": "Solo el vendedor puede asignar repartidores."},
                status=status.HTTP_403_FORBIDDEN
            )

        if order.tipo_entrega != 'REPARTO':
            return Response(
                {"detail": "Solo se pueden asignar repartidores a pedidos de reparto."},
                status=status.HTTP_400_BAD_REQUEST
            )

        repartidor_id = request.data.get('repartidor_id')
        if not repartidor_id:
            return Response(
                {"detail": "repartidor_id es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        from repartidores.models import Repartidor
        try:
            repartidor = Repartidor.objects.get(
                id=repartidor_id,
                tiendas=order.tienda
            )
        except Repartidor.DoesNotExist:
            return Response(
                {"detail": "Repartidor no encontrado o no trabaja para esta tienda."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "detail": f"Repartidor {repartidor.user.get_full_name() or repartidor.user.username} asignado.",
                "pedido": OrderSerializer(order).data,
            }
        )

    # ------------------------------------------------------------------
    # MENSAJE DE WHATSAPP
    # ------------------------------------------------------------------
    @action(detail=True, methods=['get'])
    def whatsapp(self, request, pk=None):
        """
        Retorna el mensaje de WhatsApp del pedido y el link para enviarlo.
        GET /api/pedidos/{id}/whatsapp/
        """
        order = self.get_object()
        return Response({
            "tienda": order.tienda.nombre if order.tienda else None,
            "whatsapp_url": order.tienda.propietario_perfil.whatsapp_url if order.tienda else None,
            "mensaje": order.resumen_whatsapp,
            "link_directo": (
                f"{order.tienda.propietario_perfil.whatsapp_url}"
                f"?text={order.resumen_whatsapp}"
            ) if order.tienda else None,
        })

    # ------------------------------------------------------------------
    # TOMAR PEDIDO (repartidor en modo LIBRE)
    # ------------------------------------------------------------------
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated, IsRepartidor]
    )
    def tomar_pedido(self, request, pk=None):
        """
        El repartidor toma un pedido disponible en modo LIBRE.
        GET /api/pedidos/{id}/tomar_pedido/
        """
        order = self.get_object()
        repartidor = request.user.repartidor_profile

        if not order.disponible_para_tomar:
            return Response(
                {"detail": "Este pedido no está disponible para tomar."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar que el repartidor trabaja para esta tienda
        if not repartidor.tiendas.filter(id=order.tienda.id).exists():
            return Response(
                {"detail": "No trabajas para la tienda de este pedido."},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(
            {
                "detail": "Pedido tomado exitosamente.",
                "pedido": OrderSerializer(order).data,
            }
        )


# ------------------------------------------------------------------
# 2. ORDER ITEM VIEWSET (solo lectura)
# ------------------------------------------------------------------
class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderOwnerOrSeller]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return OrderItem.objects.all()
        if hasattr(user, 'cliente_data'):
            return OrderItem.objects.filter(order__cliente=user.cliente_data)
        if hasattr(user, 'seller_profile'):
            return OrderItem.objects.filter(
                order__tienda__propietario_perfil=user.seller_profile
            )
        return OrderItem.objects.none()
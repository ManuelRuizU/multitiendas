# repartidores/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.serializers import ValidationError

from .models import Repartidor
from .serializers import RepartidorSerializer
from usuarios.permissions import IsRepartidor, IsSellerOrAdmin


# ------------------------------------------------------------------
# REPARTIDOR VIEWSET
# ------------------------------------------------------------------
class RepartidorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar repartidores.

    - GET /api/repartidores/ → lista de repartidores (solo staff o vendedores)
    - GET /api/repartidores/{id}/ → detalle de un repartidor
    - PATCH /api/repartidores/{id}/ → actualizar estado o datos
    - GET /api/repartidores/mis_pedidos/ → pedidos activos del repartidor autenticado
    - PATCH /api/repartidores/mi_estado/ → cambiar estado (DISPONIBLE/EN_RUTA/INACTIVO)
    """
    serializer_class = RepartidorSerializer

    def get_permissions(self):
        if self.action in ['mis_pedidos', 'mi_estado', 'mi_perfil']:
            return [IsRepartidor()]
        return [IsSellerOrAdmin()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Repartidor.objects.all()
        # Vendedor ve solo los repartidores de sus tiendas
        if hasattr(user, 'seller_profile'):
            return Repartidor.objects.filter(
                tiendas__propietario_perfil=user.seller_profile
            ).distinct()
        # Repartidor se ve solo a sí mismo
        if hasattr(user, 'repartidor_profile'):
            return Repartidor.objects.filter(user=user)
        return Repartidor.objects.none()

    # --- Acciones personalizadas ---

    @action(detail=False, methods=['get'], permission_classes=[IsRepartidor])
    def mi_perfil(self, request):
        """Retorna el perfil del repartidor autenticado."""
        repartidor = getattr(request.user, 'repartidor_profile', None)
        if repartidor:
            return Response(self.get_serializer(repartidor).data)
        return Response(
            {"detail": "Perfil de repartidor no encontrado."},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=False, methods=['get'], permission_classes=[IsRepartidor])
    def mis_pedidos(self, request):
        """
        Retorna los pedidos activos asignados al repartidor,
        ordenados por hora de entrega estimada.
        """
        repartidor = getattr(request.user, 'repartidor_profile', None)
        if not repartidor:
            return Response(
                {"detail": "No tienes un perfil de repartidor."},
                status=status.HTTP_404_NOT_FOUND
            )
        from pedidos.models import Order
        from pedidos.serializers import OrderSerializer
        pedidos = repartidor.pedidos_activos
        serializer = OrderSerializer(pedidos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'], permission_classes=[IsRepartidor])
    def mi_estado(self, request):
        """
        Permite al repartidor cambiar su propio estado.
        Solo puede cambiar entre DISPONIBLE e INACTIVO.
        EN_RUTA se asigna automáticamente al recibir pedidos.

        Body: {"estado": "DISPONIBLE"} o {"estado": "INACTIVO"}
        """
        repartidor = getattr(request.user, 'repartidor_profile', None)
        if not repartidor:
            return Response(
                {"detail": "No tienes un perfil de repartidor."},
                status=status.HTTP_404_NOT_FOUND
            )

        nuevo_estado = request.data.get('estado')
        estados_permitidos = ['DISPONIBLE', 'INACTIVO']

        if nuevo_estado not in estados_permitidos:
            return Response(
                {"detail": f"Estado inválido. Usa: {', '.join(estados_permitidos)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        repartidor.estado = nuevo_estado
        repartidor.save(update_fields=['estado'])
        return Response(
            {
                "detail": f"Estado actualizado a {repartidor.get_estado_display()}.",
                "estado": repartidor.estado,
            },
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsSellerOrAdmin],
        url_path='disponibles'
    )
    def disponibles(self, request):
        """
        Retorna repartidores DISPONIBLES o EN_RUTA para una tienda.
        Útil para que el emprendedor asigne pedidos.

        Query param: ?tienda_id=1
        """
        tienda_id = request.query_params.get('tienda_id')
        queryset = Repartidor.objects.filter(
            estado__in=['DISPONIBLE', 'EN_RUTA']
        )
        if tienda_id:
            queryset = queryset.filter(tiendas__id=tienda_id)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
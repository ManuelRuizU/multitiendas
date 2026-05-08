# carritos/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.decorators import action

from .models import Carrito, GrupoCarrito, ItemCarrito
from .serializers import CarritoSerializer, GrupoCarritoSerializer, ItemCarritoSerializer
from productos.models import Producto
from tiendas.models import Tienda
import uuid


# ------------------------------------------------------------------
# PERMISO: Solo el dueño del carrito
# ------------------------------------------------------------------
class IsCartOwner(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        guest_id = request.data.get('guest_id') or request.query_params.get('guest_id')
        return bool(guest_id)

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, ItemCarrito):
            carrito = obj.grupo.carrito
        elif isinstance(obj, GrupoCarrito):
            carrito = obj.carrito
        else:
            carrito = obj

        if request.user.is_authenticated:
            return carrito.usuario == request.user
        guest_id = request.data.get('guest_id') or request.query_params.get('guest_id')
        return bool(guest_id) and carrito.guest_id == guest_id and carrito.usuario is None


# ------------------------------------------------------------------
# UTILIDAD: Obtener o crear carrito
# ------------------------------------------------------------------
def get_or_create_carrito(request):
    """Retorna (carrito, created) para usuario autenticado o invitado."""
    if request.user.is_authenticated:
        return Carrito.objects.get_or_create(usuario=request.user)
    guest_id = request.data.get('guest_id') or request.query_params.get('guest_id')
    if not guest_id:
        guest_id = str(uuid.uuid4())
    return Carrito.objects.get_or_create(
        guest_id=guest_id,
        defaults={'guest_id': guest_id}
    )


def get_carrito(request):
    """
    Retorna el carrito existente o None.
    No crea uno nuevo — usar para operaciones de edición.
    """
    if request.user.is_authenticated:
        return Carrito.objects.filter(usuario=request.user).first()
    guest_id = request.data.get('guest_id') or request.query_params.get('guest_id')
    if not guest_id:
        return None
    return Carrito.objects.filter(guest_id=guest_id).first()


# ------------------------------------------------------------------
# 1. CARRITO VIEWSET
# ------------------------------------------------------------------
class CarritoViewSet(viewsets.GenericViewSet):
    """
    Gestión del carrito multitienda.

    GET  /api/carritos/mi_carrito/           → ver carrito completo
    POST /api/carritos/mi_carrito/           → crear carrito invitado
    POST /api/carritos/fusionar_carrito/     → fusionar carrito invitado al hacer login
    GET  /api/carritos/{id}/                 → ver carrito por ID
    """
    queryset = Carrito.objects.all()
    serializer_class = CarritoSerializer
    permission_classes = [IsCartOwner]

    def retrieve(self, request, pk=None):
        carrito = self.get_object()
        self.check_object_permissions(request, carrito)
        return Response(self.get_serializer(carrito).data)

    @action(detail=False, methods=['get', 'post'])
    def mi_carrito(self, request):
        """
        Retorna el carrito del usuario o invitado.
        Si no existe lo crea automáticamente.
        """
        carrito, created = get_or_create_carrito(request)

        # Advertencia de retiros simultáneos
        response_data = self.get_serializer(carrito).data
        if carrito.tiene_retiros_simultaneos:
            response_data['advertencia'] = (
                "⚠️ Tienes retiros en local a la misma hora en distintas tiendas. "
                "Verifica que puedas estar en ambos lugares o ajusta los horarios."
            )

        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(response_data, status=status_code)

    @action(detail=False, methods=['post'], permission_classes=[IsCartOwner])
    def agregar_producto(self, request):
        """
        Agrega un producto al carrito multitienda.
        Crea el carrito y el GrupoCarrito si no existen.

        Body: {"producto_id": 1, "cantidad": 2}
        Invitados: {"producto_id": 1, "cantidad": 2, "guest_id": "uuid"}
        """
        producto_id = request.data.get('producto_id')
        if not producto_id:
            return Response(
                {"detail": "producto_id es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cantidad = int(request.data.get('cantidad', 1))
            if cantidad <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {"detail": "cantidad debe ser un entero mayor a 0."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            producto = Producto.objects.select_related('tienda').get(pk=producto_id)
        except Producto.DoesNotExist:
            return Response(
                {"detail": f"Producto {producto_id} no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not producto.disponible:
            return Response(
                {"detail": f"'{producto.nombre}' no está disponible."},
                status=status.HTTP_400_BAD_REQUEST
            )

        carrito, _ = get_or_create_carrito(request)

        grupo, _ = GrupoCarrito.objects.get_or_create(
            carrito=carrito,
            tienda=producto.tienda
        )

        # Validar stock antes de crear/actualizar
        if not producto.stock_ilimitado and cantidad > producto.stock:
            return Response(
                {
                    "detail": f"Stock insuficiente de '{producto.nombre}'. "
                              f"Disponible: {producto.stock}."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        item, created = ItemCarrito.objects.get_or_create(
            grupo=grupo,
            producto=producto,
            defaults={'cantidad': cantidad}
        )

        if not created:
            nueva_cantidad = item.cantidad + cantidad
            if not producto.stock_ilimitado and nueva_cantidad > producto.stock:
                return Response(
                    {
                        "detail": f"Stock insuficiente. Ya tienes {item.cantidad} "
                                  f"en el carrito. Disponible: {producto.stock}."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            item.cantidad = nueva_cantidad
            item.save(update_fields=['cantidad'])

        return Response(self.get_serializer(carrito).data)

    @action(detail=False, methods=['post'], permission_classes=[IsCartOwner])
    def eliminar_producto(self, request):
        """
        Elimina un producto del carrito.
        Si el grupo de esa tienda queda vacío, también se elimina.
        Body: {"producto_id": 1}
        Invitados: {"producto_id": 1, "guest_id": "uuid"}
        """
        producto_id = request.data.get('producto_id')
        if not producto_id:
            return Response(
                {"detail": "producto_id es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            producto = Producto.objects.get(pk=producto_id)
        except Producto.DoesNotExist:
            return Response(
                {"detail": f"Producto {producto_id} no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        carrito = get_carrito(request)
        if not carrito:
            return Response(
                {"detail": "No tienes carrito activo."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            item = ItemCarrito.objects.get(grupo__carrito=carrito, producto=producto)
        except ItemCarrito.DoesNotExist:
            return Response(
                {"detail": f"'{producto.nombre}' no está en el carrito."},
                status=status.HTTP_404_NOT_FOUND
            )

        grupo = item.grupo
        item.delete()
        if not grupo.items.exists():
            grupo.delete()

        return Response(self.get_serializer(carrito).data)

    @action(detail=False, methods=['patch'], permission_classes=[IsCartOwner])
    def actualizar_cantidad(self, request):
        """
        Cambia la cantidad de un producto en el carrito.
        Si cantidad <= 0 elimina el item (y el grupo si queda vacío).
        Body: {"producto_id": 1, "cantidad": 3}
        Invitados: {"producto_id": 1, "cantidad": 3, "guest_id": "uuid"}
        """
        producto_id = request.data.get('producto_id')
        if not producto_id:
            return Response(
                {"detail": "producto_id es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cantidad = int(request.data.get('cantidad'))
        except (ValueError, TypeError):
            return Response(
                {"detail": "cantidad es requerida y debe ser un entero."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            producto = Producto.objects.select_related('tienda').get(pk=producto_id)
        except Producto.DoesNotExist:
            return Response(
                {"detail": f"Producto {producto_id} no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        carrito = get_carrito(request)
        if not carrito:
            return Response(
                {"detail": "No tienes carrito activo."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            item = ItemCarrito.objects.get(grupo__carrito=carrito, producto=producto)
        except ItemCarrito.DoesNotExist:
            return Response(
                {"detail": f"'{producto.nombre}' no está en el carrito."},
                status=status.HTTP_404_NOT_FOUND
            )

        if cantidad <= 0:
            grupo = item.grupo
            item.delete()
            if not grupo.items.exists():
                grupo.delete()
            return Response(self.get_serializer(carrito).data)

        if not producto.stock_ilimitado and cantidad > producto.stock:
            return Response(
                {
                    "detail": f"Stock insuficiente de '{producto.nombre}'. "
                              f"Disponible: {producto.stock}."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        item.cantidad = cantidad
        item.save(update_fields=['cantidad'])

        return Response(self.get_serializer(carrito).data)

    @action(detail=False, methods=['post'], permission_classes=[IsCartOwner])
    def vaciar_carrito(self, request):
        """
        Elimina todos los grupos e items del carrito.
        El carrito en sí se conserva.
        Body invitados: {"guest_id": "uuid"}
        """
        carrito = get_carrito(request)
        if not carrito:
            return Response(
                {"detail": "No tienes carrito activo."},
                status=status.HTTP_404_NOT_FOUND
            )
        carrito.grupos.all().delete()
        return Response(self.get_serializer(carrito).data)

    @action(detail=False, methods=['post'])
    def fusionar_carrito(self, request):
        """
        Fusiona el carrito de invitado al carrito del usuario registrado.
        Llamar después del login o registro.
        Body: {"guest_id": "uuid"}
        """
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Debe estar autenticado para fusionar."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        guest_id = request.data.get('guest_id')
        if not guest_id:
            return Response(
                {"detail": "guest_id es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            carrito_invitado = Carrito.objects.get(
                guest_id=guest_id,
                usuario__isnull=True
            )
        except Carrito.DoesNotExist:
            return Response(
                {"detail": "Carrito de invitado no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

        carrito_usuario, _ = Carrito.objects.get_or_create(usuario=request.user)

        # Fusionar grupos por tienda
        for grupo_invitado in carrito_invitado.grupos.all():
            grupo_usuario, _ = GrupoCarrito.objects.get_or_create(
                carrito=carrito_usuario,
                tienda=grupo_invitado.tienda,
                defaults={
                    'metodo_pago': grupo_invitado.metodo_pago,
                    'tipo_entrega': grupo_invitado.tipo_entrega,
                    'hora_sugerida_cliente': grupo_invitado.hora_sugerida_cliente,
                    'notas_cliente': grupo_invitado.notas_cliente,
                }
            )
            # Fusionar items del grupo
            for item in grupo_invitado.items.all():
                item_usuario, created = ItemCarrito.objects.get_or_create(
                    grupo=grupo_usuario,
                    producto=item.producto,
                    defaults={
                        'cantidad': item.cantidad,
                        'precio_unitario': item.precio_unitario,
                    }
                )
                if not created:
                    item_usuario.cantidad += item.cantidad
                    item_usuario.save()

        # Eliminar carrito invitado
        carrito_invitado.delete()

        return Response(self.get_serializer(carrito_usuario).data)


# ------------------------------------------------------------------
# 2. GRUPO CARRITO VIEWSET
# ------------------------------------------------------------------
class GrupoCarritoViewSet(viewsets.GenericViewSet):
    """
    Gestión de grupos del carrito (uno por tienda).

    GET   /api/carritos/{carrito_pk}/grupos/                    → ver grupos
    PATCH /api/carritos/{carrito_pk}/grupos/{id}/               → actualizar configuración
    DELETE /api/carritos/{carrito_pk}/grupos/{id}/              → vaciar grupo/tienda
    POST  /api/carritos/{carrito_pk}/grupos/{id}/calcular_envio/ → calcular envío
    POST  /api/carritos/{carrito_pk}/grupos/{id}/cambiar_metodo_pago/ → cambiar método pago
    """
    serializer_class = GrupoCarritoSerializer
    permission_classes = [IsCartOwner]

    def get_queryset(self):
        carrito_pk = self.kwargs.get('carrito_pk')
        if self.request.user.is_authenticated:
            return GrupoCarrito.objects.filter(
                carrito__usuario=self.request.user,
                carrito__id=carrito_pk
            )
        guest_id = (
            self.request.data.get('guest_id') or
            self.request.query_params.get('guest_id')
        )
        if guest_id:
            return GrupoCarrito.objects.filter(
                carrito__guest_id=guest_id,
                carrito__id=carrito_pk
            )
        return GrupoCarrito.objects.none()

    def list(self, request, carrito_pk=None):
        queryset = self.get_queryset()
        return Response(self.get_serializer(queryset, many=True).data)

    def partial_update(self, request, carrito_pk=None, pk=None):
        """Actualizar configuración del grupo (metodo_pago, tipo_entrega, hora, notas)."""
        grupo = self.get_object()
        self.check_object_permissions(request, grupo)
        serializer = self.get_serializer(grupo, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, carrito_pk=None, pk=None):
        """Elimina el grupo completo (todos los items de esa tienda)."""
        grupo = self.get_object()
        self.check_object_permissions(request, grupo)
        grupo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def calcular_envio(self, request, carrito_pk=None, pk=None):
        """
        Calcula el costo de envío para este grupo.
        Usa la dirección configurada en el grupo o coordenadas opcionales.

        Body (opcional): {"lat": -37.79, "lng": -72.70}
        """
        grupo = self.get_object()
        self.check_object_permissions(request, grupo)

        lat = request.data.get('lat')
        lng = request.data.get('lng')

        costo = grupo.calcular_costo_envio(
            lat=float(lat) if lat else None,
            lng=float(lng) if lng else None
        )

        if costo is None:
            return Response(
                {
                    "detail": "No se pudo calcular el envío. "
                              "Verifica que la dirección tenga coordenadas válidas "
                              "o que esté dentro del área de cobertura.",
                    "cubierto": False
                },
                status=status.HTTP_200_OK
            )

        return Response({
            "tienda": grupo.tienda.nombre,
            "tipo_entrega": grupo.tipo_entrega,
            "costo_envio": costo,
            "cubierto": True,
        })

    @action(detail=True, methods=['post'])
    def cambiar_metodo_pago(self, request, carrito_pk=None, pk=None):
        """
        Cambia el método de pago de este grupo y recalcula precios.
        Body: {"metodo_pago": "TRANSFERENCIA"}
        """
        grupo = self.get_object()
        self.check_object_permissions(request, grupo)

        nuevo_metodo = request.data.get('metodo_pago')
        opciones = [c[0] for c in GrupoCarrito.METODO_PAGO_CHOICES]

        if nuevo_metodo not in opciones:
            return Response(
                {"detail": f"Método inválido. Opciones: {opciones}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar que la tienda acepta el método
        metodos_map = {
            'EFECTIVO': 'Efectivo',
            'TRANSFERENCIA': 'Transferencia bancaria',
            'LINK_PAGO': 'Link de pago',
        }
        if metodos_map.get(nuevo_metodo) not in grupo.tienda.metodos_pago_activos:
            return Response(
                {"detail": f"La tienda '{grupo.tienda.nombre}' no acepta este método de pago."},
                status=status.HTTP_400_BAD_REQUEST
            )

        grupo.metodo_pago = nuevo_metodo
        grupo.save(update_fields=['metodo_pago'])
        grupo.actualizar_precios()

        return Response(self.get_serializer(grupo).data)


# ------------------------------------------------------------------
# 3. ITEM CARRITO VIEWSET
# ------------------------------------------------------------------
class ItemCarritoViewSet(viewsets.ModelViewSet):
    """
    Gestión de items dentro de un grupo del carrito.

    POST   /api/carritos/{carrito_pk}/grupos/{grupo_pk}/items/      → agregar item
    PATCH  /api/carritos/{carrito_pk}/grupos/{grupo_pk}/items/{id}/ → actualizar cantidad
    DELETE /api/carritos/{carrito_pk}/grupos/{grupo_pk}/items/{id}/ → eliminar item
    """
    serializer_class = ItemCarritoSerializer
    permission_classes = [IsCartOwner]

    def get_queryset(self):
        grupo_pk = self.kwargs.get('grupo_pk')
        if self.request.user.is_authenticated:
            return ItemCarrito.objects.filter(
                grupo__carrito__usuario=self.request.user,
                grupo__id=grupo_pk
            )
        guest_id = (
            self.request.data.get('guest_id') or
            self.request.query_params.get('guest_id')
        )
        if guest_id:
            return ItemCarrito.objects.filter(
                grupo__carrito__guest_id=guest_id,
                grupo__id=grupo_pk
            )
        return ItemCarrito.objects.none()

    def create(self, request, carrito_pk=None, grupo_pk=None, *args, **kwargs):
        """
        Agrega un producto al carrito multitienda.
        Crea el GrupoCarrito automáticamente si no existe para esa tienda.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        producto = serializer.validated_data['producto']
        cantidad = serializer.validated_data['cantidad']

        # Obtener o crear carrito
        carrito, _ = get_or_create_carrito(request)

        # Obtener o crear grupo para la tienda del producto
        grupo, grupo_created = GrupoCarrito.objects.get_or_create(
            carrito=carrito,
            tienda=producto.tienda
        )

        # Validar disponibilidad
        if not producto.disponible:
            return Response(
                {"detail": f"'{producto.nombre}' no está disponible."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar stock
        if not producto.stock_ilimitado and cantidad > producto.stock:
            return Response(
                {
                    "detail": f"Stock insuficiente de '{producto.nombre}'. "
                              f"Disponible: {producto.stock}."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Agregar o actualizar item
        item, created = ItemCarrito.objects.get_or_create(
            grupo=grupo,
            producto=producto,
            defaults={
                'cantidad': cantidad,
                'precio_unitario': (
                    producto.precio_tarjeta
                    if grupo.metodo_pago == 'TARJETA'
                    else producto.precio_efectivo
                )
            }
        )

        if not created:
            nueva_cantidad = item.cantidad + cantidad
            if not producto.stock_ilimitado and nueva_cantidad > producto.stock:
                return Response(
                    {
                        "detail": f"Stock insuficiente. Ya tienes {item.cantidad} en el carrito. "
                                  f"Stock disponible: {producto.stock}."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            item.cantidad = nueva_cantidad
            item.save()

        return Response(
            self.get_serializer(item).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs):
        """Si cantidad <= 0 elimina el item."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        self.check_object_permissions(request, instance)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        nueva_cantidad = serializer.validated_data.get('cantidad')
        if nueva_cantidad is not None and nueva_cantidad <= 0:
            instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
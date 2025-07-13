# carritos/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404 # Esta importación ya no será necesaria para el producto en create
from django.db.models import F # Agrega esta importación si no la tienes, para futuras optimizaciones

from .models import Carrito, ItemCarrito
from .serializers import CarritoSerializer, ItemCarritoSerializer
from productos.models import Producto # Asegúrate de que Producto esté importado aquí
import uuid

class CarritoViewSet(viewsets.GenericViewSet):
    # ... (Tu código existente para CarritoViewSet es correcto) ...
    queryset = Carrito.objects.all()
    serializer_class = CarritoSerializer

    def get_permissions(self):
        if self.action in ['mi_carrito', 'fusionar_carrito']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get', 'post'])
    def mi_carrito(self, request):
        if request.user.is_authenticated:
            carrito, created = Carrito.objects.get_or_create(usuario=request.user)
            if created:
                print(f"Carrito creado para el usuario {request.user.username}")
            serializer = self.get_serializer(carrito)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            guest_id = request.data.get('guest_id') or request.query_params.get('guest_id')
            if not guest_id:
                return Response(
                    {"detail": "Guest ID no proporcionado. Por favor, proporcione uno (ej. un UUID generado por el frontend)."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                carrito = Carrito.objects.get(guest_id=guest_id, usuario__isnull=True)
            except Carrito.DoesNotExist:
                carrito = Carrito.objects.create(guest_id=guest_id)
                print(f"Carrito de invitado creado con guest_id: {guest_id}")
            serializer = self.get_serializer(carrito)
            return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def fusionar_carrito(self, request):
        guest_id = request.data.get('guest_id')
        if not guest_id:
            return Response({"detail": "Guest ID no proporcionado para la fusión."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            carrito_invitado = Carrito.objects.get(guest_id=guest_id, usuario__isnull=True)
        except Carrito.DoesNotExist:
            return Response({"detail": "Carrito de invitado no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        carrito_usuario, created = Carrito.objects.get_or_create(usuario=request.user)

        for item_invitado in carrito_invitado.items.all():
            item_usuario, item_created = ItemCarrito.objects.get_or_create(
                carrito=carrito_usuario,
                producto=item_invitado.producto,
                defaults={'cantidad': item_invitado.cantidad, 'precio_unitario': item_invitado.precio_unitario}
            )
            if not item_created:
                item_usuario.cantidad += item_invitado.cantidad
                item_usuario.save()
            item_invitado.delete()

        carrito_invitado.delete()
        carrito_usuario.save()

        serializer = self.get_serializer(carrito_usuario)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ItemCarritoViewSet(viewsets.ModelViewSet):
    serializer_class = ItemCarritoSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return ItemCarrito.objects.filter(carrito__usuario=self.request.user)
        else:
            guest_id = self.request.data.get('guest_id') or self.request.query_params.get('guest_id')
            if guest_id:
                return ItemCarrito.objects.filter(carrito__guest_id=guest_id, carrito__usuario__isnull=True)
            return ItemCarrito.objects.none()

    def create(self, request, *args, **kwargs):
        # 1. Validar los datos de entrada con el serializador
        # Esto se encarga de que 'producto_id' sea válido y lo convierte en una instancia de Producto
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True) # Si no es válido, lanza una excepción 400

        # Ahora obtenemos 'producto' y 'cantidad' directamente de los datos validados
        producto = serializer.validated_data['producto'] # <--- ¡Aquí está la instancia de Producto!
        cantidad = serializer.validated_data['cantidad']
        
        # 2. Determinar a qué carrito se añade el ítem
        carrito = None
        if request.user.is_authenticated:
            carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        else:
            guest_id = request.data.get('guest_id')
            if not guest_id:
                return Response({"detail": "Guest ID es requerido para usuarios no autenticados."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                carrito = Carrito.objects.get(guest_id=guest_id, usuario__isnull=True)
            except Carrito.DoesNotExist:
                # Si el carrito de invitado no existe, lo creamos aquí mismo
                carrito = Carrito.objects.create(guest_id=guest_id)
                print(f"Carrito de invitado creado al añadir ítem: {guest_id}")
                
        # 3. Intentar encontrar el ítem existente en el carrito
        item_carrito, created = ItemCarrito.objects.get_or_create(
            carrito=carrito,
            producto=producto, # Usamos la instancia de producto ya validada
            defaults={'cantidad': cantidad, 'precio_unitario': producto.precio_efectivo} # Guarda el precio efectivo por defecto
        )

        if not created:
            # Si el ítem ya existe, actualiza la cantidad
            item_carrito.cantidad += int(cantidad)
            item_carrito.save()
        
        # 4. Serializar y devolver la respuesta
        response_serializer = self.get_serializer(item_carrito)
        return Response(response_serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        # ... (Tu código existente para update es correcto) ...
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        if request.user.is_authenticated:
            if instance.carrito.usuario != request.user:
                return Response({"detail": "No tiene permiso para actualizar este ítem de carrito."}, status=status.HTTP_403_FORBIDDEN)
        else:
            guest_id = request.data.get('guest_id') or request.query_params.get('guest_id')
            if not guest_id or instance.carrito.guest_id != guest_id:
                return Response({"detail": "No tiene permiso o Guest ID inválido para este ítem."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        # ... (Tu código existente para destroy es correcto) ...
        instance = self.get_object()
        
        if request.user.is_authenticated:
            if instance.carrito.usuario != request.user:
                return Response({"detail": "No tiene permiso para eliminar este ítem de carrito."}, status=status.HTTP_403_FORBIDDEN)
        else:
            guest_id = request.data.get('guest_id') or request.query_params.get('guest_id')
            if not guest_id or instance.carrito.guest_id != guest_id:
                return Response({"detail": "No tiene permiso o Guest ID inválido para este ítem."}, status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

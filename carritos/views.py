# carritos/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from .models import Carrito, ItemCarrito
from .serializers import CarritoSerializer, ItemCarritoSerializer
import uuid

class CarritoViewSet(viewsets.GenericViewSet):
    queryset = Carrito.objects.all()
    serializer_class = CarritoSerializer

    # Sobrescribe get_permissions para manejar los permisos por acción
    def get_permissions(self):
        if self.action in ['mi_carrito', 'fusionar_carrito']:
            # Para 'mi_carrito' (GET/POST) y 'fusionar_carrito' (POST), permitimos a cualquiera.
            # La lógica dentro de la acción determinará si requiere autenticación o guest_id.
            return [AllowAny()]
        # Para cualquier otra acción futura que pudieras añadir al CarritoViewSet
        # y que requiera autenticación.
        return [IsAuthenticated()]

    # Acción para obtener o crear el carrito del usuario actual o un carrito de invitado
    @action(detail=False, methods=['get', 'post']) # Ya no necesitamos permission_classes aquí
    def mi_carrito(self, request):
        if request.user.is_authenticated:
            # Si el usuario está autenticado, obtener su carrito
            carrito, created = Carrito.objects.get_or_create(usuario=request.user)
            if created:
                print(f"Carrito creado para el usuario {request.user.username}")
            serializer = self.get_serializer(carrito)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Para usuarios no autenticados, se usa guest_id
            guest_id = request.data.get('guest_id') or request.query_params.get('guest_id')

            if not guest_id:
                # Si no se proporciona un guest_id, el frontend es responsable de generarlo.
                # Aquí retornamos un 400 y sugerimos que el frontend genere uno.
                # Podrías modificar esto para generar el UUID directamente aquí si lo prefieres.
                return Response(
                    {"detail": "Guest ID no proporcionado. Por favor, proporcione uno (ej. un UUID generado por el frontend)."},
                    status=status.HTTP_400_BAD_REQUEST 
                )

            try:
                carrito = Carrito.objects.get(guest_id=guest_id, usuario__isnull=True)
            except Carrito.DoesNotExist:
                # Si el carrito de invitado no existe, lo creamos
                carrito = Carrito.objects.create(guest_id=guest_id)
                print(f"Carrito de invitado creado con guest_id: {guest_id}")

            serializer = self.get_serializer(carrito)
            return Response(serializer.data, status=status.HTTP_200_OK)

    # Acción para fusionar un carrito de invitado con un carrito de usuario registrado
    @action(detail=False, methods=['post']) # Ya no necesitamos permission_classes aquí
    def fusionar_carrito(self, request):
        # ... (el resto de tu lógica de fusión es correcta) ...
        guest_id = request.data.get('guest_id')
        if not guest_id:
            return Response({"detail": "Guest ID no proporcionado para la fusión."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            carrito_invitado = Carrito.objects.get(guest_id=guest_id, usuario__isnull=True)
        except Carrito.DoesNotExist:
            return Response({"detail": "Carrito de invitado no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        # Obtener o crear el carrito del usuario registrado
        carrito_usuario, created = Carrito.objects.get_or_create(usuario=request.user)

        # Mover los ítems del carrito de invitado al carrito del usuario
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
    permission_classes = [AllowAny] # Permitimos a anónimos modificar ítems si acceden a su carrito

    def get_queryset(self):
        # Aseguramos que solo se puedan modificar ítems del carrito del usuario o del guest_id
        if self.request.user.is_authenticated:
            return ItemCarrito.objects.filter(carrito__usuario=self.request.user)
        else:
            guest_id = self.request.data.get('guest_id') or self.request.query_params.get('guest_id')
            if guest_id:
                return ItemCarrito.objects.filter(carrito__guest_id=guest_id, carrito__usuario__isnull=True)
            return ItemCarrito.objects.none() # No hay guest_id, no se muestran ítems


    def create(self, request, *args, **kwargs):
        # Determinar a qué carrito se añade el ítem
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
                return Response({"detail": "Carrito de invitado no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        
        producto_id = request.data.get('producto_id')
        cantidad = request.data.get('cantidad', 1) # Por defecto 1

        if not producto_id:
            return Response({"detail": "ID de producto es requerido."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            producto = get_object_or_404(Producto, pk=producto_id)
        except Exception: # Captura si el producto no existe
            return Response({"detail": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        # Intentar encontrar el ítem existente
        item_carrito, created = ItemCarrito.objects.get_or_create(
            carrito=carrito,
            producto=producto,
            defaults={'cantidad': cantidad, 'precio_unitario': producto.precio_efectivo} # Guarda el precio efectivo por defecto
        )

        if not created:
            # Si el ítem ya existe, actualiza la cantidad
            item_carrito.cantidad += int(cantidad)
            item_carrito.save()
        
        serializer = self.get_serializer(item_carrito)
        return Response(serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        # Asegurarse de que solo se actualice la cantidad
        partial = kwargs.pop('partial', False)
        instance = self.get_object() # Obtiene el ItemCarrito a actualizar
        
        # Validar que el ítem pertenece al carrito correcto (usuario/guest_id)
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
        instance = self.get_object() # Obtiene el ItemCarrito a eliminar
        
        # Validar que el ítem pertenece al carrito correcto (usuario/guest_id)
        if request.user.is_authenticated:
            if instance.carrito.usuario != request.user:
                return Response({"detail": "No tiene permiso para eliminar este ítem de carrito."}, status=status.HTTP_403_FORBIDDEN)
        else:
            guest_id = request.data.get('guest_id') or request.query_params.get('guest_id')
            if not guest_id or instance.carrito.guest_id != guest_id:
                return Response({"detail": "No tiene permiso o Guest ID inválido para este ítem."}, status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

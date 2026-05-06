    # carritos/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission # Import BasePermission
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django.db.models import F 

from .models import Carrito, ItemCarrito
from .serializers import CarritoSerializer, ItemCarritoSerializer
from productos.models import Producto 
import uuid 

    # Permiso personalizado para ItemCarritoViewSet y CarritoViewSet.retrieve
    # --- CAMBIO CLAVE AQUÍ: Hereda de BasePermission ---
class IsCartOwner(BasePermission):
        """
        Permite el acceso solo al propietario del carrito (usuario autenticado o guest_id).
        """
        def has_permission(self, request, view):
            # Este método se llama para vistas de lista o antes de los permisos a nivel de objeto.
            # Para la acción 'create' (POST), necesitamos asegurar que el usuario esté autenticado
            # o que proporcione un guest_id.
            if request.user.is_authenticated:
                return True # Los usuarios autenticados siempre pueden intentar

            # Para usuarios no autenticados, deben proporcionar un guest_id en los datos de la solicitud o query params
            # Esto es crucial para POST (crear) o GET (listar items de invitado)
            guest_id = request.data.get('guest_id') or request.query_params.get('guest_id')
            if guest_id:
                return True # Guest ID proporcionado, se verificará más a fondo si es el dueño del carrito correcto.
            
            # Si no hay autenticación y no hay guest_id, denegar el acceso.
            return False

        def has_object_permission(self, request, view, obj):
            # obj es una instancia de Carrito o ItemCarrito
            carrito_instance = obj.carrito if isinstance(obj, ItemCarrito) else obj

            # Si el usuario está autenticado, debe ser el dueño del carrito
            if request.user.is_authenticated:
                return carrito_instance.usuario == request.user
            # Si el usuario NO está autenticado, debe proporcionar un guest_id válido
            # y este guest_id debe coincidir con el del carrito.
            guest_id = request.data.get('guest_id') or request.query_params.get('guest_id')
            if guest_id and carrito_instance.guest_id == guest_id and carrito_instance.usuario is None:
                return True
            return False

class CarritoViewSet(viewsets.GenericViewSet):
        queryset = Carrito.objects.all()
        serializer_class = CarritoSerializer

        def get_permissions(self):
            # mi_carrito, fusionar_carrito y retrieve pueden ser accedidos por cualquiera (manejan auth/guest_id internamente)
            # No se necesita AllowAny aquí, ya que IsCartOwner maneja la verificación inicial de permisos.
            if self.action in ['mi_carrito', 'fusionar_carrito', 'retrieve']: 
                return [IsCartOwner()] # <--- Cambiado el permiso aquí
            # Para otras acciones (si las hubiera en un GenericViewSet), requerir autenticación
            return [IsAuthenticated()]

        # --- MÉTODO PARA RECUPERAR UN CARRITO POR ID ---
        def retrieve(self, request, pk=None):
            carrito = self.get_object() 
            # Validar permisos de propietario
            self.check_object_permissions(request, carrito) 
            serializer = self.get_serializer(carrito)
            return Response(serializer.data)

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
                    guest_id = str(uuid.uuid4())
                    carrito = Carrito.objects.create(guest_id=guest_id)
                    print(f"Nuevo carrito de invitado creado con guest_id: {guest_id}")
                    return Response(self.get_serializer(carrito).data, status=status.HTTP_201_CREATED)
                
                try:
                    carrito = Carrito.objects.get(guest_id=guest_id, usuario__isnull=True)
                except Carrito.DoesNotExist:
                    carrito = Carrito.objects.create(guest_id=guest_id)
                    print(f"Carrito de invitado creado con guest_id: {guest_id}")
                
                serializer = self.get_serializer(carrito)
                return Response(serializer.data, status=status.HTTP_200_OK)

        @action(detail=False, methods=['post'])
        def fusionar_carrito(self, request):
            if not request.user.is_authenticated:
                return Response({"detail": "Debe estar autenticado para fusionar un carrito."}, status=status.HTTP_401_UNAUTHORIZED)
            
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
            
            carrito_invitado.items.all().delete() 
            carrito_invitado.delete() 

            carrito_usuario.save() 

            serializer = self.get_serializer(carrito_usuario)
            return Response(serializer.data, status=status.HTTP_200_OK)


class ItemCarritoViewSet(viewsets.ModelViewSet):
        serializer_class = ItemCarritoSerializer
        # --- CAMBIO CLAVE AQUÍ: Solo IsCartOwner ---
        permission_classes = [IsCartOwner] # <--- Eliminado AllowAny, IsCartOwner maneja todos los casos ahora

        def get_queryset(self):
            if self.request.user.is_authenticated:
                return ItemCarrito.objects.filter(carrito__usuario=self.request.user)
            else:
                guest_id = self.request.data.get('guest_id') or self.request.query_params.get('guest_id')
                if guest_id:
                    return ItemCarrito.objects.filter(carrito__guest_id=guest_id, carrito__usuario__isnull=True)
                return ItemCarrito.objects.none() 

        def create(self, request, *args, **kwargs):
            # El método has_permission de IsCartOwner ya asegura que guest_id esté presente para usuarios no autenticados
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            producto = serializer.validated_data['producto']
            cantidad = serializer.validated_data['cantidad']
            
            carrito = None
            if request.user.is_authenticated:
                carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
            else:
                guest_id = request.data.get('guest_id') or request.query_params.get('guest_id')
                # Esta verificación también la realiza IsCartOwner.has_permission, pero se mantiene como medida de seguridad.
                if not guest_id:
                    return Response({"detail": "Guest ID es requerido para usuarios no autenticados."}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    carrito = Carrito.objects.get(guest_id=guest_id, usuario__isnull=True)
                except Carrito.DoesNotExist:
                    carrito = Carrito.objects.create(guest_id=guest_id)
                    print(f"Carrito de invitado creado al añadir ítem: {guest_id}")
                    
            item_carrito, created = ItemCarrito.objects.get_or_create(
                carrito=carrito,
                producto=producto,
                defaults={'cantidad': cantidad, 'precio_unitario': producto.precio_efectivo}
            )

            if not created:
                item_carrito.cantidad += cantidad 
                item_carrito.save()
            
            response_serializer = self.get_serializer(item_carrito)
            return Response(response_serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

        def update(self, request, *args, **kwargs):
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

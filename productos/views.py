# productos/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.serializers import ValidationError

from .models import Categoria, SubCategoria, Producto
from .serializers import (
    CategoriaSerializer,
    SubCategoriaSerializer,
    ProductoSerializer,
    ProductoPublicoSerializer,
)
from usuarios.permissions import IsSeller


# ------------------------------------------------------------------
# 1. CATEGORÍA VIEWSET
# ------------------------------------------------------------------
class CategoriaViewSet(viewsets.ModelViewSet):
    """
    Gestión de categorías de productos.
    - Lectura pública: cualquiera puede ver categorías
    - Escritura: solo el vendedor dueño de la tienda
    """
    serializer_class = CategoriaSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsSeller()]

    def get_queryset(self):
        queryset = Categoria.objects.all()

        # Filtro por tienda
        tienda_id = self.request.query_params.get('tienda_id')
        if tienda_id:
            queryset = queryset.filter(tienda__id=tienda_id)

        return queryset.order_by('orden_display', 'nombre')

    def perform_create(self, serializer):
        tienda_obj = serializer.validated_data['tienda']
        if tienda_obj.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError(
                {"tienda": "No tienes permiso para añadir categorías a esta tienda."}
            )
        serializer.save()

    def perform_update(self, serializer):
        categoria = self.get_object()
        if not self.request.user.is_staff and \
                categoria.tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No tienes permiso para actualizar esta categoría.")
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if not self.request.user.is_staff and \
                instance.tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No tienes permiso para eliminar esta categoría.")
        super().perform_destroy(instance)


# ------------------------------------------------------------------
# 2. SUBCATEGORÍA VIEWSET
# ------------------------------------------------------------------
class SubCategoriaViewSet(viewsets.ModelViewSet):
    """
    Gestión de subcategorías.
    - Lectura pública
    - Escritura: solo el vendedor dueño de la tienda
    """
    serializer_class = SubCategoriaSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsSeller()]

    def get_queryset(self):
        queryset = SubCategoria.objects.all()

        # Filtros
        categoria_id = self.request.query_params.get('categoria_id')
        tienda_id = self.request.query_params.get('tienda_id')

        if categoria_id:
            queryset = queryset.filter(categoria__id=categoria_id)
        if tienda_id:
            queryset = queryset.filter(categoria__tienda__id=tienda_id)

        return queryset.order_by('orden_display', 'nombre')

    def perform_create(self, serializer):
        categoria_obj = serializer.validated_data['categoria']
        if categoria_obj.tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError(
                {"categoria": "No tienes permiso para añadir subcategorías a esta tienda."}
            )
        serializer.save()

    def perform_update(self, serializer):
        subcategoria = self.get_object()
        if not self.request.user.is_staff and \
                subcategoria.categoria.tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No tienes permiso para actualizar esta subcategoría.")
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if not self.request.user.is_staff and \
                instance.categoria.tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No tienes permiso para eliminar esta subcategoría.")
        super().perform_destroy(instance)


# ------------------------------------------------------------------
# 3. PRODUCTO VIEWSET
# ------------------------------------------------------------------
class ProductoViewSet(viewsets.ModelViewSet):
    """
    Gestión de productos.

    Acceso público:
    - GET /productos/ → todos los productos disponibles
    - GET /productos/{id}/ → detalle de un producto
    - GET /productos/?tienda_id=1 → productos de una tienda
    - GET /productos/?disponible=true → solo disponibles
    - GET /productos/?categoria_id=1 → por categoría

    Acceso vendedor:
    - POST/PUT/PATCH/DELETE → gestión de sus productos
    - PATCH /productos/{id}/toggle_disponible/ → activar/desactivar rápido
    """

    def get_serializer_class(self):
        # El vendedor ve el serializer completo con SKU, Loyverse, etc.
        if self.request.user.is_authenticated and \
                hasattr(self.request.user, 'seller_profile'):
            return ProductoSerializer
        return ProductoPublicoSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsSeller()]

    def get_queryset(self):
        queryset = Producto.objects.all()

        # Filtros disponibles para el público
        tienda_id = self.request.query_params.get('tienda_id')
        subcategoria_id = self.request.query_params.get('subcategoria_id')
        categoria_id = self.request.query_params.get('categoria_id')
        disponible = self.request.query_params.get('disponible')

        if tienda_id:
            queryset = queryset.filter(tienda__id=tienda_id)
        if subcategoria_id:
            queryset = queryset.filter(subcategoria__id=subcategoria_id)
        if categoria_id:
            queryset = queryset.filter(subcategoria__categoria__id=categoria_id)
        if disponible and disponible.lower() == 'true':
            queryset = queryset.filter(disponible=True)

        # El público solo ve productos de tiendas activas
        if not self.request.user.is_authenticated or \
                not hasattr(self.request.user, 'seller_profile'):
            queryset = queryset.filter(tienda__activo=True, disponible=True)

        return queryset.order_by('orden_display', 'nombre')

    def perform_create(self, serializer):
        tienda_obj = serializer.validated_data['tienda']
        subcategoria_obj = serializer.validated_data.get('subcategoria')

        if tienda_obj.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError(
                {"tienda": "No tienes permiso para añadir productos a esta tienda."}
            )

        if subcategoria_obj and subcategoria_obj.categoria.tienda != tienda_obj:
            raise ValidationError(
                {"subcategoria": "La subcategoría no pertenece a la tienda seleccionada."}
            )

        # Heredar stock_ilimitado de la tienda si no se especificó
        if 'stock_ilimitado' not in serializer.validated_data:
            serializer.save(
                stock_ilimitado=tienda_obj.stock_ilimitado_default
            )
        else:
            serializer.save()

    def perform_update(self, serializer):
        producto = self.get_object()
        if not self.request.user.is_staff and \
                producto.tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No tienes permiso para actualizar este producto.")
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if not self.request.user.is_staff and \
                instance.tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No tienes permiso para eliminar este producto.")
        super().perform_destroy(instance)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated, IsSeller])
    def toggle_disponible(self, request, pk=None):
        """
        Activa o desactiva un producto rápidamente.
        URL: PATCH /api/productos/{id}/toggle_disponible/
        """
        producto = self.get_object()
        if producto.tienda.propietario_perfil != request.user.seller_profile:
            raise ValidationError("No tienes permiso para modificar este producto.")

        producto.disponible = not producto.disponible
        producto.save(update_fields=['disponible'])

        return Response({
            "id": producto.id,
            "nombre": producto.nombre,
            "disponible": producto.disponible,
            "mensaje": f"Producto {'activado' if producto.disponible else 'desactivado'} correctamente."
        })

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsSeller])
    def mis_productos(self, request):
        """
        Retorna todos los productos del vendedor autenticado.
        URL: GET /api/productos/mis_productos/
        """
        productos = Producto.objects.filter(
            tienda__propietario_perfil=request.user.seller_profile
        ).order_by('tienda', 'orden_display', 'nombre')

        serializer = ProductoSerializer(productos, many=True)
        return Response(serializer.data)

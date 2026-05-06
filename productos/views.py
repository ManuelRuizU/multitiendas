# productos/views.py
# modificado 6/8/2025

from rest_framework import viewsets, status, permissions # Importa 'permissions' aquí
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

# Importamos los modelos de la propia app 'productos'
from .models import Categoria, SubCategoria, Producto

# Importamos los serializadores de la propia app 'productos'
from .serializers import CategoriaSerializer, SubCategoriaSerializer, ProductoSerializer

# Importamos los modelos de otras apps que se necesitan para la lógica de negocio
from tiendas.models import Tienda
from usuarios.models import SellerProfile

# Importamos IsSeller desde usuarios.permissions
from usuarios.permissions import IsSeller, IsOwnerOrReadOnly # Asegúrate de importar IsOwnerOrReadOnly si lo usas en otros ViewSets


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

    def get_permissions(self):
        """
        Permite a cualquiera listar y ver categorías.
        Solo vendedores autenticados pueden crear, actualizar o eliminar categorías.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny] # Lectura pública
        else:
            permission_classes = [permissions.IsAuthenticated, IsSeller] # Escritura solo para vendedores autenticados
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        vendedor_autenticado = self.request.user.seller_profile
        tienda_obj = serializer.validated_data['tienda']

        if tienda_obj.propietario_perfil != vendedor_autenticado:
            raise ValidationError({"tienda": "No tienes permiso para añadir categorías a esta tienda."})

        serializer.save(tienda=tienda_obj)

    def perform_update(self, serializer):
        categoria_a_actualizar = self.get_object()
        if not self.request.user.is_staff and categoria_a_actualizar.tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No tienes permiso para actualizar esta categoría.")
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if not self.request.user.is_staff and instance.tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No tienes permiso para eliminar esta categoría.")
        super().perform_destroy(instance)

    def get_queryset(self):
        queryset = Categoria.objects.all()
        tienda_id = self.request.query_params.get('tienda_id', None)
        if tienda_id is not None:
            queryset = queryset.filter(tienda__id=tienda_id)

        # Si el usuario es un vendedor, solo ve sus propias categorías
        if self.request.user.is_authenticated and hasattr(self.request.user, 'seller_profile') and not self.request.user.is_staff:
            queryset = queryset.filter(tienda__propietario_perfil=self.request.user.seller_profile)

        return queryset


class SubCategoriaViewSet(viewsets.ModelViewSet):
    queryset = SubCategoria.objects.all()
    serializer_class = SubCategoriaSerializer

    def get_permissions(self):
        """
        Permite a cualquiera listar y ver subcategorías.
        Solo vendedores autenticados pueden crear, actualizar o eliminar subcategorías.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny] # Lectura pública
        else:
            permission_classes = [permissions.IsAuthenticated, IsSeller] # Escritura solo para vendedores autenticados
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        vendedor_autenticado = self.request.user.seller_profile
        categoria_obj = serializer.validated_data['categoria']

        if categoria_obj.tienda.propietario_perfil != vendedor_autenticado:
            raise ValidationError({"categoria": "No tienes permiso para añadir subcategorías a esta categoría/tienda."})

        serializer.save(categoria=categoria_obj)

    def perform_update(self, serializer):
        subcategoria_a_actualizar = self.get_object()
        if not self.request.user.is_staff and subcategoria_a_actualizar.categoria.tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No tienes permiso para actualizar esta subcategoría.")
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if not self.request.user.is_staff and instance.categoria.tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No tienes permiso para eliminar esta subcategoría.")
        super().perform_destroy(instance)

    def get_queryset(self):
        queryset = SubCategoria.objects.all()
        categoria_id = self.request.query_params.get('categoria_id', None)
        if categoria_id is not None:
            queryset = queryset.filter(categoria__id=categoria_id)

        # Si el usuario es un vendedor, solo ve sus propias subcategorías
        if self.request.user.is_authenticated and hasattr(self.request.user, 'seller_profile') and not self.request.user.is_staff:
            queryset = queryset.filter(categoria__tienda__propietario_perfil=self.request.user.seller_profile)

        return queryset


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

    def get_permissions(self):
        """
        Permite a cualquiera listar y ver productos.
        Solo vendedores autenticados pueden crear, actualizar o eliminar productos.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny] # Lectura pública
        else:
            permission_classes = [permissions.IsAuthenticated, IsSeller] # Escritura solo para vendedores autenticados
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        vendedor_autenticado = self.request.user.seller_profile
        tienda_obj = serializer.validated_data['tienda']
        subcategoria_obj = serializer.validated_data.get('subcategoria')

        if tienda_obj.propietario_perfil != vendedor_autenticado:
            raise ValidationError({"tienda": "No tienes permiso para añadir productos a esta tienda."})

        if subcategoria_obj and subcategoria_obj.categoria.tienda != tienda_obj:
            raise ValidationError({"subcategoria": "La subcategoría no pertenece a la tienda seleccionada."})

        serializer.save(tienda=tienda_obj, subcategoria=subcategoria_obj)

    def perform_update(self, serializer):
        producto_a_actualizar = self.get_object()
        if not self.request.user.is_staff and producto_a_actualizar.tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No tienes permiso para actualizar este producto.")
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if not self.request.user.is_staff and instance.tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError("No tienes permiso para eliminar este producto.")
        super().perform_destroy(instance)

    def get_queryset(self):
        queryset = Producto.objects.all()
        tienda_id = self.request.query_params.get('tienda_id', None)
        subcategoria_id = self.request.query_params.get('subcategoria_id', None)

        if tienda_id is not None:
            queryset = queryset.filter(tienda__id=tienda_id)
        if subcategoria_id is not None:
            queryset = queryset.filter(subcategoria__id=subcategoria_id)

        # Si el usuario es un vendedor (y no un staff), solo ve sus propios productos
        if self.request.user.is_authenticated and hasattr(self.request.user, 'seller_profile') and not self.request.user.is_staff:
            queryset = queryset.filter(tienda__propietario_perfil=self.request.user.seller_profile)

        return queryset




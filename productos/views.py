# productos/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly # Asegúrate de importar IsAuthenticatedOrReadOnly
from rest_framework.serializers import ValidationError

# Importamos los modelos de la propia app 'productos'
from .models import Categoria, SubCategoria, Producto

# Importamos los serializadores de la propia app 'productos'
from .serializers import CategoriaSerializer, SubCategoriaSerializer, ProductoSerializer

# Importamos los modelos de otras apps que se necesitan para la lógica de negocio
from tiendas.models import Tienda
from usuarios.models import PerfilVendedor


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    # CAMBIO AQUÍ: Permitir lectura a cualquiera, escritura solo a autenticados
    permission_classes = [IsAuthenticatedOrReadOnly] 

    def perform_create(self, serializer):
        # La lógica de validación del vendedor y la tienda es correcta y robusta aquí.
        # Se ejecuta después de que IsAuthenticatedOrReadOnly permita el acceso de escritura.
        if not self.request.user.is_authenticated or not hasattr(self.request.user, 'perfil_vendedor'):
            # Aunque IsAuthenticatedOrReadOnly lo filtraría, esta validación es una buena segunda capa
            raise ValidationError("Solo vendedores pueden crear categorías.")
        
        vendedor_autenticado = self.request.user.perfil_vendedor

        tienda_obj = serializer.validated_data['tienda'] 

        if tienda_obj.vendedor != vendedor_autenticado:
            raise ValidationError("No tienes permiso para añadir categorías a esta tienda.")
        
        serializer.save(tienda=tienda_obj)

    def get_queryset(self):
        queryset = Categoria.objects.all()
        tienda_id = self.request.query_params.get('tienda_id', None)
        if tienda_id is not None:
            queryset = queryset.filter(tienda__id=tienda_id)
        return queryset


class SubCategoriaViewSet(viewsets.ModelViewSet):
    queryset = SubCategoria.objects.all()
    serializer_class = SubCategoriaSerializer
    # CAMBIO AQUÍ: Permitir lectura a cualquiera, escritura solo a autenticados
    permission_classes = [IsAuthenticatedOrReadOnly] 

    def perform_create(self, serializer):
        # La lógica de validación del vendedor y la categoría es correcta y robusta aquí.
        if not self.request.user.is_authenticated or not hasattr(self.request.user, 'perfil_vendedor'):
            raise ValidationError("Solo vendedores pueden crear subcategorías.")
        
        vendedor_autenticado = self.request.user.perfil_vendedor

        categoria_obj = serializer.validated_data['categoria']

        if categoria_obj.tienda.vendedor != vendedor_autenticado:
            raise ValidationError("No tienes permiso para añadir subcategorías a esta categoría/tienda.")
        
        serializer.save(categoria=categoria_obj)

    def get_queryset(self):
        queryset = SubCategoria.objects.all()
        categoria_id = self.request.query_params.get('categoria_id', None)
        if categoria_id is not None:
            queryset = queryset.filter(categoria__id=categoria_id)
        return queryset


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    # CAMBIO AQUÍ: Permitir lectura a cualquiera, escritura solo a autenticados
    permission_classes = [IsAuthenticatedOrReadOnly] 

    def perform_create(self, serializer):
        # La lógica de validación del vendedor y la tienda/subcategoría es correcta y robusta aquí.
        if not self.request.user.is_authenticated or not hasattr(self.request.user, 'perfil_vendedor'):
            raise ValidationError("Solo vendedores pueden crear productos.")
        
        vendedor_autenticado = self.request.user.perfil_vendedor

        tienda_obj = serializer.validated_data['tienda']
        subcategoria_obj = serializer.validated_data.get('subcategoria') 

        if tienda_obj.vendedor != vendedor_autenticado:
            raise ValidationError("No tienes permiso para añadir productos a esta tienda.")
        
        if subcategoria_obj and subcategoria_obj.categoria.tienda != tienda_obj:
            raise ValidationError("La subcategoría no pertenece a la tienda seleccionada.")
            
        serializer.save(tienda=tienda_obj, subcategoria=subcategoria_obj)

    def get_queryset(self):
        queryset = Producto.objects.all()
        tienda_id = self.request.query_params.get('tienda_id', None)
        subcategoria_id = self.request.query_params.get('subcategoria_id', None)

        if tienda_id is not None:
            queryset = queryset.filter(tienda__id=tienda_id)
        if subcategoria_id is not None:
            queryset = queryset.filter(subcategoria__id=subcategoria_id)
        return queryset
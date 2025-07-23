# productos/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.serializers import ValidationError

# Importamos los modelos de la propia app 'productos'
from .models import Categoria, SubCategoria, Producto

# Importamos los serializadores de la propia app 'productos'
from .serializers import CategoriaSerializer, SubCategoriaSerializer, ProductoSerializer

# Importamos los modelos de otras apps que se necesitan para la lógica de negocio
from tiendas.models import Tienda
from usuarios.models import PerfilVendedor

# Permiso personalizado para verificar si el usuario es un vendedor
# Esto es una buena práctica para centralizar la lógica de permisos de vendedor
class IsSeller(IsAuthenticated):
    """
    Permite el acceso solo a usuarios autenticados que tienen un perfil de vendedor.
    """
    def has_permission(self, request, view):
        # Primero, verifica si el usuario está autenticado
        if not super().has_permission(request, view):
            return False
        # Luego, verifica si el usuario tiene un perfil de vendedor
        return hasattr(request.user, 'perfil_vendedor') and request.user.perfil_vendedor.is_complete()

    def has_object_permission(self, request, view, obj):
        # Permite a los vendedores acceder a sus propias categorías/subcategorías/productos
        if request.user.is_staff: # Los superusuarios pueden hacer lo que quieran
            return True
        # Para Categoría, SubCategoría, Producto, el vendedor debe ser el dueño de la tienda asociada
        if isinstance(obj, Categoria):
            return obj.tienda.vendedor.user == request.user
        if isinstance(obj, SubCategoria):
            return obj.categoria.tienda.vendedor.user == request.user
        if isinstance(obj, Producto):
            return obj.tienda.vendedor.user == request.user
        return False


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    # Permite lectura a cualquiera, escritura solo a autenticados (y la lógica perform_create validará si es vendedor)
    permission_classes = [IsAuthenticatedOrReadOnly] # <--- ¡CAMBIO AQUÍ!

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
        
        # Opcional: Si el usuario es un vendedor, solo mostrar sus propias categorías
        if self.request.user.is_authenticated and hasattr(self.request.user, 'perfil_vendedor') and not self.request.user.is_staff:
            queryset = queryset.filter(tienda__vendedor=self.request.user.perfil_vendedor)
            
        return queryset


class SubCategoriaViewSet(viewsets.ModelViewSet):
    queryset = SubCategoria.objects.all()
    serializer_class = SubCategoriaSerializer
    # Permite lectura a cualquiera, escritura solo a autenticados (y la lógica perform_create validará si es vendedor)
    permission_classes = [IsAuthenticatedOrReadOnly] # <--- ¡CAMBIO AQUÍ!

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

        # Opcional: Si el usuario es un vendedor, solo mostrar sus propias subcategorías
        if self.request.user.is_authenticated and hasattr(self.request.user, 'perfil_vendedor') and not self.request.user.is_staff:
            queryset = queryset.filter(categoria__tienda__vendedor=self.request.user.perfil_vendedor)
            
        return queryset


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    # Permite lectura a cualquiera, escritura solo a autenticados (y la lógica perform_create validará si es vendedor)
    permission_classes = [IsAuthenticatedOrReadOnly] # <--- ¡CAMBIO AQUÍ!

    def perform_create(self, serializer):
        # La lógica de validación del vendedor y la tienda/subcategoría es correcta y robusta aquí.
        if not self.request.user.is_authenticated or not hasattr(self.request.user, 'perfil_vendedor'):
            raise ValidationError("Solo vendedores pueden crear productos.")
        
        vendedor_autenticado = self.request.user.perfil_vendedor

        tienda_obj = serializer.validated_data['tienda']
        subcategoria_obj = serializer.validated_data.get('subcategoria') 

        # Validar que la tienda seleccionada pertenece al vendedor autenticado
        if tienda_obj.vendedor != vendedor_autenticado:
            raise ValidationError({"tienda": "No tienes permiso para añadir productos a esta tienda."})
        
        # Validar que la subcategoría (si se proporciona) pertenece a la tienda seleccionada
        if subcategoria_obj and subcategoria_obj.categoria.tienda != tienda_obj:
            raise ValidationError({"subcategoria": "La subcategoría no pertenece a la tienda seleccionada."})
            
        serializer.save(tienda=tienda_obj, subcategoria=subcategoria_obj)

    def get_queryset(self):
        queryset = Producto.objects.all()
        tienda_id = self.request.query_params.get('tienda_id', None)
        subcategoria_id = self.request.query_params.get('subcategoria_id', None)

        if tienda_id is not None:
            queryset = queryset.filter(tienda__id=tienda_id)
        if subcategoria_id is not None:
            queryset = queryset.filter(subcategoria__id=subcategoria_id)

        # Opcional: Si el usuario es un vendedor, solo mostrar sus propios productos
        if self.request.user.is_authenticated and hasattr(self.request.user, 'perfil_vendedor') and not self.request.user.is_staff:
            queryset = queryset.filter(tienda__vendedor=self.request.user.perfil_vendedor)
            
        return queryset


    
    
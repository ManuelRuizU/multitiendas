# productos/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
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
    permission_classes = [IsAuthenticated] # ¡Recomendación! Permitir crear solo a autenticados.

    def perform_create(self, serializer):
        # 1. Validar que el usuario sea autenticado y tenga un perfil de vendedor
        if not self.request.user.is_authenticated or not hasattr(self.request.user, 'perfil_vendedor'):
            raise ValidationError("Solo vendedores pueden crear categorías.")
        
        vendedor_autenticado = self.request.user.perfil_vendedor

        # 2. El campo 'tienda' del serializador ya es el objeto Tienda (gracias a PrimaryKeyRelatedField)
        # Si el ID de la tienda no se envió o no es válido, el serializador ya habría
        # lanzado un ValidationError antes de llegar a perform_create.
        tienda_obj = serializer.validated_data['tienda'] # Obtenemos el objeto Tienda directamente

        # 3. Validar que la tienda pertenezca al vendedor autenticado
        if tienda_obj.vendedor != vendedor_autenticado:
            raise ValidationError("No tienes permiso para añadir categorías a esta tienda.")
        
        # 4. Guardar la instancia, asignando la tienda validada
        serializer.save(tienda=tienda_obj)


    # Filtrar categorías por tienda si se pasa el parámetro `tienda_id`
    def get_queryset(self):
        queryset = Categoria.objects.all()
        tienda_id = self.request.query_params.get('tienda_id', None)
        if tienda_id is not None:
            queryset = queryset.filter(tienda__id=tienda_id)
        return queryset


class SubCategoriaViewSet(viewsets.ModelViewSet):
    queryset = SubCategoria.objects.all()
    serializer_class = SubCategoriaSerializer
    permission_classes = [IsAuthenticated] # ¡Recomendación! Permitir crear solo a autenticados.

    def perform_create(self, serializer):
        # 1. Validar que el usuario sea autenticado y tenga un perfil de vendedor
        if not self.request.user.is_authenticated or not hasattr(self.request.user, 'perfil_vendedor'):
            raise ValidationError("Solo vendedores pueden crear subcategorías.")
        
        vendedor_autenticado = self.request.user.perfil_vendedor

        # 2. El campo 'categoria' del serializador ya es el objeto Categoria.
        categoria_obj = serializer.validated_data['categoria']

        # 3. Validar que la categoría (y por ende su tienda) pertenezca al vendedor autenticado
        if categoria_obj.tienda.vendedor != vendedor_autenticado:
            raise ValidationError("No tienes permiso para añadir subcategorías a esta categoría/tienda.")
        
        # 4. Guardar la instancia, asignando la categoría validada
        serializer.save(categoria=categoria_obj)

    # Filtrar subcategorías por categoría si se pasa el parámetro `categoria_id`
    def get_queryset(self):
        queryset = SubCategoria.objects.all()
        categoria_id = self.request.query_params.get('categoria_id', None)
        if categoria_id is not None:
            queryset = queryset.filter(categoria__id=categoria_id)
        return queryset


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated] # ¡Recomendación! Permitir crear solo a autenticados.

    def perform_create(self, serializer):
        # 1. Validar que el usuario sea autenticado y tenga un perfil de vendedor
        if not self.request.user.is_authenticated or not hasattr(self.request.user, 'perfil_vendedor'):
            raise ValidationError("Solo vendedores pueden crear productos.")
        
        vendedor_autenticado = self.request.user.perfil_vendedor

        # 2. Obtener los objetos Tienda y SubCategoria (si existe) del validated_data
        tienda_obj = serializer.validated_data['tienda']
        subcategoria_obj = serializer.validated_data.get('subcategoria') # subcategoria_obj será None si no se envió

        # 3. Validar permisos y relaciones
        if tienda_obj.vendedor != vendedor_autenticado:
            raise ValidationError("No tienes permiso para añadir productos a esta tienda.")
        
        if subcategoria_obj and subcategoria_obj.categoria.tienda != tienda_obj:
            raise ValidationError("La subcategoría no pertenece a la tienda seleccionada.")
            
        # 4. Guardar la instancia, asignando los objetos validados
        serializer.save(tienda=tienda_obj, subcategoria=subcategoria_obj)

    # Filtrar productos por tienda o subcategoría
    def get_queryset(self):
        queryset = Producto.objects.all()
        tienda_id = self.request.query_params.get('tienda_id', None)
        subcategoria_id = self.request.query_params.get('subcategoria_id', None)

        if tienda_id is not None:
            queryset = queryset.filter(tienda__id=tienda_id)
        if subcategoria_id is not None:
            queryset = queryset.filter(subcategoria__id=subcategoria_id)
        return queryset
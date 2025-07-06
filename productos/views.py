# productos/views.py
from rest_framework import viewsets, status # ¡Asegúrate de que 'status' esté importado si lo usas!
from rest_framework.response import Response # Importar Response si se usa directamente
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.serializers import ValidationError # ¡Importar ValidationError directamente!

# Importamos los modelos de la propia app 'productos'
from .models import Categoria, SubCategoria, Producto

# Importamos los serializadores de la propia app 'productos'
from .serializers import CategoriaSerializer, SubCategoriaSerializer, ProductoSerializer

# Importamos los modelos de otras apps que se necesitan para la lógica de negocio
from tiendas.models import Tienda # Necesario para la relación con Tienda
from usuarios.models import PerfilVendedor # Necesario para validar si el usuario es un vendedor


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny] # Permite ver categorías públicamente

    # Al crear una categoría, automáticamente asignarla a una tienda del vendedor autenticado
    def perform_create(self, serializer):
        # 1. Validar que el usuario sea autenticado y tenga un perfil de vendedor
        if not self.request.user.is_authenticated or not hasattr(self.request.user, 'perfil_vendedor'):
            raise ValidationError("Solo vendedores pueden crear categorías.")
        
        vendedor_autenticado = self.request.user.perfil_vendedor

        # 2. Obtener la tienda del validated_data.
        # En el serializador de Categoria, 'tienda_id' debería ser write_only y 'tienda' read_only.
        # Por lo tanto, serializer.validated_data.get('tienda') contendría el OBJETO Tienda si el serializer lo maneja,
        # o necesitaríamos buscarlo por ID si solo se envía el ID.
        # Asumo que el serializador de Categoria tiene un campo 'tienda_id' para escritura.
        tienda_id = serializer.validated_data.get('tienda_id') # Obtener el ID de la tienda
        if not tienda_id:
            raise ValidationError("Debe especificar la tienda para la categoría (tienda_id).")
        
        try:
            tienda_obj = Tienda.objects.get(id=tienda_id)
        except Tienda.DoesNotExist:
            raise ValidationError("La tienda especificada no existe.")
            
        # 3. Validar que la tienda pertenezca al vendedor autenticado
        if tienda_obj.vendedor != vendedor_autenticado:
            raise ValidationError("No tienes permiso para añadir categorías a esta tienda.")
        
        # 4. Guardar la instancia, asignando la tienda validada
        serializer.save(tienda=tienda_obj) # Pasamos el objeto Tienda


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
    permission_classes = [AllowAny]

    # Al crear una subcategoría, asegurar que la categoría pertenezca a la tienda del vendedor autenticado
    def perform_create(self, serializer):
        # 1. Validar que el usuario sea autenticado y tenga un perfil de vendedor
        if not self.request.user.is_authenticated or not hasattr(self.request.user, 'perfil_vendedor'):
            raise ValidationError("Solo vendedores pueden crear subcategorías.")
        
        vendedor_autenticado = self.request.user.perfil_vendedor

        # 2. Obtener la categoría del validated_data.
        # Asumo que el serializador de SubCategoria tiene un campo 'categoria_id' para escritura.
        categoria_id = serializer.validated_data.get('categoria_id')
        if not categoria_id:
            raise ValidationError("Debe especificar la categoría para la subcategoría (categoria_id).")

        try:
            categoria_obj = Categoria.objects.get(id=categoria_id)
        except Categoria.DoesNotExist:
            raise ValidationError("La categoría especificada no existe.")

        # 3. Validar que la categoría (y por ende su tienda) pertenezca al vendedor autenticado
        if categoria_obj.tienda.vendedor != vendedor_autenticado:
            raise ValidationError("No tienes permiso para añadir subcategorías a esta categoría/tienda.")
        
        # 4. Guardar la instancia, asignando la categoría validada
        serializer.save(categoria=categoria_obj) # Pasamos el objeto Categoria

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
    permission_classes = [AllowAny] # Permite ver productos públicamente

    # Al crear un producto, asegurar que la tienda y subcategoría pertenezcan al vendedor autenticado
    def perform_create(self, serializer):
        # 1. Validar que el usuario sea autenticado y tenga un perfil de vendedor
        if not self.request.user.is_authenticated or not hasattr(self.request.user, 'perfil_vendedor'):
            raise ValidationError("Solo vendedores pueden crear productos.")
        
        vendedor_autenticado = self.request.user.perfil_vendedor

        # 2. Obtener la tienda y subcategoría de los IDs enviados
        tienda_id = serializer.validated_data.get('tienda_id')
        subcategoria_id = serializer.validated_data.get('subcategoria_id')
        
        if not tienda_id:
            raise ValidationError("Debe especificar la tienda para el producto (tienda_id).")
        
        try:
            tienda_obj = Tienda.objects.get(id=tienda_id)
        except Tienda.DoesNotExist:
            raise ValidationError("La tienda especificada no existe.")
            
        subcategoria_obj = None
        if subcategoria_id: # La subcategoría puede ser opcional
            try:
                subcategoria_obj = SubCategoria.objects.get(id=subcategoria_id)
            except SubCategoria.DoesNotExist:
                raise ValidationError("La subcategoría especificada no existe.")

        # 3. Validar permisos y relaciones
        if tienda_obj.vendedor != vendedor_autenticado:
            raise ValidationError("No tienes permiso para añadir productos a esta tienda.")
        
        if subcategoria_obj and subcategoria_obj.categoria.tienda != tienda_obj:
            raise ValidationError("La subcategoría no pertenece a la tienda seleccionada.")
            
        # 4. Guardar la instancia, asignando los objetos validados
        serializer.save(tienda=tienda_obj, subcategoria=subcategoria_obj) # Pasamos los objetos Tienda y SubCategoria

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
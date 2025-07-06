# tiendas/views.py
from rest_framework import viewsets
from .models import Tienda, RadioEnvio
from .serializers import TiendaSerializer, RadioEnvioSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny # Permisos
from rest_framework.serializers import ValidationError # ¡Importar ValidationError directamente!

# Importamos el modelo PerfilVendedor de la app 'usuarios' si no lo tienes ya en tus models.py
# Aunque en este caso, se accede a través de self.request.user.perfil_vendedor, no se necesita importar el modelo directamente
# PERO si la validación lo requiere para hacer un .get() por ejemplo, SÍ se necesitaría.
# Sin embargo, para los errores que describes, la línea de ValidationError es suficiente.

class TiendaViewSet(viewsets.ModelViewSet):
    queryset = Tienda.objects.all()
    serializer_class = TiendaSerializer
    permission_classes = [AllowAny] # Permite ver todas las tiendas para todos

    # Solo el vendedor asociado o un superusuario puede editar/borrar su tienda
    def get_permissions(self):
        # NOTA: Para implementar una clase de permiso personalizada para el dueño,
        # necesitarías crear un permissions.py en tu app 'tiendas'
        # Por ahora, IsAuthenticated basta para exigir login.
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated] # O una clase de permiso personalizada (IsOwnerOrAdmin)
        # Para 'create', la lógica de perform_create ya maneja el permiso del vendedor
        elif self.action == 'create':
            self.permission_classes = [IsAuthenticated] # Solo usuarios autenticados pueden intentar crear
        return super().get_permissions()

    # Opcional: Filtrar tiendas por el vendedor actual para listados específicos
    def get_queryset(self):
        # Si la acción es de listado y el usuario es vendedor, filtra por sus tiendas
        if self.action == 'list' and self.request.user.is_authenticated and hasattr(self.request.user, 'perfil_vendedor'):
            return Tienda.objects.filter(vendedor=self.request.user.perfil_vendedor)
        # Si el usuario no es vendedor o la acción no es 'list', o se permite AllowAny para 'retrieve',
        # regresamos el queryset completo o ajustamos la lógica.
        # Para ver todas las tiendas (si permission_classes = [AllowAny]), necesitamos el queryset completo
        # a menos que haya un parámetro de filtro específico.
        # Si quieres que 'retrieve' (ver una tienda por ID) sea público:
        if self.action == 'retrieve':
            return Tienda.objects.all()
        # Para el resto (create, update, destroy), el queryset se maneja internamente.
        # Para el caso por defecto de 'list' para no-autenticados, también queremos todas las tiendas.
        return Tienda.objects.all() # Valor por defecto si no se aplica un filtro específico


    # Al crear una tienda, automáticamente asignarla al vendedor autenticado
    def perform_create(self, serializer):
        if self.request.user.is_authenticated and hasattr(self.request.user, 'perfil_vendedor'):
            serializer.save(vendedor=self.request.user.perfil_vendedor)
        else:
            # Ahora usa ValidationError directamente porque la importaste
            raise ValidationError("Solo vendedores registrados pueden crear tiendas.")


class RadioEnvioViewSet(viewsets.ModelViewSet):
    queryset = RadioEnvio.objects.all()
    serializer_class = RadioEnvioSerializer
    permission_classes = [IsAuthenticated] # Solo usuarios autenticados pueden ver/editar radios

    # Asegurar que solo se pueda ver/editar radios de las tiendas del vendedor autenticado
    def get_queryset(self):
        if self.request.user.is_authenticated and hasattr(self.request.user, 'perfil_vendedor'):
            # Filtra los radios de envío por las tiendas que pertenecen al vendedor autenticado
            return RadioEnvio.objects.filter(tienda__vendedor=self.request.user.perfil_vendedor)
        return RadioEnvio.objects.none() # No mostrar nada si no está autenticado como vendedor

    # Al crear, asegurar que el radio se asocie a una tienda del vendedor actual
    def perform_create(self, serializer):
        # Asegúrate de obtener el objeto Tienda, no solo el ID
        # Asumiendo que tu RadioEnvioSerializer tiene un campo 'tienda_id' para escritura
        tienda_id = serializer.validated_data.get('tienda_id')
        if not tienda_id:
            raise ValidationError("Debe especificar la tienda para el radio de envío (tienda_id).")
        
        try:
            tienda_obj = Tienda.objects.get(id=tienda_id)
        except Tienda.DoesNotExist:
            raise ValidationError("La tienda especificada no existe.")
            
        if not self.request.user.is_authenticated or not hasattr(self.request.user, 'perfil_vendedor'):
            raise ValidationError("Solo vendedores pueden crear radios de envío.")

        # Ahora sí, compara el vendedor de la tienda con el vendedor autenticado
        if tienda_obj.vendedor != self.request.user.perfil_vendedor:
            raise ValidationError("No tienes permiso para añadir radios de envío a esta tienda.")
            
        # Guarda la instancia, asignando el objeto Tienda validado
        serializer.save(tienda=tienda_obj)
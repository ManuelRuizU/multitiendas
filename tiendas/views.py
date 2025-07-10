# tiendas/views.py
from rest_framework import viewsets
from .models import Tienda, RadioEnvio
from .serializers import TiendaSerializer, RadioEnvioSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.serializers import ValidationError

# No es necesario importar PerfilVendedor aquí, ya que se accede a través de self.request.user.perfil_vendedor.

class TiendaViewSet(viewsets.ModelViewSet):
    queryset = Tienda.objects.all()
    serializer_class = TiendaSerializer
    permission_classes = [AllowAny] # Permite ver todas las tiendas para todos

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy', 'create']:
            # Solo usuarios autenticados pueden crear, actualizar o borrar tiendas.
            # Para una lógica más granular (ej. solo el dueño puede modificar su tienda),
            # necesitarías una clase de permiso personalizada (IsOwnerOrAdmin).
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_queryset(self):
        # Si la acción es de listado y el usuario es vendedor, filtra por sus tiendas
        if self.action == 'list' and self.request.user.is_authenticated and hasattr(self.request.user, 'perfil_vendedor'):
            return Tienda.objects.filter(vendedor=self.request.user.perfil_vendedor)
        # Para 'retrieve' (ver una tienda por ID) y 'list' para no-autenticados,
        # o cualquier otra acción no específica, regresamos el queryset completo.
        return Tienda.objects.all()

    def perform_create(self, serializer):
        if self.request.user.is_authenticated and hasattr(self.request.user, 'perfil_vendedor'):
            serializer.save(vendedor=self.request.user.perfil_vendedor)
        else:
            raise ValidationError("Solo vendedores registrados pueden crear tiendas.")


class RadioEnvioViewSet(viewsets.ModelViewSet):
    queryset = RadioEnvio.objects.all()
    serializer_class = RadioEnvioSerializer
    permission_classes = [IsAuthenticated] # Solo usuarios autenticados pueden ver/editar radios

    def get_queryset(self):
        if self.request.user.is_authenticated and hasattr(self.request.user, 'perfil_vendedor'):
            # Filtra los radios de envío por las tiendas que pertenecen al vendedor autenticado
            return RadioEnvio.objects.filter(tienda__vendedor=self.request.user.perfil_vendedor)
        return RadioEnvio.objects.none() # No mostrar nada si no está autenticado como vendedor

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated or not hasattr(self.request.user, 'perfil_vendedor'):
            raise ValidationError("Solo vendedores pueden crear radios de envío.")
        
        vendedor_autenticado = self.request.user.perfil_vendedor

        # ¡CORREGIDO! El campo 'tienda' del serializador ya es el objeto Tienda (PrimaryKeyRelatedField).
        # Si el ID de la tienda no es válido o no se envió, el serializador ya habrá lanzado un ValidationError.
        tienda_obj = serializer.validated_data['tienda'] 
            
        # Compara el vendedor de la tienda con el vendedor autenticado
        if tienda_obj.vendedor != vendedor_autenticado:
            raise ValidationError("No tienes permiso para añadir radios de envío a esta tienda.")
                
        # Guarda la instancia, asignando el objeto Tienda validado
        serializer.save(tienda=tienda_obj)
# tiendas/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.serializers import ValidationError
from rest_framework.decorators import action # Importamos 'action' para métodos personalizados

from .models import Tienda, RadioEnvio
from .serializers import TiendaSerializer, RadioEnvioSerializer

# No es necesario importar PerfilVendedor aquí, ya que se accede a través de self.request.user.perfil_vendedor.

class TiendaViewSet(viewsets.ModelViewSet):
    queryset = Tienda.objects.all()
    serializer_class = TiendaSerializer
    permission_classes = [AllowAny] # Permite ver todas las tiendas para todos por defecto

    def get_permissions(self):
        # Permisos para acciones específicas:
        # 'create' requiere autenticación (validado en perform_create)
        # 'update', 'partial_update', 'destroy' requieren autenticación (y deberían ser solo para el dueño/admin)
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated]
        # Para el método 'calcular_envio', lo configuramos con AllowAny directamente en el decorador @action
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

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def calcular_envio(self, request, pk=None):
        """
        Calcula el costo de envío para una tienda específica.
        Requiere un parámetro 'distancia_km' en la query string.
        Ej: /api/tiendas/tiendas/{id}/calcular_envio/?distancia_km=X.X
        """
        try:
            tienda = self.get_object() # Obtiene la instancia de la tienda basada en el 'pk' de la URL
        except Tienda.DoesNotExist:
            return Response({'detail': 'Tienda no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        distancia_km_str = request.query_params.get('distancia_km')

        if not distancia_km_str:
            return Response({'detail': 'Parámetro "distancia_km" es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Se asegura que la distancia sea un número válido y positivo.
            distancia_km_float = float(distancia_km_str)
            if distancia_km_float < 0:
                raise ValueError
        except ValueError:
            return Response({'detail': 'La distancia_km debe ser un número positivo válido.'}, status=status.HTTP_400_BAD_REQUEST)

        costo = tienda.calcular_costo_envio(distancia_km_float)

        if costo is not None:
            return Response({'costo_envio': costo}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Distancia fuera del radio de cobertura para esta tienda.', 'costo_envio': None}, status=status.HTTP_404_NOT_FOUND)


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
        
        
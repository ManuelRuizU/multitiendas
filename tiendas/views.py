# tiendas/views.py
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.serializers import ValidationError
from rest_framework.decorators import action

from .models import Tienda, RadioEnvio, CuadranteEnvio
from .serializers import (
    TiendaSerializer,
    TiendaPublicaSerializer,
    RadioEnvioSerializer,
    CuadranteEnvioSerializer,
)
from usuarios.permissions import IsSeller, IsOwnerOrReadOnly


# ------------------------------------------------------------------
# 1. TIENDA VIEWSET
# ------------------------------------------------------------------
class TiendaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar las Tiendas.

    Acceso público:
    - GET /tiendas/ → todas las tiendas activas (serializer público)
    - GET /tiendas/{slug}/ → detalle de una tienda activa

    Acceso vendedor:
    - POST /tiendas/ → crear tienda (requiere IsSeller)
    - PUT/PATCH /tiendas/{slug}/ → editar su tienda
    - DELETE /tiendas/{slug}/ → eliminar su tienda

    Acceso especial:
    - GET /tiendas/{slug}/calcular_envio/?lat=X&lng=Y → costo de envío
    - GET /tiendas/mis_tiendas/ → tiendas del vendedor autenticado
    """
    lookup_field = 'slug'

    def get_serializer_class(self):
        # El panel del vendedor usa el serializer completo
        if self.request.user.is_authenticated and hasattr(
            self.request.user, 'seller_profile'
        ):
            return TiendaSerializer
        # El público usa el serializer reducido
        return TiendaPublicaSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsSeller()]
        return [AllowAny()]

    def get_queryset(self):
        user = self.request.user
        qs = Tienda.objects.all() if (user.is_authenticated and user.is_staff) else Tienda.objects.filter(activo=True)
        tipo = self.request.query_params.get('tipo_negocio')
        if tipo:
            qs = qs.filter(tipo_negocio=tipo)
        return qs

    def perform_create(self, serializer):
        if not hasattr(self.request.user, 'seller_profile'):
            raise ValidationError(
                "El usuario no tiene un perfil de vendedor asociado."
            )
        serializer.save(propietario_perfil=self.request.user.seller_profile)

    def perform_update(self, serializer):
        tienda = self.get_object()
        if (
            not self.request.user.is_staff and
            tienda.propietario_perfil != self.request.user.seller_profile
        ):
            raise ValidationError(
                "No tienes permiso para modificar esta tienda."
            )
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if (
            not self.request.user.is_staff and
            instance.propietario_perfil != self.request.user.seller_profile
        ):
            raise ValidationError(
                "No tienes permiso para eliminar esta tienda."
            )
        instance.delete()

    # --- Acciones personalizadas ---

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsSeller]
    )
    def mis_tiendas(self, request):
        """
        Retorna solo las tiendas del vendedor autenticado.
        URL: GET /api/tiendas/tiendas/mis_tiendas/
        """
        tiendas = Tienda.objects.filter(
            propietario_perfil=request.user.seller_profile
        )
        serializer = TiendaSerializer(tiendas, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[AllowAny]
    )
    def calcular_envio(self, request, pk=None):
        """
        Calcula el costo de envío para una dirección dada.
        Usa Ray Casting para cuadrantes + Haversine para radios.

        URL: GET /api/tiendas/tiendas/{id}/calcular_envio/?lat=-37.79&lng=-72.71

        Respuesta exitosa:
        {
            "tienda": "Mi Tienda",
            "costo_envio": 1000,
            "cubierto": true,
            "tipo": "cuadrante" | "radio"
        }
        """
        tienda = self.get_object()
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')

        if not lat or not lng:
            return Response(
                {'detail': 'Se requieren los parámetros "lat" y "lng".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            return Response(
                {'detail': 'Los parámetros "lat" y "lng" deben ser números.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Verificar cuadrante primero
            cuadrante = tienda.verificar_cuadrante(lat, lng)
            if cuadrante:
                costo = 0 if cuadrante.envio_gratis else cuadrante.costo_envio
                return Response({
                    'tienda': tienda.nombre,
                    'costo_envio': costo,
                    'cubierto': True,
                    'tipo': 'cuadrante',
                    'zona': cuadrante.nombre,
                })

            # Si no hay cuadrante, calcular por radio
            costo = tienda.calcular_costo_envio(lat, lng)
            if costo is not None:
                return Response({
                    'tienda': tienda.nombre,
                    'costo_envio': costo,
                    'cubierto': True,
                    'tipo': 'radio',
                })

            return Response({
                'tienda': tienda.nombre,
                'detail': 'La dirección está fuera del área de cobertura.',
                'costo_envio': None,
                'cubierto': False,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'detail': f'Error en el cálculo: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ------------------------------------------------------------------
# 2. RADIO DE ENVÍO VIEWSET
# ------------------------------------------------------------------
class RadioEnvioViewSet(viewsets.ModelViewSet):
    """
    Gestiona los radios de cobertura de las tiendas del vendedor.
    Solo el vendedor dueño de la tienda puede gestionarlos.
    """
    serializer_class = RadioEnvioSerializer
    permission_classes = [IsSeller]

    def get_queryset(self):
        if self.request.user.is_staff:
            return RadioEnvio.objects.all()
        if hasattr(self.request.user, 'seller_profile'):
            return RadioEnvio.objects.filter(
                tienda__propietario_perfil=self.request.user.seller_profile
            )
        return RadioEnvio.objects.none()

    def perform_create(self, serializer):
        tienda = serializer.validated_data['tienda']
        if tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError(
                "No puedes añadir radios a una tienda que no te pertenece."
            )
        serializer.save()


# ------------------------------------------------------------------
# 3. CUADRANTE DE ENVÍO VIEWSET
# ------------------------------------------------------------------
class CuadranteEnvioViewSet(viewsets.ModelViewSet):
    """
    Gestiona los cuadrantes (polígonos) de cobertura de las tiendas.
    Solo el vendedor dueño de la tienda puede gestionarlos.
    """
    serializer_class = CuadranteEnvioSerializer
    permission_classes = [IsSeller]

    def get_queryset(self):
        if self.request.user.is_staff:
            return CuadranteEnvio.objects.all()
        if hasattr(self.request.user, 'seller_profile'):
            return CuadranteEnvio.objects.filter(
                tienda__propietario_perfil=self.request.user.seller_profile
            )
        return CuadranteEnvio.objects.none()

    def perform_create(self, serializer):
        tienda = serializer.validated_data['tienda']
        if tienda.propietario_perfil != self.request.user.seller_profile:
            raise ValidationError(
                "No puedes añadir cuadrantes a una tienda que no te pertenece."
            )
        serializer.save()
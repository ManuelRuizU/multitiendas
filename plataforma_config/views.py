# plataforma_config/views.py
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny

from .models import PlatformSetting, CategoriaTienda
from .serializers import (
    PlatformSettingPublicSerializer,
    PlatformSettingAdminSerializer,
    CategoriaTiendaSerializer,
)


class PlatformSettingView(APIView):
    """
    GET  /api/configuracion/ → público, devuelve config para el frontend
    PUT  /api/configuracion/ → solo admin, actualiza la configuración
    PATCH /api/configuracion/ → solo admin, actualización parcial
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def get_object(self):
        return PlatformSetting.get_settings()

    def get(self, request):
        config = self.get_object()
        serializer = PlatformSettingPublicSerializer(config)
        return Response(serializer.data)

    def put(self, request):
        config = self.get_object()
        serializer = PlatformSettingAdminSerializer(config, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request):
        config = self.get_object()
        serializer = PlatformSettingAdminSerializer(
            config, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CategoriaTiendaListView(generics.ListAPIView):
    """
    GET /api/categorias-plataforma/
    Categorías activas ordenadas por 'orden'. Público.
    El frontend las usa para el orbital de la página principal.
    """
    queryset           = CategoriaTienda.objects.filter(activo=True)
    serializer_class   = CategoriaTiendaSerializer
    permission_classes = [AllowAny]

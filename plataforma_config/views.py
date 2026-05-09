# plataforma_config/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny

from .models import PlatformSetting
from .serializers import PlatformSettingPublicSerializer, PlatformSettingAdminSerializer


class PlatformSettingView(APIView):
    """
    Configuración global de la plataforma.

    GET  /api/configuracion/ → público, devuelve config para el frontend
    PUT  /api/configuracion/ → solo admin, actualiza la configuración
    PATCH /api/configuracion/ → solo admin, actualización parcial
    """

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def get_object(self):
        """Siempre retorna la única instancia, creándola si no existe."""
        return PlatformSetting.get_settings()

    def get(self, request):
        """
        Retorna la configuración pública de la plataforma.
        El frontend llama esto al iniciar para obtener nombre, logo y colores.
        """
        config = self.get_object()
        serializer = PlatformSettingPublicSerializer(config)
        return Response(serializer.data)

    def put(self, request):
        """Actualización completa — solo admin."""
        config = self.get_object()
        serializer = PlatformSettingAdminSerializer(
            config,
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request):
        """Actualización parcial — solo admin."""
        config = self.get_object()
        serializer = PlatformSettingAdminSerializer(
            config,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
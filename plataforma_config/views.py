# plataforma_config/views.py
from rest_framework import viewsets, status # ¡Añadido 'status' para usar códigos HTTP!
from rest_framework.response import Response # Asegúrate de que Response esté importado si lo usas
from .models import PlatformSetting
from .serializers import PlatformSettingSerializer
from rest_framework.permissions import IsAdminUser, AllowAny

class PlatformSettingViewSet(viewsets.ModelViewSet):
    queryset = PlatformSetting.objects.all()
    serializer_class = PlatformSettingSerializer

    # Permitir a cualquiera obtener la configuración, pero solo a admins modificarla
    def get_permissions(self):
        # Es importante instanciar las clases de permiso.
        # Las clases de permiso en DRF son clases, no simples booleanos.
        if self.action in ['list', 'retrieve']: # GET requests
            self.permission_classes = [AllowAny]
        else: # POST, PUT, PATCH, DELETE requests
            self.permission_classes = [IsAdminUser] # Solo superusuarios pueden modificar
        
        # Debes llamar al método get_permissions del padre después de asignar self.permission_classes
        # para que se procesen correctamente las permisos.
        return [permission() for permission in self.permission_classes] # Correcta forma de devolver permisos instanciados

    # Opcional: Asegurar que solo haya una instancia
    def get_object(self):
        # Siempre intenta obtener la primera instancia de PlatformSetting.
        # Si no existe, la crea. Esto asegura que siempre haya una configuración disponible.
        obj = PlatformSetting.objects.first()
        if not obj:
            # Crea una si no existe. Esto es seguro porque 'create' se impide si ya existe una.
            # Puedes inicializarla con valores predeterminados si tu modelo PlatformSetting los tiene.
            obj = PlatformSetting.objects.create() 
        
        # Después de obtener o crear el objeto, se deben verificar los permisos del objeto.
        self.check_object_permissions(self.request, obj)
        return obj

    # Impedir la creación de nuevas instancias si ya existe una
    def create(self, request, *args, **kwargs):
        # Aquí también debemos asegurar que solo los admins puedan intentar crear.
        # Esto se maneja con get_permissions, pero es una doble capa de seguridad.
        if PlatformSetting.objects.exists():
            return Response({"detail": "Solo puede existir una configuración de plataforma."},
                            status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    # Impedir la eliminación
    def destroy(self, request, *args, **kwargs):
        # No tiene sentido intentar verificar el objeto si de todas formas se va a impedir la eliminación.
        # Eliminamos la llamada a get_object si el objetivo es siempre prohibir.
        return Response({"detail": "La configuración de plataforma no puede ser eliminada."},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    # Opcional: Para el método update (PUT/PATCH), asegurarse de que siempre opere sobre la única instancia
    def update(self, request, *args, **kwargs):
        # Aseguramos que el método update siempre opere sobre la única instancia de configuración.
        # Esto es especialmente útil si las URLs permiten IDs y no queremos que alguien intente actualizar
        # una instancia inexistente o diferente.
        # get_object ya se encarga de obtener la única instancia y verificar permisos de objeto.
        self.kwargs['pk'] = self.get_object().pk # Sobreescribir pk para asegurar que actualiza el objeto correcto
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        # Lo mismo para partial_update
        self.kwargs['pk'] = self.get_object().pk
        return super().partial_update(request, *args, **kwargs)

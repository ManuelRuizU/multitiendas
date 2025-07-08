# usuarios/views.py
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator # Necesario para clases
from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import PerfilVendedor, Cliente, Direccion
# Importa tus serializadores
from .serializers import UserSerializer, UserRegisterSerializer, PerfilVendedorSerializer, ClienteSerializer, DireccionSerializer
# Importaciones para tokens
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
# Importación necesaria para ValidationError desde rest_framework
from rest_framework.serializers import ValidationError as SerializerValidationError 
from django.db import IntegrityError # Necesaria para manejar posibles errores de unicidad

# --- VISTA PARA REGISTRO DE USUARIOS (SIN CAMBIOS SIGNIFICATIVOS) ---
@method_decorator(csrf_exempt, name='dispatch') # <-- Añade esta línea
class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]
    
        

    def create(self, request, *args, **kwargs):
        print("--- Iniciando método create en RegisterUserView ---")
        print(f"Request method: {request.method}")
        print(f"Request data: {request.data}")
        print(f"Request user authenticated: {request.user.is_authenticated}") # Debería ser False
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({"username": user.username, "email": user.email, "id": user.id},
                        status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save()

# --- UserViewSet (SIN CAMBIOS) ---
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser] 


# --- PerfilVendedorViewSet (AJUSTADO PARA ASIGNACIÓN AUTOMÁTICA) ---
class PerfilVendedorViewSet(viewsets.ModelViewSet):
    queryset = PerfilVendedor.objects.all()
    serializer_class = PerfilVendedorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Permite a usuarios staff/admins ver todos los perfiles, 
        pero los usuarios normales solo pueden ver su propio perfil.
        """
        # Tu lógica original es buena aquí. Si un usuario es staff, ve todo.
        if self.request.user.is_authenticated and self.request.user.is_staff: 
            return PerfilVendedor.objects.all()
        # Si no es staff o es el propio usuario, filtra por su perfil.
        return PerfilVendedor.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Asigna automáticamente el usuario autenticado al PerfilVendedor.
        Previene la creación de múltiples perfiles para el mismo usuario.
        """
        if PerfilVendedor.objects.filter(user=self.request.user).exists():
            raise SerializerValidationError({"detail": "Ya existe un perfil de vendedor para este usuario."})
        # Si no existe, guarda el PerfilVendedor y lo vincula al usuario autenticado.
        serializer.save(user=self.request.user)

    # Nota: Tu `my_profile` `@action` puede ser útil para un endpoint específico como `/perfilvendedor/mi-perfil/`
    # Aquí un ejemplo simple de cómo lo integrarías si aún no lo has hecho en tus urls.py
    # from rest_framework.decorators import action # Asegúrate de importar action
    # @action(detail=False, methods=['get', 'post'], url_path='mi-perfil')
    # def my_profile(self, request):
    #     if request.method == 'GET':
    #         try:
    #             perfil = self.get_queryset().get() # Asegura que solo obtenga SU perfil
    #             serializer = self.get_serializer(perfil)
    #             return Response(serializer.data)
    #         except PerfilVendedor.DoesNotExist:
    #             return Response({"detail": "No se ha encontrado un perfil de vendedor para este usuario."}, status=status.HTTP_404_NOT_FOUND)
    #     elif request.method == 'POST':
    #         serializer = self.get_serializer(data=request.data)
    #         serializer.is_valid(raise_exception=True)
    #         self.perform_create(serializer) # Llama a perform_create para asignar el user
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)


# --- ClienteViewSet (MAYORES CAMBIOS PARA INVITADOS Y REGISTRADOS) ---
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    
    def get_permissions(self):
        """
        Define permisos:
        - POST (crear): Cualquiera puede crear un Cliente (registrado o invitado).
        - GET/PUT/PATCH/DELETE: Solo usuarios autenticados pueden ver/editar SUS propios perfiles.
        """
        if self.action == 'create': # Permite a no autenticados POSTear para crear clientes invitados
            return [permissions.AllowAny()] 
        return [permissions.IsAuthenticated()] # Restringe otros métodos a autenticados

    def get_queryset(self):
        """
        Un usuario autenticado solo puede ver y modificar su propio perfil de Cliente.
        Los usuarios no autenticados (invitados) no pueden listar perfiles.
        """
        if self.request.user.is_authenticated:
            # Si el usuario es staff, puede ver todos los clientes.
            if self.request.user.is_staff:
                return Cliente.objects.all()
            # Si no es staff, solo puede ver su propio perfil.
            return Cliente.objects.filter(user=self.request.user)
        # Si el usuario no está autenticado, no se le permite ver ningún perfil de Cliente listado.
        return Cliente.objects.none()

    def perform_create(self, serializer):
        """
        Lógica para crear un Cliente: asigna al usuario autenticado si existe, 
        de lo contrario crea un cliente invitado.
        """
        if self.request.user.is_authenticated:
            # Caso 1: Usuario autenticado quiere crear/vincular su perfil de cliente
            if Cliente.objects.filter(user=self.request.user).exists():
                raise SerializerValidationError({"detail": "Ya existe un perfil de cliente para este usuario."})
            
            # Guarda el cliente vinculándolo al usuario autenticado.
            serializer.save(user=self.request.user)
        else:
            # Caso 2: Cliente invitado (no autenticado)
            # El serializador ya validó que tenga email y nombre_completo.
            # No es necesario pasar 'user=None' explícitamente ya que el campo es `null=True, blank=True`
            # en el modelo y el serializer lo manejará si no se le pasa un 'user' o 'user_id'.
            try:
                # Opcional: Para evitar duplicados de clientes invitados por email (si lo deseas)
                # Esto es una decisión de diseño: puedes querer crear un nuevo Cliente para cada pedido
                # de invitado, o intentar reusar un Cliente invitado existente si el email coincide.
                # Aquí, por simplicidad y flexibilidad, permitimos la creación si no hay un user_id.
                # Si quieres reusar, la lógica sería más compleja, buscando por email y actualizando.
                
                serializer.save() # Guarda el cliente invitado
            except IntegrityError: # En caso de que Django lance un error de unicidad (ej. si luego decides hacer email único para invitados)
                raise SerializerValidationError({"detail": "Error al crear cliente invitado. El email podría estar duplicado o ya registrado."})

    # Acción personalizada para que un usuario autenticado pueda acceder a "su" perfil de cliente
    # La acción ya existía en tu código, solo la formalizamos con @action
    from rest_framework.decorators import action # Asegúrate de importar action si no lo está
    @action(detail=False, methods=['get'], url_path='mi-perfil')
    def my_profile(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "Para acceder a tu perfil, debes iniciar sesión."}, status=status.HTTP_403_FORBIDDEN)
        try:
            # get_queryset ya filtra por el usuario actual
            cliente = self.get_queryset().get() 
            serializer = self.get_serializer(cliente)
            return Response(serializer.data)
        except Cliente.DoesNotExist:
            return Response({"detail": "No se ha encontrado un perfil de cliente para este usuario."}, status=status.HTTP_404_NOT_FOUND)


# --- DireccionViewSet (AJUSTADO PARA CLIENTES INVITADOS Y REGISTRADOS) ---
class DireccionViewSet(viewsets.ModelViewSet):
    queryset = Direccion.objects.all()
    serializer_class = DireccionSerializer
    # Permite solo a usuarios autenticados gestionar direcciones.
    # Un cliente invitado no tiene un "perfil" persistente para asociar direcciones a largo plazo,
    # aunque se podrían crear direcciones temporales vinculadas al Cliente invitado en un flujo de checkout.
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Asegura que un usuario solo pueda ver/editar las direcciones asociadas a SU perfil de Cliente.
        """
        # Si el usuario es staff, puede ver todas las direcciones.
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return Direccion.objects.all()
        
        # Para usuarios normales, filtra por su perfil de cliente.
        try:
            # Recupera el perfil de cliente del usuario autenticado.
            cliente = Cliente.objects.get(user=self.request.user)
            return self.queryset.filter(cliente=cliente)
        except Cliente.DoesNotExist:
            # Si el usuario no tiene perfil de cliente, no hay direcciones que mostrar.
            # Puedes retornar un queryset vacío para evitar errores 404,
            # o levantar una SerializerValidationError si consideras que es un error de negocio.
            return Direccion.objects.none() 

    def perform_create(self, serializer):
        """
        Al crear una dirección, automáticamente la asigna al perfil de Cliente
        del usuario autenticado.
        """
        try:
            # Obtiene el perfil de cliente del usuario autenticado.
            cliente = Cliente.objects.get(user=self.request.user)
        except Cliente.DoesNotExist:
            raise SerializerValidationError({"detail": "Para crear una dirección, debes tener un perfil de cliente asociado a tu cuenta."})
        
        # Guarda la dirección, vinculándola al objeto Cliente del usuario actual.
        serializer.save(cliente=cliente)

# --- CustomAuthToken (SIN CAMBIOS) ---
class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'username': user.username
        })
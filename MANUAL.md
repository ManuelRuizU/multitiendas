
Manual de Creación de Proyecto Django REST API: Desde Cero hasta el Primer Usuario

Este manual detalla los pasos esenciales para configurar un proyecto Django con Django REST Framework, estructurar las aplicaciones, definir APIs y realizar la primera interacción para crear un usuario.

1. Preparación del Entorno de Desarrollo

    Instalar Python: Descarga e instala la última versión estable de Python desde python.org.

    Verificar Pip: pip (el gestor de paquetes de Python) se instala automáticamente con Python. Verifica su instalación:
    Bash

pip --version

Crear Entorno Virtual: Los entornos virtuales aíslan las dependencias de tu proyecto.

    Navega a la carpeta donde quieres guardar tu proyecto:
    Bash

cd C:\Users\dell

Crea el entorno virtual (ej. env):
Bash

python -m venv env

Activa el entorno virtual:
Bash

        .\env\Scripts\activate

        Verás (env) al inicio de tu prompt, indicando que está activo.

2. Configuración Inicial del Proyecto Django

    Instalar Django y Django REST Framework (DRF):
    Bash

pip install django djangorestframework

Crear el Proyecto Django:

    Navega a la carpeta raíz donde quieres crear el proyecto (por ejemplo, mi_plataforma_multitienda):
    Bash

    django-admin startproject core_multitienda .

    (El . crea el proyecto en el directorio actual).

Configurar settings.py (dentro de core_multitienda/settings.py):

    Añade rest_framework a INSTALLED_APPS:
    Python

INSTALLED_APPS = [
    # ... otras apps ...
    'rest_framework',
    # Tus apps personalizadas irán aquí
]

Añade la configuración básica de DRF (opcional pero recomendado):
Python

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ]
}

Configura la base de datos (por defecto SQLite es suficiente para desarrollo):
Python

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

Ejecutar Migraciones Iniciales:
Bash

python manage.py migrate

Crear Superusuario (Administrador):
Bash

    python manage.py createsuperuser

    (Sigue las instrucciones para nombre de usuario, email y contraseña).

3. Estructura de Aplicaciones y Modelos (models.py)

    Crear Aplicaciones (Apps): Para organizar tu proyecto, crea aplicaciones separadas para cada dominio lógico (ej. usuarios, tiendas, productos, pedidos, plataforma).
    Bash

python manage.py startapp usuarios
python manage.py startapp tiendas
python manage.py startapp productos
python manage.py startapp pedidos
python manage.py startapp plataforma

Registrar Apps en settings.py: Añade tus nuevas apps a INSTALLED_APPS en core_multitienda/settings.py:
Python

INSTALLED_APPS = [
    # ...
    'rest_framework',
    'usuarios',
    'tiendas',
    'productos',
    'pedidos',
    'plataforma',
]

Definir Modelos en models.py de cada App:

    En cada mi_app/models.py, define tus clases de modelo (django.db.models.Model).

    Ejemplo para usuarios/models.py:
    Python

    # usuarios/models.py
    from django.db import models
    from django.contrib.auth.models import User

    class PerfilVendedor(models.Model):
        user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_vendedor')
        telefono = models.CharField(max_length=20, blank=True, null=True)
        rut = models.CharField(max_length=12, unique=True, blank=True, null=True)
        razon_social = models.CharField(max_length=100, blank=True, null=True)
        giro = models.CharField(max_length=100, blank=True, null=True)
        direccion_fiscal = models.CharField(max_length=255, blank=True, null=True)
        fecha_registro = models.DateTimeField(auto_now_add=True)
        is_complete = models.BooleanField(default=False)

        def __str__(self):
            return f"Vendedor: {self.user.username}"

    class Cliente(models.Model):
        user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cliente')
        telefono = models.CharField(max_length=20, blank=True, null=True)

        def __str__(self):
            return f"Cliente: {self.user.username}"

    class Direccion(models.Model):
        cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='direcciones')
        etiqueta = models.CharField(max_length=50) # Ej: Casa, Trabajo
        direccion = models.CharField(max_length=255)
        latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
        longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
        validada = models.BooleanField(default=False) # Si la dirección ha sido geocodificada y validada

        def __str__(self):
            return f"{self.etiqueta}: {self.direccion}"

Crear y Aplicar Migraciones: Después de definir/modificar modelos en cada app, genera y aplica las migraciones:
Bash

    python manage.py makemigrations
    python manage.py migrate

4. Serializadores (serializers.py)

    Crear serializers.py en cada App: Crea un archivo serializers.py dentro de cada una de tus aplicaciones (usuarios/serializers.py, tiendas/serializers.py, etc.).

    Definir Serializadores (rest_framework.serializers.ModelSerializer): Un serializador convierte objetos de Django en JSON (y viceversa).

        Ejemplo para usuarios/serializers.py (Incluyendo registro):
        Python

        # usuarios/serializers.py
        from rest_framework import serializers
        from django.contrib.auth.models import User
        from .models import PerfilVendedor, Cliente, Direccion

        class UserRegisterSerializer(serializers.ModelSerializer):
            password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
            password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

            class Meta:
                model = User
                fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'password2']
                extra_kwargs = {'password': {'write_only': True}}

            def validate(self, data):
                if data['password'] != data['password2']:
                    raise serializers.ValidationError({"password": "Password fields didn't match."})
                return data

            def create(self, validated_data):
                validated_data.pop('password2')
                user = User.objects.create_user(**validated_data)
                return user

        # Serializador para lectura/actualización de usuarios (sin exponer contraseña)
        class UserSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = ['id', 'username', 'email', 'first_name', 'last_name']
                read_only_fields = ['username'] # No permite cambiar username vía API
                extra_kwargs = {'password': {'write_only': True, 'required': False}} # Permite actualizar contraseña

            def update(self, instance, validated_data):
                password = validated_data.pop('password', None)
                user = super().update(instance, validated_data)
                if password:
                    user.set_password(password)
                    user.save()
                return user

        class PerfilVendedorSerializer(serializers.ModelSerializer):
            user = UserSerializer(read_only=True)
            user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='user', write_only=True)
            class Meta:
                model = PerfilVendedor
                fields = ['id', 'user', 'user_id', 'telefono', 'rut', 'razon_social', 'giro', 'direccion_fiscal', 'fecha_registro', 'is_complete']
                read_only_fields = ['id', 'fecha_registro', 'is_complete']

        class ClienteSerializer(serializers.ModelSerializer):
            user = UserSerializer(read_only=True)
            user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='user', write_only=True)
            class Meta:
                model = Cliente
                fields = ['id', 'user', 'user_id', 'telefono']
                read_only_fields = ['id']

        class DireccionSerializer(serializers.ModelSerializer):
            cliente = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.all(), source='cliente', write_only=True)
            class Meta:
                model = Direccion
                fields = ['id', 'cliente', 'etiqueta', 'direccion', 'latitud', 'longitud', 'validada']
                read_only_fields = ['id']

5. Vistas (views.py)

    Crear views.py en cada App: Crea un archivo views.py dentro de cada una de tus aplicaciones (usuarios/views.py, tiendas/views.py, etc.).

    Definir Vistas (rest_framework.viewsets.ModelViewSet o generics.APIView): Las vistas manejan la lógica de negocio y la interacción con los serializadores y modelos.

        Ejemplo para usuarios/views.py (con registro y ViewSets):
        Python

        # usuarios/views.py
        from rest_framework import viewsets, generics, permissions, status
        from rest_framework.response import Response
        from django.contrib.auth.models import User
        from .models import PerfilVendedor, Cliente, Direccion
        from .serializers import UserSerializer, UserRegisterSerializer, PerfilVendedorSerializer, ClienteSerializer, DireccionSerializer

        # Vista para el registro de usuarios (solo POST)
        class RegisterUserView(generics.CreateAPIView):
            queryset = User.objects.all()
            serializer_class = UserRegisterSerializer
            permission_classes = [permissions.AllowAny] # Permite el registro público

            def create(self, request, *args, **kwargs):
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                user = self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response({"username": user.username, "email": user.email, "id": user.id},
                                status=status.HTTP_201_CREATED, headers=headers)

            def perform_create(self, serializer):
                return serializer.save()

        # ViewSet para User (solo lectura, generalmente para admins)
        class UserViewSet(viewsets.ReadOnlyModelViewSet):
            queryset = User.objects.all()
            serializer_class = UserSerializer
            permission_classes = [permissions.IsAdminUser]

        # Otros ViewSets para PerfilVendedor, Cliente, Direccion
        class PerfilVendedorViewSet(viewsets.ModelViewSet):
            queryset = PerfilVendedor.objects.all()
            serializer_class = PerfilVendedorSerializer
            permission_classes = [permissions.IsAuthenticated] # Ajusta según necesidad

        class ClienteViewSet(viewsets.ModelViewSet):
            queryset = Cliente.objects.all()
            serializer_class = ClienteSerializer
            permission_classes = [permissions.IsAuthenticated]

        class DireccionViewSet(viewsets.ModelViewSet):
            queryset = Direccion.objects.all()
            serializer_class = DireccionSerializer
            permission_classes = [permissions.IsAuthenticated]

6. Configuración de URLs (urls.py)

    Crear urls.py en cada App: Crea un archivo urls.py dentro de cada una de tus aplicaciones (usuarios/urls.py, tiendas/urls.py, etc.).

    Configurar URLs de la App: Usa DefaultRouter para los ModelViewSet y path() para las vistas genéricas.

        Ejemplo para usuarios/urls.py:
        Python

    # usuarios/urls.py
    from django.urls import path, include
    from rest_framework.routers import DefaultRouter
    from .views import UserViewSet, PerfilVendedorViewSet, ClienteViewSet, DireccionViewSet, RegisterUserView

    router = DefaultRouter()
    router.register(r'users', UserViewSet)
    router.register(r'perfiles-vendedor', PerfilVendedorViewSet)
    router.register(r'clientes', ClienteViewSet)
    router.register(r'direcciones', DireccionViewSet)

    urlpatterns = [
        path('', include(router.urls)),
        path('register/', RegisterUserView.as_view(), name='user-register'),
    ]

Incluir URLs de Apps en core_multitienda/urls.py (URLS del Proyecto):
Python

    # core_multitienda/urls.py
    from django.contrib import admin
    from django.urls import path, include

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('api/usuarios/', include('usuarios.urls')),
        path('api/tiendas/', include('tiendas.urls')),
        path('api/productos/', include('productos.urls')),
        path('api/pedidos/', include('pedidos.urls')),
        path('api/plataforma/', include('plataforma.urls')), # Si tienes una app 'plataforma'
        # Otras URLs de tu proyecto
    ]

7. Gestión de Versiones con Git y GitHub

    Inicializar Git en el Proyecto:

        Navega a la raíz de tu proyecto (mi_plataforma_multitienda).

        Inicializa Git: git init

    Crear Archivo .gitignore: En la raíz del proyecto, crea un archivo .gitignore y añade:

    # Byte-code files
    *.pyc
    __pycache__/

    # Django stuff:
    *.log
    *.pot
    *.mo
    *.sqlite3
    .env/
    env/
    venv/
    media/
    static_root/
    staticfiles/

    # For Django production settings (if you create one later)
    local_settings.py

    # IDEs
    .vscode/
    .idea/

    # Operating System files
    .DS_Store
    Thumbs.db

    Primer Commit:

        Añadir archivos: git add .

        Realizar commit: git commit -m "Initial project setup and basic API endpoints"

    Crear Repositorio en GitHub:

        Ve a github.com, inicia sesión, y crea un nuevo repositorio vacío (sin README, .gitignore o licencia inicial).

    Conectar y Subir a GitHub:

        Copia los comandos de GitHub para "push an existing repository" (serán algo como):
        Bash

git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
git branch -M main
git push -u origin main

Si tu rama local es master y GitHub es main y tienes conflictos de historial:
Bash

git pull origin main --allow-unrelated-histories # Puede abrir un editor de texto, guarda y cierra.
git push -u origin master:main # Sube tu master local a la main remota

Para commits posteriores:
Bash

        git add .
        git commit -m "Mensaje descriptivo de los cambios"
        git push

8. Puesta en Marcha y Pruebas Iniciales

    Iniciar Servidor de Desarrollo:
    Bash

python manage.py runserver

(El servidor se ejecuta en http://127.0.0.1:8000/)

Explorar la API en el Navegador:

    Abre http://127.0.0.1:8000/api/usuarios/ (y otras apps) para ver la raíz de tu API.

    Haz clic en los enlaces de cada endpoint (/users/, /perfiles-vendedor/, etc.). Espera ver un array vacío [] inicialmente.

Probar Creación de Usuario con Postman:

    Descarga e instala Postman (si no lo tienes) desde postman.com/downloads/.

    Asegúrate de usar el "Postman Desktop Agent" (lo verás en la esquina inferior derecha de Postman).

    Crea una nueva solicitud.

    Método: POST

    URL: http://127.0.0.1:8000/api/usuarios/register/

    Headers: Content-Type: application/json

    Body: Selecciona raw y luego JSON. Pega:
    JSON

{
    "username": "tu_nuevo_usuario",
    "email": "tu.email@ejemplo.com",
    "first_name": "TuNombre",
    "last_name": "TuApellido",
    "password": "UnaContraseñaFuerte123",
    "password2": "UnaContraseñaFuerte123"
}

Envía la solicitud.

Verifica la Respuesta: Deberías ver un estado 201 Created y el JSON con los detalles del usuario (id, username, email).

9. Interacción con APIs Autenticadas (Post-Registro/Login)

    9.1. Usando el Token de Autenticación:

        Explicar cómo el auth_token obtenido en el login se utiliza en futuras solicitudes a endpoints protegidos.

        Ejemplo de cómo añadir el header Authorization: Token TU_TOKEN en Postman.

    9.2. Creación de Perfiles de Cliente:

        Detallar el endpoint, método (POST), headers y el cuerpo JSON (user_id, telefono).

        Mencionar la importancia de obtener el id del usuario (ya sea del registro o consultándolo).

    9.3. Gestión de Direcciones de Cliente:

        Explicar el endpoint, método (POST), headers y el cuerpo JSON (cliente_id, etiqueta, direccion, etc.).

        Subrayar que se necesita el id del cliente previamente creado.

    9.4. Creación y Actualización de Perfiles de Vendedor:

        Similar a los clientes, detallar cómo crear y actualizar PerfilVendedor una vez que un User ha sido autenticado.

        Endpoint, método, headers y cuerpo JSON (user_id, rut, razon_social, giro, etc.).

10. Estructura de APIs para otras Aplicaciones

    10.1. API de Tiendas (tiendas app):

        Describir el TiendaModel (nombre, descripción, perfil_vendedor FK, etc.).

        Cómo crear TiendaSerializer y TiendaViewSet.

        Endpoints básicos (/api/tiendas/, /api/tiendas/{id}/).

        Consideraciones sobre permisos (solo vendedores pueden crear/editar sus tiendas).

    10.2. API de Productos (productos app):

        Descripción del ProductoModel (nombre, precio, tienda FK, stock, etc.).

        Cómo crear ProductoSerializer y ProductoViewSet.

        Endpoints (/api/productos/, /api/productos/{id}/).

        Permisos (cualquiera puede ver, solo el vendedor de la tienda puede editar/eliminar).

    10.3. API de Pedidos (pedidos app):

        Modelos de Pedido y ItemPedido.

        Serializadores y vistas (PedidoViewSet).

        Lógica de carrito de compras y proceso de pago (esto podría ser más complejo y quizás una sección futura).

        Permisos (clientes pueden crear sus pedidos, vendedores solo ver/actualizar sus pedidos).

    10.4. API de Configuración de Plataforma (plataforma_config app):

        Modelos para configuración global (ej., categorías, métodos de pago, etc.).

        Serializadores y vistas.

        Permisos (solo administradores).

11. Testing de APIs

    11.1. Pruebas Unitarias con pytest o unittest:

        Cómo escribir tests para serializadores, modelos y vistas.

    11.2. Pruebas de Integración con Postman:

        Recalcar la importancia de usar colecciones de Postman para organizar las solicitudes.

        Uso de variables de entorno en Postman para manejar tokens y IDs dinámicamente.

12. Despliegue (Básico)

    Consideraciones para producción (DEBUG=False, SECRET_KEY, ALLOWED_HOSTS, bases de datos, servir estáticos/medios). Esto podría ser una sección más avanzada, pero es bueno mencionarla.


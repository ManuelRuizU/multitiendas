# core_multitienda/settings.py
from pathlib import Path
from datetime import timedelta
import os
import environ
from google.oauth2 import service_account


# ------------------------------------------------------------------
# RUTAS BASE
# ------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# ------------------------------------------------------------------
# VARIABLES DE ENTORNO
# Lee el archivo .env en la raíz del proyecto.
# Ejemplo de .env:
#   SECRET_KEY=tu-clave-secreta
#   DEBUG=True
#   GOOGLE_MAPS_API_KEY=AIza...
#   GS_BUCKET_NAME=mi-bucket
#   GS_CREDENTIALS=/ruta/a/credentials.json
# ------------------------------------------------------------------
env = environ.Env(
    DEBUG=(bool, False),
    GOOGLE_ANALYTICS_ID=(str, ''),
)
environ.Env.read_env(env_file=os.path.join(BASE_DIR, '.env'))


# ------------------------------------------------------------------
# SEGURIDAD
# ------------------------------------------------------------------
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')

# IMPORTANTE: En producción, reemplaza con tu dominio real.
# Ej: ['mitienda.com', 'www.mitienda.com']
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'DESKTOP-228SR5A',
    'mi_tienda_de_prueba.127.0.0.1.xip.io',
    'mi_tienda_de_prueba.localhost.xip.io',
]

# Dominio principal de la plataforma para manejo de subdominios.
# IMPORTANTE: Cambia esto a tu dominio real en producción.
MAIN_DOMAIN = '127.0.0.1:8000'


# ------------------------------------------------------------------
# APLICACIONES INSTALADAS
# ------------------------------------------------------------------
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Terceros
    'storages',                               # Google Cloud Storage
    'rest_framework',                         # Django REST Framework
    'corsheaders',                            # CORS Headers
    'rest_framework_simplejwt',               # Simple JWT
    'rest_framework_simplejwt.token_blacklist', # Blacklist de tokens JWT

    # Apps del proyecto
    'usuarios',
    'tiendas',
    'productos',
    'pedidos',
    'carritos',
    'repartidores',
    'plataforma_config',
]


# ------------------------------------------------------------------
# MIDDLEWARE
# ------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',        # Debe ir antes de CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'tiendas.middleware.TiendaSubdominioMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ------------------------------------------------------------------
# CORS
# En desarrollo: permite todos los orígenes.
# En producción: define los orígenes permitidos explícitamente.
# ------------------------------------------------------------------
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = [
        # Agrega aquí los dominios permitidos en producción
        # 'https://tudominio.com',
        # 'https://www.tudominio.com',
    ]


# ------------------------------------------------------------------
# URLs Y WSGI
# ------------------------------------------------------------------
ROOT_URLCONF = 'core_multitienda.urls'
WSGI_APPLICATION = 'core_multitienda.wsgi.application'


# ------------------------------------------------------------------
# TEMPLATES
# ------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core_multitienda' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core_multitienda.context_processors.google_analytics',
            ],
        },
    },
]


# ------------------------------------------------------------------
# BASE DE DATOS
# SQLite para desarrollo. En producción migrar a PostgreSQL.
# ------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ------------------------------------------------------------------
# AUTENTICACIÓN
# ------------------------------------------------------------------
AUTH_USER_MODEL = 'usuarios.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ------------------------------------------------------------------
# INTERNACIONALIZACIÓN
# ------------------------------------------------------------------
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True


# ------------------------------------------------------------------
# ARCHIVOS ESTÁTICOS
# ------------------------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'


# ------------------------------------------------------------------
# ARCHIVOS DE MEDIA
# En desarrollo: se sirven localmente desde /mediafiles/.
# En producción: se sirven desde Google Cloud Storage.
# ------------------------------------------------------------------
if DEBUG:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'mediafiles'
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
else:
    # Google Cloud Storage — solo en producción
    GS_BUCKET_NAME = env('GS_BUCKET_NAME')
    GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
        env('GS_CREDENTIALS')  # Ruta al archivo JSON de credenciales
    )
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'


# ------------------------------------------------------------------
# DEFAULT PRIMARY KEY
# ------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ------------------------------------------------------------------
# DJANGO REST FRAMEWORK
# ------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
}


# ------------------------------------------------------------------
# SIMPLE JWT
# CORRECCIÓN: El nombre correcto es SIMPLE_JWT (no REST_FRAMEWORK_SIMPLEJWT).
# El nombre incorrecto causaba que toda esta configuración fuera ignorada.
# ------------------------------------------------------------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=20),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}


# ------------------------------------------------------------------
# VARIABLES DE ENTORNO PERSONALIZADAS
# ------------------------------------------------------------------
GOOGLE_MAPS_API_KEY = env('GOOGLE_MAPS_API_KEY')
GOOGLE_ANALYTICS_ID = env('GOOGLE_ANALYTICS_ID', default='')
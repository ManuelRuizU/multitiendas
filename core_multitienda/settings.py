# core_multitienda/settings.py

from pathlib import Path
from datetime import timedelta # ¡Necesario para configurar las duraciones de los tokens JWT!


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-e-)*76i6#rxx@1m&)!o2wkwjxla#m!ddu(#cbxt-2hbx72725x'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'DESKTOP-228SR5A'] # Tu nombre de host añadido


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Terceros (Django REST Framework, CORS Headers, y Simple JWT)
    'rest_framework',
    # 'rest_framework.authtoken', # Comentado/Eliminado ya que usaremos JWT con simple_jwt
    'corsheaders',
    'rest_framework_simplejwt', # ¡Asegúrate de que esta línea esté presente para JWT!
    # 'djoser', # Descomentar si decides usar Djoser para registro/auth más avanzado

    # Tus aplicaciones personalizadas
    'usuarios',
    'tiendas',
    'productos',
    'pedidos',
    'plataforma_config',
    'carritos', 
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', # Permite peticiones de diferentes orígenes
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware', # Comentado para APIs REST que usan tokens
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# Configuración de CORS Headers
CORS_ALLOW_ALL_ORIGINS = True # ¡¡¡ADVERTENCIA: CAMBIAR A FALSE EN PRODUCCIÓN Y USAR CORS_ALLOWED_ORIGINS!!!
                               # Para desarrollo, CORS_ALLOW_ALL_ORIGINS = True es útil, pero inseguro en producción.

# CORS_ALLOWED_ORIGINS = [ # Para producción, descomentar y listar tus frontends
#     "http://localhost:8000", 
#     "http://127.0.0.1:8000",
#     # "https://tudominiofrontend.com",
# ]

ROOT_URLCONF = 'core_multitienda.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core_multitienda.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es-cl'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Django REST Framework (DRF) Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication', # ¡Autenticación principal con JWT!
        'rest_framework.authentication.SessionAuthentication', # Útil para la interfaz browsable de DRF
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny', # Por defecto, cualquiera puede acceder; tus vistas pueden ser más restrictivas
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    )
}

# Simple JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=50),   # Token de acceso de corta duración
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),    # Token de refresco de larga duración
    'ROTATE_REFRESH_TOKENS': False,                 # No rotar tokens de refresco (para mayor simplicidad)
    'BLACKLIST_AFTER_ROTATION': False,              # No añadir a la blacklist después de rotar (si ROTATE_REFRESH_TOKENS es True)
    'UPDATE_LAST_LOGIN': False,                     # No actualizar last_login del usuario con cada token

    'ALGORITHM': 'HS256',                           # Algoritmo de firma del token
    'SIGNING_KEY': SECRET_KEY,                      # Clave de firma (usa tu SECRET_KEY de Django)
    'VERIFYING_KEY': None,                          # Para RSA/ECDSA, pero None para HS256
    'AUDIENCE': None,                               # Audiencia del token (opcional)
    'ISSUER': None,                                 # Emisor del token (opcional)
    'JWK_URL': None,                                # URL para JSON Web Key Set (para JWKS)
    'LEEWAY': 0,                                    # Margen de tiempo para expiración

    'AUTH_HEADER_TYPES': ('Bearer',),               # Tipo de encabezado de autorización (ej. "Bearer eyJ...")
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',       # Nombre del encabezado
    'USER_ID_FIELD': 'id',                          # Campo del modelo de usuario para el ID
    'USER_ID_CLAIM': 'user_id',                     # Nombre del claim en el token para el ID del usuario
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule', # Regla de autenticación

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',), # Clases de tokens
    'TOKEN_TYPE_CLAIM': 'token_type',               # Nombre del claim para el tipo de token
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser', # Clase de usuario para tokens

    'JTI_CLAIM': 'jti',                             # Nombre del claim para el ID único del token

    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=20),        # Duración de tokens deslizantes (si los usas)
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),   # Duración de refresco de tokens deslizantes
}
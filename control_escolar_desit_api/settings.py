import os
from dotenv import load_dotenv
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Mantén la clave secreta en variables de entorno en producción
SECRET_KEY = '-_&+lsebec(whhw!%n@ww&1j=4-^j_if9x8$q778+99oz&!ms2'

DEBUG = True  # en desarrollo

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "https://control-escolar-desit-api-luis-aziz.onrender.com"]
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',                 # necesarios para los filtros de DRF
    'rest_framework',
    'rest_framework.authtoken',       # conserva soporte de tokens de DRF
    'corsheaders',                    # librería CORS actualizada
    'control_escolar_desit_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',     # CORS debe ir antes de CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configuración de CORS: define orígenes permitidos y quita CORS_ORIGIN_ALLOW_ALL
CORS_ALLOWED_ORIGINS = [
    'http://localhost:4200',
    'https://app-movil-escolar-webapp-luis-aziz.onrender.com'
]

# También es muy recomendable agregar esto para evitar bloqueos de CSRF en producción:
CSRF_TRUSTED_ORIGINS = [
    'https://app-movil-escolar-webapp-luis-aziz.onrender.com'
]

CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'control_escolar_desit_api.urls'



import os

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

STATIC_URL = "/static/"
# STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
# TEMPLATES[0]["DIRS"] = [os.path.join(BASE_DIR, "templates")]
# STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'control_escolar_desit_api.wsgi.application'

DATABASES = {
    'default2': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'read_default_file': os.path.join(BASE_DIR, "my.cnf"),
            'charset': 'utf8mb4',
        }
    },
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv("DB_NAME"),
        'USER': os.getenv("DB_USERNAME"),
        'PASSWORD': os.getenv("DB_PASSWORD"),
        'HOST': os.getenv("DB_ADDR"),
        'PORT': os.getenv("DB_PORT"),
        'CONN_MAX_AGE': 600,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'

REST_FRAMEWORK = {
    'COERCE_DECIMAL_TO_STRING': False,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'control_escolar_desit_api.models.BearerTokenAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
}

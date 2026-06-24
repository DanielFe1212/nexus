"""
==============================================================================
ARCHIVO: settings.py
==============================================================================
Las variables sensibles (SECRET_KEY, credenciales de base de datos, DEBUG,
ALLOWED_HOSTS) se leen desde un archivo .env que NO se sube al repositorio.
Ver .env.example para la plantilla de configuración.
==============================================================================
"""

from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Cargar variables de entorno desde el archivo .env (en la raíz del proyecto)
load_dotenv(BASE_DIR / '.env')


# ── Utilidades para leer variables de entorno ─────────────────────────────
def env(clave, defecto=None):
    """Devuelve la variable de entorno o un valor por defecto."""
    return os.environ.get(clave, defecto)

def env_bool(clave, defecto=False):
    """Interpreta una variable de entorno como booleano."""
    valor = os.environ.get(clave)
    if valor is None:
        return defecto
    return valor.strip().lower() in ('1', 'true', 'yes', 'on', 'si', 'sí')

def env_list(clave, defecto=None):
    """Interpreta una variable separada por comas como lista."""
    valor = os.environ.get(clave)
    if not valor:
        return defecto or []
    return [item.strip() for item in valor.split(',') if item.strip()]


# ── Seguridad ─────────────────────────────────────────────────────────────
SECRET_KEY = env('SECRET_KEY', 'django-insecure-CAMBIAME-en-el-archivo-env')

DEBUG = env_bool('DEBUG', False)

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', ['127.0.0.1', 'localhost'])


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app',
    'rangefilter',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'app', 'templates')],
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

WSGI_APPLICATION = 'wsgi.application'


# ── Base de datos (SQL Server) ─────────────────────────────────────────────
# Todas las credenciales se leen del .env
DATABASES = {
    'default': {
        'ENGINE':   'mssql',
        'NAME':     env('DB_NAME', 'nexus_db'),
        'USER':     env('DB_USER', ''),
        'PASSWORD': env('DB_PASSWORD', ''),
        'HOST':     env('DB_HOST', 'localhost'),
        'PORT':     env('DB_PORT', ''),
        'OPTIONS': {
            'driver': env('DB_DRIVER', 'ODBC Driver 18 for SQL Server'),
            'extra_params': env('DB_EXTRA_PARAMS', 'TrustServerCertificate=yes;Encrypt=yes;'),
        },
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-co'
TIME_ZONE     = 'America/Bogota'
USE_I18N      = True
USE_TZ        = True

STATIC_URL       = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT      = os.path.join(BASE_DIR, 'staticfiles')

# ── Caché en memoria (LocMemCache) ────────────────────────────────────────
# Para escalar a Redis en producción, cambia el BACKEND a:
# 'django.core.cache.backends.redis.RedisCache' y agrega LOCATION
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'nexus-cache',
        'TIMEOUT': 300,  # 5 minutos — ajustable
    }
}

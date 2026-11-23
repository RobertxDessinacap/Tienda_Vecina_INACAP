"""
Django settings for Tienda Vecina.
Adhering to ISO/IEC 27001 Security Standard & Clean Architecture.
All sensitive configurations, database credentials and secrets are loaded strictly from .env.
"""

from pathlib import Path
import os
import sys
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

# Base Directory: root of backend
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env
ENV_FILE = BASE_DIR / '.env'
load_dotenv(dotenv_path=ENV_FILE)

# ==============================================================================
# ISO 27001 A.8.9: Secret & Configuration Management
# ==============================================================================
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError("[SECURITY ERROR - ISO 27001] SECRET_KEY must be defined in .env")

DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [host.strip() for host in os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',') if host.strip()]

# ==============================================================================
# Application Definition
# ==============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'corsheaders',

    # Local Domain Apps
    'apps.accounts',
    'apps.products',
    'apps.payments',
    'apps.security',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'apps.security.middleware.ISO27001SecurityHeadersMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.security.middleware.SecurityAuditLoggingMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ==============================================================================
# Database Configuration (PostgreSQL ORM via psycopg3 - Fail-Fast)
# ==============================================================================
_IS_TEST_RUN = 'test' in sys.argv
db_engine = os.getenv('DB_ENGINE', 'django.db.backends.postgresql')

if _IS_TEST_RUN and os.getenv('TEST_USE_SQLITE', 'False').lower() in ('true', '1'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
elif db_engine == 'django.db.backends.sqlite3':
    sqlite_name = os.getenv('DB_SQLITE_NAME', 'db.sqlite3')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / sqlite_name,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': db_engine,
            'NAME': os.getenv('DB_NAME', 'inacap_ecommerce'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
            'HOST': os.getenv('DB_HOST', '127.0.0.1'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'CONN_MAX_AGE': 60,
        }
    }

# ==============================================================================
# Password Validation (ISO 27001 A.8.5 - Secure Authentication)
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': int(os.getenv('PASSWORD_MIN_LENGTH', 8))},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom User Model for ISO 27001 Auth Segregation
AUTH_USER_MODEL = 'accounts.UserCredential'

# ==============================================================================
# Internationalization & Localization
# ==============================================================================
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# Django REST Framework Configuration
# ==============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.accounts.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.getenv('THROTTLE_ANON_RATE', '120/minute'),
        'user': os.getenv('THROTTLE_USER_RATE', '600/minute'),
        'login': os.getenv('THROTTLE_LOGIN_RATE', '5/minute'),
        'register': os.getenv('THROTTLE_REGISTER_RATE', '3/minute'),
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,
    'EXCEPTION_HANDLER': 'apps.security.audit.custom_exception_handler',
}

# ==============================================================================
# CORS Configuration (Restricted Origin Whitelist)
# ==============================================================================
cors_origins = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173')
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins.split(',') if origin.strip()]
CORS_ALLOW_CREDENTIALS = os.getenv('CORS_ALLOW_CREDENTIALS', 'True').lower() in ('true', '1')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

# ==============================================================================
# ISO 27001 Security Headers & Proxy Trust
# ==============================================================================
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
TRUST_X_FORWARDED_FOR = os.getenv('TRUST_X_FORWARDED_FOR', 'False').lower() in ('true', '1')
SECURE_BROWSER_XSS_FILTER = os.getenv('SECURE_BROWSER_XSS_FILTER', 'True').lower() in ('true', '1')
SECURE_CONTENT_TYPE_NOSNIFF = os.getenv('SECURE_CONTENT_TYPE_NOSNIFF', 'True').lower() in ('true', '1')
X_FRAME_OPTIONS = os.getenv('X_FRAME_OPTIONS', 'DENY')

# JWT Authentication Secrets (Segregated from SECRET_KEY in production)
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '').strip()
if not JWT_SECRET_KEY:
    if DEBUG or _IS_TEST_RUN:
        JWT_SECRET_KEY = f"{SECRET_KEY}-jwt-dev"
    else:
        raise ImproperlyConfigured('JWT_SECRET_KEY debe estar configurada de forma independiente en producción.')

if not DEBUG and not _IS_TEST_RUN:
    _insecure_jwt_keys = {
        'inacap-jwt-super-secret-iso27001-signature-key-2026',
        'jwt-super-secret-key-change-in-production-2026',
    }
    if (
        JWT_SECRET_KEY == SECRET_KEY
        or JWT_SECRET_KEY in _insecure_jwt_keys
        or JWT_SECRET_KEY.startswith('django-insecure-')
        or JWT_SECRET_KEY.upper().startswith('CHANGE_ME')
    ):
        raise ImproperlyConfigured(
            'JWT_SECRET_KEY no puede usar valores inseguros por defecto ni coincidir con SECRET_KEY en producción.'
        )

JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24))

# Media Files (Uploaded product images: 900x600, <=1MB)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Transbank Webpay Plus Integration (ISO 27001 Secure Payments)
TRANSBANK_COMMERCE_CODE = os.getenv('TRANSBANK_COMMERCE_CODE', '597055555532')
TRANSBANK_API_KEY = os.getenv('TRANSBANK_API_KEY', '579B532A7440BB061E185D8252273087')
TRANSBANK_ENVIRONMENT = os.getenv('TRANSBANK_ENVIRONMENT', 'TEST')


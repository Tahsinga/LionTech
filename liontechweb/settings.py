
"""
Django settings for liontechweb project.

This file has been cleaned to remove duplicate imports and duplicate sections.
It preserves the original settings and provides a clear static/media configuration.
"""

import os
import sys
from pathlib import Path

# Load local environment variables from a .env file (optional, ignored by git)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # python-dotenv is optional in production; ignore if not installed
    pass

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('1', 'true', 'yes')
# In production require SECRET_KEY to be set. For local dev allow a fallback.
if DEBUG:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-av6tyl$acs--twu1=9zw@^+731wgnk8i_nygan((umxd!)a-hk')
else:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError('Missing SECRET_KEY environment variable')
# Normalize ALLOWED_HOSTS into a list (comma separated in env)
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'website',
    'channels',
    'rest_framework',
    'corsheaders',
]

MIDDLEWARE = [
    'website.middleware.SqlitePragmaMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

ROOT_URLCONF = 'liontechweb.urls'
CORS_ALLOW_ALL_ORIGINS = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'liontechweb.wsgi.application'
ASGI_APPLICATION = 'liontechweb.asgi.application'

# Channels: prefer Redis in production (if REDIS_URL provided), otherwise use
# in-memory layer for local development.
REDIS_URL = os.environ.get('REDIS_URL') or os.environ.get('CHANNEL_REDIS_URL')
if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {'hosts': [REDIS_URL]},
        }
    }
else:
    CHANNEL_LAYERS = {'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {'timeout': 20},
    }
}

if os.environ.get('DATABASE_URL'):
    try:
        import dj_database_url

        DATABASES['default'] = dj_database_url.parse(os.environ.get('DATABASE_URL'))
    except Exception:
        pass

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

REST_FRAMEWORK = {'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination', 'PAGE_SIZE': 6}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static and media files
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'website', 'static')]
STATIC_ROOT = str(BASE_DIR / 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = str(BASE_DIR / 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Optional: use S3 for media if requested via environment variables.
# To enable in production set USE_S3=1 and provide the AWS credentials and bucket name.
USE_S3 = os.environ.get('USE_S3', '0').lower() in ('1', 'true', 'yes')
if USE_S3:
    try:
        # django-storages must be installed for S3 support. If it's not present,
        # we gracefully fall back to the local filesystem storage.
        from storages.backends.s3boto3 import S3Boto3Storage  # noqa: F401

        DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
        AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
        AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
        AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
        AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', None)
        AWS_QUERYSTRING_AUTH = False
    except Exception:
        USE_S3 = False



from backend.config.settings.base import *

DEBUG = False

# Ensure strict host matching
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Database: Production Postgres setup (Must load from env and use standard psycopg driver)
DATABASES = {
    'default': env.db('DATABASE_URL')
}
# Enable persistent DB connections
DATABASES['default']['CONN_MAX_AGE'] = 600

# Security Headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Cloud storage setups
if DEFAULT_FILE_STORAGE_PROVIDER == 's3':
    AWS_ACCESS_KEY_ID = env.str('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env.str('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env.str('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = env.str('AWS_S3_REGION_NAME', default='nyc3')
    AWS_S3_ENDPOINT_URL = env.str('AWS_S3_ENDPOINT_URL', default=f'https://{AWS_S3_REGION_NAME}.digitaloceanspaces.com')
    AWS_S3_CUSTOM_DOMAIN = env.str('AWS_S3_CUSTOM_DOMAIN', default=f'{AWS_STORAGE_BUCKET_NAME}.{AWS_S3_REGION_NAME}.digitaloceanspaces.com')
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
    }
elif DEFAULT_FILE_STORAGE_PROVIDER == 'gcs':
    GS_BUCKET_NAME = env.str('GS_BUCKET_NAME')
    GS_PROJECT_ID = env.str('GS_PROJECT_ID')
    GS_CREDENTIALS = env.str('GS_CREDENTIALS')  # JSON credentials string or path
    STORAGES = {
        "default": {"BACKEND": "storages.backends.gcloud.GoogleCloudStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }

# Structured Enterprise Production Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'backend.apps.core.logging.StructuredJSONFormatter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'eduorbit': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

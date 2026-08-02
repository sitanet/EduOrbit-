import os
from pathlib import Path
import environ

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Initialize environment variables
env = environ.Env()
backend_env_path = os.path.join(BASE_DIR, 'backend', '.env')
root_env_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(backend_env_path):
    environ.Env.read_env(backend_env_path)
elif os.path.exists(root_env_path):
    environ.Env.read_env(root_env_path)


SECRET_KEY = env.str('SECRET_KEY', default='django-insecure-default-secret-key-change-in-prod')

DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '.eduorbit.local'])

# Application definition
INSTALLED_APPS = [
    # ASGI Channels / Server Daphne should load before core admin/static files
    'daphne',
    
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party packages
    'rest_framework',
    'corsheaders',
    'channels',
    
    # Custom Application Core Modules
    'backend.apps.core',
    'backend.apps.identity',
    'backend.apps.tenants',
    'backend.apps.billing',
    'backend.apps.dashboard',
    'backend.apps.activity_log',
    'backend.apps.notifications',
    'backend.apps.storage',
    'backend.apps.configuration',
    'backend.apps.academic',
    'backend.apps.people',
    'backend.apps.admissions',
    'backend.apps.students',
    'backend.apps.timetable',
    'backend.apps.teachers',
    'backend.apps.attendance',
    'backend.apps.lms',
    'backend.apps.eae',
    'backend.apps.emrp',
    'backend.apps.efbm',
    'backend.apps.communication',
    'backend.apps.hr',
    'backend.apps.library',
    'backend.apps.transport',
    'backend.apps.hostel',
    'backend.apps.clinic',
    'backend.apps.inventory',
    'backend.apps.workflow',
    'backend.apps.facilities',
    'backend.apps.analytics',
    'backend.apps.portal',
    'backend.apps.administration',
    'backend.apps.ai',
    'backend.apps.integration',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Core Tenant Context Resolver Middleware
    'backend.apps.core.middleware.TenantMiddleware',
    'backend.apps.hr.middleware.HRContextMiddleware',
]

ROOT_URLCONF = 'backend.config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'backend', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # EduOrbit RBAC — injects sidebar_template, dashboard_role, etc.
                'backend.apps.dashboard.context_processors.permission_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.config.wsgi.application'
ASGI_APPLICATION = 'backend.config.asgi.application'

# Database Setup - Locked strictly to PostgreSQL engine
DATABASES = {
    'default': env.db('DATABASE_URL', default='postgres://postgres:admin@localhost:5432/eduorbit')
}

# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'backend', 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'identity.User'

# Django REST Framework config
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'backend.apps.core.api.StandardResponseRenderer',
    ),
    'DEFAULT_EXCEPTION_HANDLER': 'backend.apps.core.api.custom_exception_handler',
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
}

# Redis & Celery Config
REDIS_URL = env.str('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Celery Queues
from kombu import Queue
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_QUEUES = (
    Queue('default', routing_key='task.#'),
    Queue('email', routing_key='email.#'),
    Queue('notification', routing_key='notification.#'),
    Queue('report', routing_key='report.#'),
    Queue('analytics', routing_key='analytics.#'),
    Queue('ai', routing_key='ai.#'),
    Queue('embeddings', routing_key='embeddings.#'),
    Queue('documents', routing_key='documents.#'),
    Queue('media', routing_key='media.#'),
)

# Celery Beat Schedule
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'daily-backup': {
        'task': 'core.tasks.daily_backup',
        'schedule': crontab(hour=2, minute=0),
    },
    'cache-session-cleanup': {
        'task': 'core.tasks.cleanup_cache_sessions',
        'schedule': crontab(hour=3, minute=0),
    },
    'expired-tokens-cleanup': {
        'task': 'identity.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=3, minute=30),
    },
    'ai-embedding-jobs': {
        'task': 'ai.tasks.process_embeddings',
        'schedule': crontab(minute='*/15'),
    },
    'notification-retries': {
        'task': 'notifications.tasks.retry_failed_notifications',
        'schedule': crontab(minute='*/10'),
    },
    'invoice-payroll-reminders': {
        'task': 'billing.tasks.send_reminders',
        'schedule': crontab(hour=8, minute=0),
    },
    'attendance-summaries': {
        'task': 'attendance.tasks.generate_summaries',
        'schedule': crontab(hour=18, minute=0),
    },
    'analytics-snapshots': {
        'task': 'analytics.tasks.take_snapshots',
        'schedule': crontab(hour=23, minute=45),
    },
    'library-overdue-reminders': {
        'task': 'library.tasks.send_overdue_reminders',
        'schedule': crontab(hour=9, minute=0),
    },
}

# Channels / WebSockets layer
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'config': {
            "hosts": [REDIS_URL],
        },
    },
}

# Custom File Storage Provider configuration: 'local', 's3', or 'gcs'
DEFAULT_FILE_STORAGE_PROVIDER = env.str('DEFAULT_FILE_STORAGE_PROVIDER', default='local')

# Hostinger Email Provider Settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env.str('EMAIL_HOST', default='smtp.hostinger.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=465)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=True)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', default='noreply@eduorbit.com')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env.str('DEFAULT_FROM_EMAIL', default='EduOrbit ERP <noreply@eduorbit.com>')

# Termii SMS Provider Settings
TERMII_API_KEY = env.str('TERMII_API_KEY', default='test_termii_api_key_123')
TERMII_SENDER_ID = env.str('TERMII_SENDER_ID', default='EduOrbit')
TERMII_BASE_URL = env.str('TERMII_BASE_URL', default='https://api.ng.termii.com')

# Dojah KYC Identity Verification Provider Settings
DOJAH_API_KEY = env.str('DOJAH_API_KEY', default=None)
DOJAH_APP_ID = env.str('DOJAH_APP_ID', default=None)
DOJAH_BASE_URL = env.str('DOJAH_BASE_URL', default='https://api.dojah.io')


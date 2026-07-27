from backend.config.settings.base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Database Setup - Locked strictly to PostgreSQL engine
DATABASES = {
    'default': env.db('DATABASE_URL', default='postgres://postgres:admin@localhost:5432/eduorbit')
}

# Console logs and debug email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# In-memory channels layer for faster local execution without Redis if needed (fallback)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

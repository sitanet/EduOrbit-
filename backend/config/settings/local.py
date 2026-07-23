from backend.config.settings.base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Local SQLite override if postgres is not active in environment
DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3'))
}

# Console logs and debug email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# In-memory channels layer for faster local execution without Redis if needed (fallback)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

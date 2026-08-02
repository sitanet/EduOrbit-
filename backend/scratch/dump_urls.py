import os
import sys
# Make sure the parent of 'backend' directory (which is SMS) is in PYTHONPATH, or backend itself is treated correctly.
# Let's add the SMS folder to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__)) # SMS/backend/scratch
backend_dir = os.path.abspath(os.path.join(current_dir, '..')) # SMS/backend
sms_dir = os.path.abspath(os.path.join(backend_dir, '..')) # SMS

sys.path.insert(0, sms_dir)
sys.path.insert(0, backend_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings.local')

import django
django.setup()

from django.urls import get_resolver

def show_patterns(patterns, prefix=''):
    for pattern in patterns:
        if hasattr(pattern, 'url_patterns'):
            show_patterns(pattern.url_patterns, prefix + str(pattern.pattern))
        else:
            print(f"{prefix}{str(pattern.pattern)} [name={pattern.name}]")

resolver = get_resolver()
show_patterns(resolver.url_patterns)

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.config.settings.local'
import django; django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.get(username='hr.admin')
print('Groups:', list(u.groups.values_list('name', flat=True)))
print('is_staff:', u.is_staff)

# Simulate what the HR middleware does with no tenant
class FakeRequest:
    user = u
    tenant = None

req = FakeRequest()
from backend.apps.hr.middleware import HRContextMiddleware
HRContextMiddleware(lambda r: None)(req)
print('hr_role:', getattr(req, 'hr_role', 'NOT SET'))
